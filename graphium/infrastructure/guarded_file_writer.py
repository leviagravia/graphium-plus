"""POSIX/local-filesystem guarded physical writer for Graphium.

Safety model:
- immutable writer-grade target observation;
- same-directory exclusive staging;
- complete writes and stage fsync;
- metadata preservation for an existing target;
- late target/parent/stage revalidation;
- atomic replace for an observed existing target;
- race-safe rename-no-replace commit for an observed absent target, with link fallback;
- parent-directory fsync;
- truthful post-commit baseline/durability outcomes.

There is deliberately no direct/truncate fallback.
"""
from __future__ import annotations

import ctypes
import errno
import hashlib
import os
from pathlib import Path
import secrets
import stat
from typing import Callable

from graphium.domain.document_identity import (
    ContentFingerprint,
    DocumentFileState,
    FileObjectIdentity,
)
from graphium.domain.document_save import (
    GuardedWriteError,
    GuardedWriteResult,
    SaveDisposition,
    SaveTargetExpectation,
    SaveTargetObservation,
    SaveTargetSnapshot,
    StaleSaveTargetError,
    UnsafeSaveTargetError,
)
from graphium.infrastructure.document_loader import load_document, normalize_logical_path


DEFAULT_NEW_FILE_MODE = 0o644
_CHUNK_SIZE = 1024 * 1024
_RENAME_NOREPLACE = 1
_RENAME_NOREPLACE_UNSUPPORTED_ERRNOS = frozenset(
    {
        errno.ENOSYS,
        errno.EINVAL,
        errno.ENOTSUP,
        getattr(errno, "EOPNOTSUPP", errno.ENOTSUP),
    }
)


def _load_renameat2() -> object | None:
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = libc.renameat2
    except (OSError, AttributeError):
        return None
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    return renameat2


_RENAMEAT2 = _load_renameat2()


def _rename_noreplace_at(
    source_directory_fd: int,
    source_name: str,
    target_directory_fd: int,
    target_name: str,
) -> None:
    renameat2 = _RENAMEAT2
    if renameat2 is None:
        raise OSError(errno.ENOSYS, os.strerror(errno.ENOSYS))
    result = renameat2(
        source_directory_fd,
        os.fsencode(source_name),
        target_directory_fd,
        os.fsencode(target_name),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        error_number = ctypes.get_errno() or errno.EIO
        raise OSError(error_number, os.strerror(error_number), target_name)


def _object_id(st: os.stat_result) -> FileObjectIdentity:
    return FileObjectIdentity(int(st.st_dev), int(st.st_ino))


def _stat_value(st: os.stat_result, name: str, default: int = 0) -> int:
    return int(getattr(st, name, default))


def _read_xattrs(path: str) -> tuple[tuple[str, bytes], ...]:
    if not all(hasattr(os, name) for name in ("listxattr", "getxattr")):
        return ()
    try:
        names = os.listxattr(path, follow_symlinks=True)
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)):
            return ()
        raise UnsafeSaveTargetError(f"cannot inspect target extended attributes: {exc}") from exc
    values: list[tuple[str, bytes]] = []
    for name in sorted(names):
        try:
            values.append((name, os.getxattr(path, name, follow_symlinks=True)))
        except OSError as exc:
            raise UnsafeSaveTargetError(
                f"cannot read target extended attribute {name!r}: {exc}"
            ) from exc
    return tuple(values)


