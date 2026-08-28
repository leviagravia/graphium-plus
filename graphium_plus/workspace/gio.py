"""Filesystem commit boundary for already-planned Workspace mutations."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import secrets
import stat

try:
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
except Exception:  # Keep pure planning/tests importable without PyGObject.
    Gio = None
    GLib = None

from .operations import (
    WorkspaceCreationPlan,
    WorkspaceDuplicatePlan,
    WorkspacePathToken,
    WorkspaceRenamePlan,
    WorkspaceTrashPlan,
    workspace_path_token,
)


@dataclass(frozen=True)
class WorkspaceCreationResult:
    success: bool
    path: str
    committed: bool = False
    message: str = ""


@dataclass(frozen=True)
class WorkspaceRenameResult:
    success: bool
    path: str
    committed: bool = False
    message: str = ""
    rollback_failed: bool = False


@dataclass(frozen=True)
class WorkspaceDuplicateResult:
    success: bool
    path: str
    committed: bool = False
    message: str = ""
    rollback_failed: bool = False


@dataclass(frozen=True)
class WorkspaceTrashResult:
    success: bool
    parent_path: str
    source_path: str
    accepted: bool = False
    message: str = ""


class WorkspaceGioAdapter:
    """Execute bounded local mutations after commit-time revalidation."""

    @staticmethod
    def _validated_parent(plan: WorkspaceCreationPlan | WorkspaceRenamePlan | WorkspaceDuplicatePlan) -> str | None:
        root = os.path.abspath(plan.root)
        parent = os.path.abspath(plan.parent_path)
        target_parent = os.path.abspath(os.path.dirname(plan.target_path))
        try:
            safe = (
                target_parent == parent
                and os.path.isdir(root)
                and not os.path.islink(root)
                and os.path.isdir(parent)
                and not os.path.islink(parent)
                and os.path.commonpath((os.path.realpath(root), os.path.realpath(parent)))
                == os.path.realpath(root)
            )
        except (OSError, TypeError, ValueError):
            safe = False
        return root if safe else None

    @staticmethod
    def _target_within_root(root: str, target_path: str) -> bool:
        try:
            return os.path.commonpath((os.path.realpath(root), os.path.realpath(target_path))) == os.path.realpath(root)
        except (OSError, TypeError, ValueError):
            return False

    def create(self, plan: WorkspaceCreationPlan) -> WorkspaceCreationResult:
        if not isinstance(plan, WorkspaceCreationPlan):
            raise TypeError("plan must be WorkspaceCreationPlan")
        root = self._validated_parent(plan)
        if root is None:
            return WorkspaceCreationResult(False, plan.target_path, message="The destination folder changed or resolves outside the Workspace.")
        if Gio is None or GLib is None:
            return WorkspaceCreationResult(False, plan.target_path, message="GIO is unavailable; nothing was created.")
        if plan.kind == "new-text-file":
            return self._create_file(plan, root)
        if plan.kind == "new-folder":
            return self._create_folder(plan, root)
        raise ValueError(f"unsupported Workspace creation operation: {plan.kind}")

    def _create_file(self, plan: WorkspaceCreationPlan, root: str) -> WorkspaceCreationResult:
        target = Gio.File.new_for_path(plan.target_path)
        stream = None
        committed = False
        try:
            stream = target.create(Gio.FileCreateFlags.NONE, None)
            stream.close(None)
            stream = None
            committed = True
            info = target.query_info(
                "standard::type,standard::is-symlink",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None,
            )
            if (
                info.get_is_symlink()
                or info.get_file_type() != Gio.FileType.REGULAR
                or not self._target_within_root(root, plan.target_path)
            ):
                return WorkspaceCreationResult(False, plan.target_path, True, "The file was created, but its confined regular-file identity could not be verified.")
            return WorkspaceCreationResult(True, plan.target_path, True)
        except GLib.Error as exc:
            return WorkspaceCreationResult(
                False,
                plan.target_path,
                committed,
                f"The file was created, but final verification failed: {exc.message}" if committed else f"The text file could not be created: {exc.message}",
            )
        finally:
            if stream is not None:
                try:
                    stream.close(None)
                except GLib.Error:
                    pass

    def _create_folder(self, plan: WorkspaceCreationPlan, root: str) -> WorkspaceCreationResult:
        target = Gio.File.new_for_path(plan.target_path)
        committed = False
        try:
            target.make_directory(None)
            committed = True
            info = target.query_info(
                "standard::type,standard::is-symlink",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None,
            )
            if (
                info.get_is_symlink()
                or info.get_file_type() != Gio.FileType.DIRECTORY
                or not self._target_within_root(root, plan.target_path)
            ):
                return WorkspaceCreationResult(False, plan.target_path, True, "The folder was created, but its confined directory identity could not be verified.")
            return WorkspaceCreationResult(True, plan.target_path, True)
        except GLib.Error as exc:
            return WorkspaceCreationResult(
                False,
                plan.target_path,
                committed,
                f"The folder was created, but final verification failed: {exc.message}" if committed else f"The folder could not be created: {exc.message}",
            )

    @staticmethod
    def _current_token(path: str) -> WorkspacePathToken | None:
        try:
            value = os.lstat(path)
        except OSError:
            return None
        return workspace_path_token(value)

    @staticmethod
    def _object_id(value: os.stat_result) -> tuple[int, int]:
        return int(value.st_dev), int(value.st_ino)

    @classmethod
    def _path_matches_descriptor(cls, path: str, fd: int) -> bool:
        try:
            named = os.lstat(path)
            pinned = os.fstat(fd)
        except OSError:
            return False
        return cls._object_id(named) == cls._object_id(pinned)

    @classmethod
    def _open_pinned_source(cls, plan: WorkspaceRenamePlan | WorkspaceTrashPlan) -> int | None:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        if plan.source_is_directory:
            flags |= getattr(os, "O_DIRECTORY", 0)
        try:
            fd = os.open(plan.source_path, flags)
        except OSError:
            return None
        try:
            pinned = os.fstat(fd)
            if workspace_path_token(pinned) != plan.source_token:
                raise ValueError("planned source signature is stale")
            if plan.source_is_directory:
                if not stat.S_ISDIR(pinned.st_mode):
                    raise ValueError("planned directory type changed")
            elif not stat.S_ISREG(pinned.st_mode):
                raise ValueError("planned file type changed")
            # Revalidate the pathname against the same strong signature after opening it.
            # Keeping this descriptor open pins the original inode across the GIO rename,
            # so a replacement lifetime cannot impersonate it through inode reuse.
            if cls._current_token(plan.source_path) != plan.source_token:
                raise ValueError("planned source pathname changed")
            if not cls._path_matches_descriptor(plan.source_path, fd):
                raise ValueError("planned source pathname no longer binds the pinned object")
            return fd
        except (OSError, ValueError):
            os.close(fd)
            return None

    @staticmethod
    def _collision_exists(_source_path: str, target_path: str) -> bool:
        return os.path.lexists(target_path)

    def rename(self, plan: WorkspaceRenamePlan) -> WorkspaceRenameResult:
        if not isinstance(plan, WorkspaceRenamePlan):
            raise TypeError("plan must be WorkspaceRenamePlan")
        root = self._validated_parent(plan)
        if root is None:
            return WorkspaceRenameResult(False, plan.source_path, message="The parent folder changed or resolves outside the Workspace.")
        if Gio is None or GLib is None:
            return WorkspaceRenameResult(False, plan.source_path, message="GIO is unavailable; nothing was renamed.")
        if os.path.islink(plan.source_path) or not self._target_within_root(root, plan.source_path):
            return WorkspaceRenameResult(False, plan.source_path, message="The selected item changed before it could be renamed.")

        source_fd = self._open_pinned_source(plan)
        if source_fd is None:
            return WorkspaceRenameResult(False, plan.source_path, message="The selected item changed before it could be renamed.")
        try:
            if self._collision_exists(plan.source_path, plan.target_path):
                return WorkspaceRenameResult(False, plan.source_path, message="A file or folder with that name already exists.")

            # One final pathname/descriptor binding check immediately before the single GIO
            # namespace mutation. The descriptor stays open until verification/rollback ends.
            if (
                self._current_token(plan.source_path) != plan.source_token
                or not self._path_matches_descriptor(plan.source_path, source_fd)
            ):
                return WorkspaceRenameResult(False, plan.source_path, message="The selected item changed before it could be renamed.")

            renamed = None
            failure_message = "Rename verification failed."
            try:
                renamed = Gio.File.new_for_path(plan.source_path).set_display_name(plan.display_name, None)
            except GLib.Error as exc:
                failure_message = f"The selected item could not be renamed: {exc.message}"

            # Post-rename ctime is allowed to change. Ownership is therefore proven by the
            # object pinned by source_fd, not by replaying the pre-commit metadata signature.
            committed = self._path_matches_descriptor(plan.target_path, source_fd)
            if renamed is not None:
                try:
                    returned = os.path.abspath(renamed.get_path() or "")
                    expected_type = Gio.FileType.DIRECTORY if plan.source_is_directory else Gio.FileType.REGULAR
                    info = renamed.query_info(
                        "standard::type,standard::is-symlink",
                        Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                        None,
                    )
                    if (
                        returned == plan.target_path
                        and committed
                        and not os.path.lexists(plan.source_path)
                        and not info.get_is_symlink()
                        and info.get_file_type() == expected_type
                        and self._target_within_root(root, plan.target_path)
                    ):
                        return WorkspaceRenameResult(True, plan.target_path, committed=True)
                except GLib.Error as exc:
                    failure_message = f"Rename committed, but final verification failed: {exc.message}"

            # Roll back only while the target pathname still binds the descriptor-pinned
            # original object. A substituted target can never acquire rollback authority.
            if committed and self._path_matches_descriptor(plan.target_path, source_fd):
                try:
                    Gio.File.new_for_path(plan.target_path).set_display_name(plan.source_name, None)
                except GLib.Error:
                    return WorkspaceRenameResult(
                        False, plan.target_path, committed=True,
                        message=f"{failure_message} Rollback failed.",
                        rollback_failed=True,
                    )
                if self._path_matches_descriptor(plan.source_path, source_fd):
                    return WorkspaceRenameResult(
                        False, plan.source_path,
                        message=f"{failure_message} The original name was restored.",
                    )
                return WorkspaceRenameResult(
                    False, plan.target_path, committed=True,
                    message=f"{failure_message} Rollback identity could not be verified.",
                    rollback_failed=True,
                )
            return WorkspaceRenameResult(False, plan.source_path, message=failure_message)
        finally:
            try:
                os.close(source_fd)
            except OSError:
                pass

    @staticmethod
    def _validated_trash_parent(plan: WorkspaceTrashPlan) -> str | None:
        root = os.path.abspath(plan.root)
        parent = os.path.abspath(plan.parent_path)
        source = os.path.abspath(plan.source_path)
        try:
            safe = (
                source != root
                and os.path.dirname(source) == parent
                and os.path.isdir(root)
                and not os.path.islink(root)
                and os.path.isdir(parent)
                and not os.path.islink(parent)
                and os.path.commonpath((os.path.realpath(root), os.path.realpath(parent)))
                == os.path.realpath(root)
                and os.path.commonpath((root, source)) == root
            )
        except (OSError, TypeError, ValueError):
            safe = False
        return root if safe else None

    @staticmethod
    def _trash_capability(file_obj, expected_type) -> tuple[bool, str]:
        try:
            info = file_obj.query_info(
                "standard::type,standard::is-symlink,access::can-trash",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None,
            )
        except GLib.Error as exc:
            return False, f"Trash capability could not be verified: {exc.message}"
        if info.get_is_symlink() or info.get_file_type() != expected_type:
            return False, "The selected item changed type or became a symbolic link."
        if info.has_attribute("access::can-trash") and not info.get_attribute_boolean("access::can-trash"):
            return False, "The filesystem reports that this item cannot be moved to Trash."
        return True, ""

    def trash(self, plan: WorkspaceTrashPlan) -> WorkspaceTrashResult:
        """Move one verified item to system Trash; never fall back to deletion.

        GIO exposes Trash as a pathname operation rather than an fd-bound mutation. The
        source is therefore strong-signature validated and descriptor-pinned through the
        call, with a final pathname/descriptor check immediately before `trash()`. This
        detects stale replacements before commit and prevents inode-reuse impersonation,
        while honestly retaining GIO's unavoidable last-instant pathname race boundary.
        """
        if not isinstance(plan, WorkspaceTrashPlan):
            raise TypeError("plan must be WorkspaceTrashPlan")
        if plan.kind != "move-to-trash":
            raise ValueError(f"unsupported Workspace Trash operation: {plan.kind}")
        root = self._validated_trash_parent(plan)
        if root is None:
            return WorkspaceTrashResult(
                False, plan.parent_path, plan.source_path,
                message="The selected item parent changed or resolves outside the Workspace.",
            )
        if Gio is None or GLib is None:
            return WorkspaceTrashResult(
                False, plan.parent_path, plan.source_path,
                message="GIO is unavailable; nothing was moved to Trash.",
            )
        if os.path.islink(plan.source_path) or not self._target_within_root(root, plan.source_path):
            return WorkspaceTrashResult(
                False, plan.parent_path, plan.source_path,
                message="The selected item changed before it could be moved to Trash.",
            )

        source_fd = self._open_pinned_source(plan)
        if source_fd is None:
            return WorkspaceTrashResult(
                False, plan.parent_path, plan.source_path,
                message="The selected item changed before it could be moved to Trash.",
            )
        try:
            source = Gio.File.new_for_path(plan.source_path)
            expected_type = Gio.FileType.DIRECTORY if plan.source_is_directory else Gio.FileType.REGULAR
            trashable, message = self._trash_capability(source, expected_type)
            if not trashable:
                return WorkspaceTrashResult(False, plan.parent_path, plan.source_path, message=message)

            # Final strong pathname/object revalidation immediately before the sole GIO
            # mutation. No permanent-delete or alternate move fallback is permitted.
            if (
                self._current_token(plan.source_path) != plan.source_token
                or not self._path_matches_descriptor(plan.source_path, source_fd)
            ):
                return WorkspaceTrashResult(
                    False, plan.parent_path, plan.source_path,
                    message="The selected item changed before it could be moved to Trash.",
                )
            try:
                accepted = bool(source.trash(None))
            except GLib.Error as exc:
                return WorkspaceTrashResult(
                    False, plan.parent_path, plan.source_path,
                    message=f"The selected item could not be moved to Trash: {exc.message}",
                )
            if not accepted:
                return WorkspaceTrashResult(
                    False, plan.parent_path, plan.source_path,
                    message="The system Trash operation was not accepted.",
                )
            if os.path.lexists(plan.source_path):
                return WorkspaceTrashResult(
                    False, plan.parent_path, plan.source_path, accepted=True,
                    message=(
                        "The system accepted the Trash operation, but absence of the original "
                        "pathname could not be verified. Workspace was refreshed."
                    ),
                )
            return WorkspaceTrashResult(True, plan.parent_path, plan.source_path, accepted=True)
        finally:
            try:
                os.close(source_fd)
            except OSError:
                pass

    @staticmethod
    def _write_all(fd: int, payload: bytes) -> None:
        view = memoryview(payload)
        offset = 0
        while offset < len(view):
            written = os.write(fd, view[offset:])
            if written <= 0:
                raise OSError("short/zero duplicate write")
            offset += written

    @classmethod
    def _hash_fd(cls, fd: int) -> tuple[int, str]:
        os.lseek(fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        total = 0
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            total += len(block)
            digest.update(block)
        return total, digest.hexdigest()

    @classmethod
    def _open_pinned_regular_source(cls, plan: WorkspaceDuplicatePlan) -> int | None:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            fd = os.open(plan.source_path, flags)
        except OSError:
            return None
        try:
            pinned = os.fstat(fd)
            if not stat.S_ISREG(pinned.st_mode):
                raise ValueError("planned source is not a regular file")
            if workspace_path_token(pinned) != plan.source_token:
                raise ValueError("planned source signature is stale")
            if cls._current_token(plan.source_path) != plan.source_token:
                raise ValueError("planned source pathname changed")
            if not cls._path_matches_descriptor(plan.source_path, fd):
                raise ValueError("planned source pathname no longer binds the pinned object")
            return fd
        except (OSError, ValueError):
            os.close(fd)
            return None

    @classmethod
    def _name_matches_descriptor(cls, name: str, directory_fd: int, fd: int) -> bool:
        try:
            named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            pinned = os.fstat(fd)
        except OSError:
            return False
        return cls._object_id(named) == cls._object_id(pinned)

    @classmethod
    def _unlink_owned_name(cls, name: str, directory_fd: int, fd: int) -> bool:
        if not cls._name_matches_descriptor(name, directory_fd, fd):
            return False
        try:
            os.unlink(name, dir_fd=directory_fd)
        except OSError:
            return False
        try:
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return False

    def duplicate(self, plan: WorkspaceDuplicatePlan) -> WorkspaceDuplicateResult:
        """Create one verified sibling copy from saved disk bytes only.

        The source object is descriptor-pinned. Bytes are copied into an exclusive hidden
        sibling stage, read back and SHA-256 verified, then committed without overwrite via
        a same-directory hard link. This follows Graphium Core's guarded-write ownership
        model rather than relying on path-only postconditions from older Workspace code.
        """
        if not isinstance(plan, WorkspaceDuplicatePlan):
            raise TypeError("plan must be WorkspaceDuplicatePlan")
        if plan.kind != "duplicate-file":
            raise ValueError(f"unsupported Workspace duplicate operation: {plan.kind}")
        root = self._validated_parent(plan)
        if root is None:
            return WorkspaceDuplicateResult(False, plan.source_path, message="The containing folder changed or resolves outside the Workspace.")
        if os.path.islink(plan.source_path) or not self._target_within_root(root, plan.source_path):
            return WorkspaceDuplicateResult(False, plan.source_path, message="The selected file changed before it could be duplicated.")

        source_fd = self._open_pinned_regular_source(plan)
        if source_fd is None:
            return WorkspaceDuplicateResult(False, plan.source_path, message="The selected file changed before it could be duplicated.")

        directory_fd = None
        stage_fd = None
        stage_name = f".graphium-plus-duplicate-{os.getpid()}-{secrets.token_hex(16)}.tmp"
        target_name = os.path.basename(plan.target_path)
        stage_identity = None
        committed = False
        try:
            dir_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                directory_fd = os.open(plan.parent_path, dir_flags)
            except OSError as exc:
                return WorkspaceDuplicateResult(False, plan.source_path, message=f"The containing folder cannot be opened safely: {exc}")
            if not self._path_matches_descriptor(plan.parent_path, directory_fd):
                return WorkspaceDuplicateResult(False, plan.source_path, message="The containing folder changed before duplication.")
            if self._current_token(plan.source_path) != plan.source_token or not self._path_matches_descriptor(plan.source_path, source_fd):
                return WorkspaceDuplicateResult(False, plan.source_path, message="The selected file changed before it could be duplicated.")
            try:
                os.stat(target_name, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            except OSError as exc:
                return WorkspaceDuplicateResult(False, plan.source_path, message=f"The duplicate destination cannot be inspected safely: {exc}")
            else:
                return WorkspaceDuplicateResult(False, plan.source_path, message="The duplicate destination already exists.")

            stage_flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                stage_fd = os.open(stage_name, stage_flags, 0o600, dir_fd=directory_fd)
            except OSError as exc:
                return WorkspaceDuplicateResult(False, plan.source_path, message=f"A safe duplicate stage could not be created: {exc}")
            stage_identity = self._object_id(os.fstat(stage_fd))

            source_before = os.fstat(source_fd)
            os.lseek(source_fd, 0, os.SEEK_SET)
            copied_digest = hashlib.sha256()
            copied_size = 0
            while True:
                block = os.read(source_fd, 1024 * 1024)
                if not block:
                    break
                self._write_all(stage_fd, block)
                copied_digest.update(block)
                copied_size += len(block)
            source_after = os.fstat(source_fd)
            if (
                workspace_path_token(source_before) != plan.source_token
                or workspace_path_token(source_after) != plan.source_token
                or copied_size != plan.source_token.size
                or self._current_token(plan.source_path) != plan.source_token
                or not self._path_matches_descriptor(plan.source_path, source_fd)
            ):
                return WorkspaceDuplicateResult(False, plan.source_path, message="The selected file changed while it was being duplicated.")

            os.fchmod(stage_fd, stat.S_IMODE(source_before.st_mode))
            os.fsync(stage_fd)
            verified_size, verified_digest = self._hash_fd(stage_fd)
            if verified_size != copied_size or verified_digest != copied_digest.hexdigest():
                return WorkspaceDuplicateResult(False, plan.source_path, message="The staged duplicate bytes could not be verified.")

            # Late revalidation immediately before the no-overwrite namespace commit.
            if (
                not self._path_matches_descriptor(plan.parent_path, directory_fd)
                or self._current_token(plan.source_path) != plan.source_token
                or not self._path_matches_descriptor(plan.source_path, source_fd)
            ):
                return WorkspaceDuplicateResult(False, plan.source_path, message="The source or containing folder changed before duplicate commit.")
            try:
                os.link(
                    stage_name,
                    target_name,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except FileExistsError:
                return WorkspaceDuplicateResult(False, plan.source_path, message="The duplicate destination appeared before commit.")
            except OSError as exc:
                return WorkspaceDuplicateResult(False, plan.source_path, message=f"The duplicate could not be committed safely: {exc}")
            committed = True
            try:
                os.unlink(stage_name, dir_fd=directory_fd)
            except OSError:
                # The final target is already committed; verification/rollback below still owns it via stage_fd.
                pass

            target_matches = self._name_matches_descriptor(target_name, directory_fd, stage_fd)
            try:
                target_stat = os.stat(target_name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError:
                target_stat = None
            source_still_same = (
                self._current_token(plan.source_path) == plan.source_token
                and self._path_matches_descriptor(plan.source_path, source_fd)
            )
            if (
                target_matches
                and target_stat is not None
                and stat.S_ISREG(target_stat.st_mode)
                and source_still_same
                and self._target_within_root(root, plan.target_path)
            ):
                warning = ""
                try:
                    os.fsync(directory_fd)
                except OSError as exc:
                    warning = f"Duplicate created; parent-directory durability sync failed: {exc}"
                return WorkspaceDuplicateResult(True, plan.target_path, committed=True, message=warning)

            if target_matches and self._unlink_owned_name(target_name, directory_fd, stage_fd):
                committed = False
                return WorkspaceDuplicateResult(False, plan.source_path, message="Duplicate verification failed; the created target was removed.")
            return WorkspaceDuplicateResult(
                False,
                plan.target_path,
                committed=True,
                message="Duplicate verification failed and the created target could not be removed safely.",
                rollback_failed=True,
            )
        except OSError as exc:
            if committed and directory_fd is not None and stage_fd is not None and self._name_matches_descriptor(target_name, directory_fd, stage_fd):
                if self._unlink_owned_name(target_name, directory_fd, stage_fd):
                    committed = False
            return WorkspaceDuplicateResult(
                False,
                plan.target_path if committed else plan.source_path,
                committed=committed,
                message=f"The selected file could not be duplicated safely: {exc}",
                rollback_failed=committed,
            )
        finally:
            if directory_fd is not None and stage_fd is not None and stage_identity is not None:
                try:
                    if self._name_matches_descriptor(stage_name, directory_fd, stage_fd):
                        os.unlink(stage_name, dir_fd=directory_fd)
                except OSError:
                    pass
            if stage_fd is not None:
                try:
                    os.close(stage_fd)
                except OSError:
                    pass
            if directory_fd is not None:
                try:
                    os.close(directory_fd)
                except OSError:
                    pass
            try:
                os.close(source_fd)
            except OSError:
                pass