def _hash_open_regular(path: str) -> tuple[SaveTargetSnapshot, str]:
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise UnsafeSaveTargetError(f"cannot open save target safely: {path}: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise UnsafeSaveTargetError("save target is not a regular local file")
        digest = hashlib.sha256()
        total = 0
        while True:
            block = os.read(fd, _CHUNK_SIZE)
            if not block:
                break
            total += len(block)
            digest.update(block)
        after = os.fstat(fd)
    finally:
        os.close(fd)

    signature_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        _stat_value(before, "st_ctime_ns"),
        before.st_mode,
        _stat_value(before, "st_uid"),
        _stat_value(before, "st_gid"),
        before.st_nlink,
    )
    signature_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        _stat_value(after, "st_ctime_ns"),
        after.st_mode,
        _stat_value(after, "st_uid"),
        _stat_value(after, "st_gid"),
        after.st_nlink,
    )
    if signature_before != signature_after or total != after.st_size:
        raise StaleSaveTargetError("save target changed while Graphium was observing it")
    if after.st_nlink != 1:
        raise UnsafeSaveTargetError(
            "Graphium safe save does not overwrite hardlinked targets; use Save As to a new file"
        )
    if (after.st_mode & 0o222) == 0:
        raise UnsafeSaveTargetError("save target is read-only")

    canonical = os.path.realpath(path)
    try:
        path_state = os.stat(path)
        canonical_state = os.stat(canonical)
    except OSError as exc:
        raise StaleSaveTargetError(f"save target disappeared during observation: {exc}") from exc
    if _object_id(path_state) != _object_id(after) or _object_id(canonical_state) != _object_id(after):
        raise StaleSaveTargetError("save target path changed during observation")

    snapshot = SaveTargetSnapshot(
        object_id=_object_id(after),
        size=int(after.st_size),
        mtime_ns=int(after.st_mtime_ns),
        ctime_ns=_stat_value(after, "st_ctime_ns"),
        mode=int(after.st_mode),
        uid=_stat_value(after, "st_uid"),
        gid=_stat_value(after, "st_gid"),
        nlink=int(after.st_nlink),
        content_fingerprint=ContentFingerprint("sha256", digest.hexdigest()),
        xattrs=_read_xattrs(canonical),
    )
    return snapshot, canonical


def _snapshot_matches_file_state(snapshot: SaveTargetSnapshot, state: DocumentFileState) -> bool:
    if snapshot.object_id != state.binding.object_id:
        return False
    if snapshot.size != state.disk.size or snapshot.mtime_ns != state.disk.mtime_ns:
        return False
    if snapshot.mode != state.disk.mode:
        return False
    for attr in ("ctime_ns", "uid", "gid", "nlink"):
        expected = getattr(state.disk, attr, None)
        if expected is not None and int(expected) != int(getattr(snapshot, attr)):
            return False
    return snapshot.content_fingerprint == state.content_fingerprint


def _parent_identity(path: str) -> FileObjectIdentity:
    st = os.stat(path)
    if not stat.S_ISDIR(st.st_mode):
        raise UnsafeSaveTargetError(f"save parent is not a directory: {path}")
    return _object_id(st)


class GuardedFileWriter:
    """The single Graphium physical writer authority."""

    __slots__ = ("new_file_mode", "_test_hook")

    def __init__(
        self,
        *,
        new_file_mode: int = DEFAULT_NEW_FILE_MODE,
        test_hook: Callable[[str, dict[str, object]], None] | None = None,
    ) -> None:
        mode = int(new_file_mode)
        if mode < 0 or mode > 0o7777:
            raise ValueError("new_file_mode must be a POSIX permission mode")
        self.new_file_mode = mode
        self._test_hook = test_hook

    def _hook(self, phase: str, **context: object) -> None:
        if self._test_hook is not None:
            self._test_hook(phase, context)

    def observe_target(
        self,
        path: str,
        *,
        expected_file_state: DocumentFileState | None = None,
    ) -> SaveTargetObservation:
        """Observe a Save/Save-As target without mutating it.

        For ordinary Save, pass the accepted file state; any mismatch fails closed.
        For Save As, omit it.  If the target exists, caller-side GTK confirmation remains a
        separate renderability responsibility; this token records only transactional evidence.
        """
        logical = normalize_logical_path(path)
        logical_parent = os.path.dirname(logical) or os.curdir
        if not os.path.isdir(logical_parent):
            raise UnsafeSaveTargetError(f"save parent does not exist: {logical_parent}")
        physical_parent = os.path.realpath(logical_parent)
        parent_id = _parent_identity(physical_parent)

        if not os.path.lexists(logical):
            if expected_file_state is not None:
                raise StaleSaveTargetError("the active document target no longer exists")
            physical = os.path.join(physical_parent, os.path.basename(logical))
            observation = SaveTargetObservation(
                expectation=SaveTargetExpectation.EXPECTED_ABSENT,
                logical_target_path=logical,
                logical_parent_path=logical_parent,
                physical_target_path=physical,
                physical_parent_path=physical_parent,
                parent_object_id=parent_id,
                logical_parent_object_id=_parent_identity(logical_parent),
                logical_target_is_symlink=False,
                existing=None,
            )
            self._hook("after_observation", observation=observation)
            return observation

        if os.path.islink(logical) and not os.path.exists(logical):
            raise UnsafeSaveTargetError("Graphium does not Save As through a dangling symlink")

        logical_is_symlink = os.path.islink(logical)
        physical = os.path.realpath(logical)
        snapshot, canonical = _hash_open_regular(physical)
        if canonical != physical:
            physical = canonical
        try:
            logical_state = os.stat(logical)
        except OSError as exc:
            raise StaleSaveTargetError(f"save target changed during observation: {exc}") from exc
        if _object_id(logical_state) != snapshot.object_id:
            raise StaleSaveTargetError("logical save path no longer names the observed target")

        if expected_file_state is not None:
            expected_logical = normalize_logical_path(expected_file_state.binding.logical_path)
            expected_canonical = expected_file_state.binding.canonical_path
            if logical != expected_logical:
                raise StaleSaveTargetError("ordinary Save target differs from active document binding")
            if expected_canonical is not None and os.path.realpath(expected_canonical) != physical:
                raise StaleSaveTargetError("active document canonical target changed")
            if not _snapshot_matches_file_state(snapshot, expected_file_state):
                raise StaleSaveTargetError("file changed on disk since Graphium accepted it")

        physical_parent = os.path.dirname(physical) or os.curdir
        observation = SaveTargetObservation(
            expectation=SaveTargetExpectation.EXPECTED_EXISTING,
            logical_target_path=logical,
            logical_parent_path=logical_parent,
            physical_target_path=physical,
            physical_parent_path=physical_parent,
            parent_object_id=_parent_identity(physical_parent),
            logical_parent_object_id=_parent_identity(logical_parent),
            logical_target_is_symlink=logical_is_symlink,
            existing=snapshot,
        )
        self._hook("after_observation", observation=observation)
        return observation

    @staticmethod
    def _verify_parent(observation: SaveTargetObservation, directory_fd: int) -> None:
        if _object_id(os.fstat(directory_fd)) != observation.parent_object_id:
            raise StaleSaveTargetError("physical save parent directory changed")
        try:
            logical_parent_state = os.stat(observation.logical_parent_path)
        except OSError as exc:
            raise StaleSaveTargetError("logical save parent disappeared") from exc
        if _object_id(logical_parent_state) != observation.logical_parent_object_id:
            raise StaleSaveTargetError("logical save parent was replaced or retargeted")

    @staticmethod
    def _late_revalidate(observation: SaveTargetObservation) -> None:
        if observation.expectation is SaveTargetExpectation.EXPECTED_ABSENT:
            if os.path.lexists(observation.logical_target_path) or os.path.lexists(
                observation.physical_target_path
            ):
                raise StaleSaveTargetError("Save As target appeared before commit")
            if os.path.realpath(observation.logical_parent_path) != observation.physical_parent_path:
                raise StaleSaveTargetError("Save As parent path changed before commit")
            return

        assert observation.existing is not None
        if not os.path.lexists(observation.logical_target_path):
            raise StaleSaveTargetError("save target disappeared before commit")
        if observation.logical_target_is_symlink:
            if not os.path.islink(observation.logical_target_path):
                raise StaleSaveTargetError("logical save symlink was replaced")
            if os.path.realpath(observation.logical_target_path) != observation.physical_target_path:
                raise StaleSaveTargetError("logical save symlink was retargeted")
        else:
            if os.path.realpath(observation.logical_target_path) != observation.physical_target_path:
                raise StaleSaveTargetError("logical save path was replaced")
        fresh, canonical = _hash_open_regular(observation.physical_target_path)
        if canonical != observation.physical_target_path or fresh != observation.existing:
            raise StaleSaveTargetError("save target changed before namespace commit")

    @staticmethod
    def _apply_existing_metadata(stage_fd: int, observation: SaveTargetObservation) -> None:
        assert observation.existing is not None
        snap = observation.existing
        current = os.fstat(stage_fd)
        if hasattr(os, "fchown") and (
            _stat_value(current, "st_uid") != snap.uid or _stat_value(current, "st_gid") != snap.gid
        ):
            try:
                os.fchown(stage_fd, snap.uid, snap.gid)
            except OSError as exc:
                raise UnsafeSaveTargetError(
                    "Graphium cannot preserve target owner/group safely; use Save As"
                ) from exc
        try:
            os.fchmod(stage_fd, stat.S_IMODE(snap.mode))
        except OSError as exc:
            raise UnsafeSaveTargetError("Graphium cannot preserve target permissions") from exc

    @staticmethod
    def _apply_xattrs(stage_path: str, observation: SaveTargetObservation) -> None:
        if observation.existing is None or not observation.existing.xattrs:
            return
        if not hasattr(os, "setxattr"):
            raise UnsafeSaveTargetError(
                "Graphium cannot preserve existing extended attributes on this platform"
            )
        for name, value in observation.existing.xattrs:
            try:
                os.setxattr(stage_path, name, value, follow_symlinks=False)
            except OSError as exc:
                raise UnsafeSaveTargetError(
                    f"Graphium cannot preserve extended attribute {name!r}"
                ) from exc

    @staticmethod
    def _write_all(fd: int, data: bytes) -> None:
        view = memoryview(data)
        offset = 0
        while offset < len(view):
            written = os.write(fd, view[offset:])
            if written <= 0:
                raise GuardedWriteError("short/zero stage write")
            offset += written

    def commit(self, observation: SaveTargetObservation, data: bytes) -> GuardedWriteResult:
        if not isinstance(observation, SaveTargetObservation):
            raise TypeError("observation must be SaveTargetObservation")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("data must be bytes-like")
        payload = bytes(data)
        digest = ContentFingerprint("sha256", hashlib.sha256(payload).hexdigest())

        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            directory_fd = os.open(observation.physical_parent_path, flags)
        except OSError as exc:
            raise GuardedWriteError(f"cannot open target directory safely: {exc}") from exc
        stage_name = f".graphium-save-{os.getpid()}-{secrets.token_hex(16)}.tmp"
        stage_path = os.path.join(observation.physical_parent_path, stage_name)
        target_name = os.path.basename(observation.physical_target_path)
        stage_fd: int | None = None
        committed = False
        warnings: list[str] = []
        try:
            self._verify_parent(observation, directory_fd)
            stage_flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                stage_fd = os.open(stage_name, stage_flags, 0o600, dir_fd=directory_fd)
            except OSError as exc:
                raise GuardedWriteError(f"cannot create safe sibling stage: {exc}") from exc
            stage_identity = _object_id(os.fstat(stage_fd))
            try:
                self._write_all(stage_fd, payload)
                self._hook(
                    "after_stage_write",
                    observation=observation,
                    stage_path=stage_path,
                    stage_fd=stage_fd,
                )
                if observation.existing is not None:
                    self._apply_existing_metadata(stage_fd, observation)
                else:
                    os.fchmod(stage_fd, self.new_file_mode)
                self._apply_xattrs(stage_path, observation)
                os.fsync(stage_fd)
                self._hook(
                    "after_stage_fsync",
                    observation=observation,
                    stage_path=stage_path,
                    stage_fd=stage_fd,
                )
            except (GuardedWriteError, UnsafeSaveTargetError):
                raise
            except OSError as exc:
                raise GuardedWriteError(f"stage write/sync failed: {exc}") from exc

            # The staged pathname itself is attacker-visible in a writable directory.
            try:
                named_stage = os.stat(stage_name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                raise StaleSaveTargetError("staged file pathname disappeared before commit") from exc
            if not stat.S_ISREG(named_stage.st_mode) or _object_id(named_stage) != stage_identity:
                raise StaleSaveTargetError("staged file pathname was substituted before commit")

            self._hook(
                "before_late_revalidation",
                observation=observation,
                stage_path=stage_path,
                stage_fd=stage_fd,
            )
            self._verify_parent(observation, directory_fd)
            self._late_revalidate(observation)

            self._hook(
                "before_namespace_commit",
                observation=observation,
                stage_path=stage_path,
                stage_fd=stage_fd,
            )
            if observation.expectation is SaveTargetExpectation.EXPECTED_EXISTING:
                try:
                    os.replace(
                        stage_name,
                        target_name,
                        src_dir_fd=directory_fd,
                        dst_dir_fd=directory_fd,
                    )
                except OSError as exc:
                    raise GuardedWriteError(f"namespace commit failed: {exc}") from exc
                committed = True
            else:
                try:
                    _rename_noreplace_at(
                        directory_fd,
                        stage_name,
                        directory_fd,
                        target_name,
                    )
                except OSError as exc:
                    if exc.errno == errno.EEXIST:
                        raise StaleSaveTargetError(
                            "Save As target appeared at commit time"
                        ) from exc
                    if exc.errno not in _RENAME_NOREPLACE_UNSUPPORTED_ERRNOS:
                        raise GuardedWriteError(f"namespace commit failed: {exc}") from exc
                    try:
                        os.link(
                            stage_name,
                            target_name,
                            src_dir_fd=directory_fd,
                            dst_dir_fd=directory_fd,
                            follow_symlinks=False,
                        )
                    except FileExistsError as link_exc:
                        raise StaleSaveTargetError(
                            "Save As target appeared at commit time"
                        ) from link_exc
                    except OSError as link_exc:
                        raise GuardedWriteError(
                            f"namespace commit fallback failed: {link_exc}"
                        ) from link_exc
                    committed = True
                    try:
                        os.unlink(stage_name, dir_fd=directory_fd)
                    except FileNotFoundError:
                        pass
                    except OSError as unlink_exc:
                        warnings.append(
                            "post-commit stage cleanup failed after link fallback: "
                            f"{unlink_exc}"
                        )
                else:
                    committed = True

            try:
                self._hook(
                    "after_namespace_commit",
                    observation=observation,
                    stage_path=stage_path,
                    stage_fd=stage_fd,
                )
            except Exception as exc:
                warnings.append(f"post-commit hook reported uncertainty: {exc}")

            try:
                os.fsync(directory_fd)
            except OSError as exc:
                warnings.append(f"parent-directory durability sync failed after commit: {exc}")

            file_state: DocumentFileState | None = None
            try:
                self._hook("before_postcommit_load", observation=observation)
                loaded = load_document(observation.logical_target_path)
                if loaded.file_state.content_fingerprint != digest:
                    warnings.append(
                        "target bytes changed after Graphium committed; no fresh baseline was accepted"
                    )
                else:
                    file_state = loaded.file_state
            except Exception as exc:  # post-commit: never turn into a retry-shaped failure
                warnings.append(f"fresh post-save baseline unavailable after commit: {exc}")

            if file_state is None:
                disposition = SaveDisposition.COMMITTED_BASELINE_UNAVAILABLE
            elif any("durability sync failed" in warning for warning in warnings):
                disposition = SaveDisposition.COMMITTED_DURABILITY_UNCERTAIN
            else:
                disposition = SaveDisposition.COMMITTED_CONFIRMED
            return GuardedWriteResult(
                disposition=disposition,
                logical_target_path=observation.logical_target_path,
                committed_fingerprint=digest,
                file_state=file_state,
                warnings=tuple(warnings),
            )
        finally:
            if stage_fd is not None:
                try:
                    os.close(stage_fd)
                except OSError:
                    pass
            if not committed:
                try:
                    os.unlink(stage_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
            try:
                os.close(directory_fd)
            except OSError:
                pass
