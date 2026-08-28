"""Pure planning primitives for bounded Workspace mutations."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from .model import TEXT_SUFFIXES, WorkspaceError, normalize_root, path_is_within_root


MAX_BASENAME_BYTES = 255


@dataclass(frozen=True)
class WorkspaceCreationPlan:
    kind: str
    root: str
    parent_path: str
    target_path: str
    display_name: str


@dataclass(frozen=True)
class WorkspacePathToken:
    """Strong pre-commit filesystem observation for one Workspace object."""

    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    uid: int
    gid: int
    nlink: int


def workspace_path_token(value: os.stat_result) -> WorkspacePathToken:
    return WorkspacePathToken(
        device=int(value.st_dev),
        inode=int(value.st_ino),
        mode=int(value.st_mode),
        size=int(value.st_size),
        mtime_ns=int(value.st_mtime_ns),
        ctime_ns=int(getattr(value, "st_ctime_ns", 0)),
        uid=int(getattr(value, "st_uid", 0)),
        gid=int(getattr(value, "st_gid", 0)),
        nlink=int(getattr(value, "st_nlink", 1)),
    )




@dataclass(frozen=True)
class WorkspaceDuplicatePlan:
    kind: str
    root: str
    parent_path: str
    source_path: str
    target_path: str
    source_name: str
    display_name: str
    source_token: WorkspacePathToken


@dataclass(frozen=True)
class WorkspaceRenamePlan:
    kind: str
    root: str
    parent_path: str
    source_path: str
    target_path: str
    source_name: str
    display_name: str
    source_is_directory: bool
    source_token: WorkspacePathToken


@dataclass(frozen=True)
class WorkspaceTrashPlan:
    kind: str
    root: str
    parent_path: str
    source_path: str
    source_name: str
    source_is_directory: bool
    source_token: WorkspacePathToken


def _validated_basename(raw_name: str, *, label: str) -> str:
    if not isinstance(raw_name, str):
        raise TypeError(f"{label} must be a string")
    name = raw_name.strip()
    if not name:
        raise WorkspaceError(f"Enter a {label}.")
    if "\x00" in name:
        raise WorkspaceError(f"The {label} contains an invalid character.")
    separators = {os.sep, "/", "\\"}
    if os.altsep:
        separators.add(os.altsep)
    if any(separator and separator in name for separator in separators):
        raise WorkspaceError(f"Enter one {label}, not a path.")
    if name in {".", ".."} or name.startswith("."):
        raise WorkspaceError(f"Hidden or reserved {label}s are not allowed here.")
    if len(os.fsencode(name)) > MAX_BASENAME_BYTES:
        raise WorkspaceError(f"The {label} is too long for the filesystem.")
    return name


def normalize_text_name(raw_name: str, *, suffix: str = ".txt") -> str:
    name = _validated_basename(raw_name, label="file name")
    normalized_suffix = suffix.strip().casefold() if isinstance(suffix, str) else ""
    if normalized_suffix and not normalized_suffix.startswith("."):
        normalized_suffix = f".{normalized_suffix}"
    if normalized_suffix not in TEXT_SUFFIXES:
        raise WorkspaceError("New Workspace files must use .txt or .md.")
    requested = Path(name).suffix.casefold()
    if requested:
        if requested not in TEXT_SUFFIXES:
            raise WorkspaceError("New Workspace files must use .txt or .md.")
        final_name = name
    else:
        final_name = f"{name}{normalized_suffix}"
    if len(os.fsencode(final_name)) > MAX_BASENAME_BYTES:
        raise WorkspaceError("The file name is too long for the filesystem.")
    return final_name


def normalize_folder_name(raw_name: str) -> str:
    return _validated_basename(raw_name, label="folder name")


def _plan(root: str, parent_path: str, display_name: str, *, kind: str) -> WorkspaceCreationPlan:
    canonical_root = normalize_root(root)
    parent = os.path.abspath(parent_path)
    if os.path.islink(parent) or not os.path.isdir(parent):
        raise WorkspaceError("The destination folder no longer exists or is a symbolic link.")
    if not path_is_within_root(canonical_root, parent):
        raise WorkspaceError("The destination resolves outside the Workspace.")
    target = os.path.abspath(os.path.join(parent, display_name))
    if os.path.dirname(target) != parent or not path_is_within_root(canonical_root, target):
        raise WorkspaceError("The new item would escape the Workspace.")
    return WorkspaceCreationPlan(kind, canonical_root, parent, target, display_name)


def plan_new_text_file(root: str, parent_path: str, raw_name: str, *, suffix: str = ".txt") -> WorkspaceCreationPlan:
    return _plan(
        root,
        parent_path,
        normalize_text_name(raw_name, suffix=suffix),
        kind="new-text-file",
    )


def plan_new_folder(root: str, parent_path: str, raw_name: str) -> WorkspaceCreationPlan:
    return _plan(
        root,
        parent_path,
        normalize_folder_name(raw_name),
        kind="new-folder",
    )


def normalize_rename_name(raw_name: str) -> str:
    return _validated_basename(raw_name, label="new name")


def plan_workspace_rename(
    root: str,
    source_path: str,
    raw_name: str,
    *,
    source_is_directory: bool,
    source_token: WorkspacePathToken,
) -> WorkspaceRenamePlan:
    if not isinstance(source_path, str) or not source_path.strip():
        raise WorkspaceError("Select one Workspace file or folder to rename.")
    if not isinstance(source_is_directory, bool):
        raise TypeError("source_is_directory must be boolean")
    if not isinstance(source_token, WorkspacePathToken):
        raise TypeError("source_token must be WorkspacePathToken")

    canonical_root = normalize_root(root)
    source = os.path.abspath(source_path)
    parent = os.path.dirname(source)
    if source == canonical_root:
        raise WorkspaceError("The Workspace root itself cannot be renamed here.")
    if not path_is_within_root(canonical_root, source) or not path_is_within_root(canonical_root, parent):
        raise WorkspaceError("The selected item resolves outside the Workspace.")

    source_name = os.path.basename(source)
    display_name = normalize_rename_name(raw_name)
    if display_name == source_name:
        raise WorkspaceError("The new name is unchanged.")
    target = os.path.abspath(os.path.join(parent, display_name))
    if os.path.dirname(target) != parent or not path_is_within_root(canonical_root, target):
        raise WorkspaceError("The renamed item would escape the Workspace.")
    return WorkspaceRenamePlan(
        kind="rename",
        root=canonical_root,
        parent_path=parent,
        source_path=source,
        target_path=target,
        source_name=source_name,
        display_name=display_name,
        source_is_directory=source_is_directory,
        source_token=source_token,
    )


def _truncate_utf8_component(value: str, max_bytes: int) -> str:
    if max_bytes < 1:
        raise WorkspaceError("The duplicate file name cannot fit on this filesystem.")
    candidate = value
    while candidate and len(os.fsencode(candidate)) > max_bytes:
        candidate = candidate[:-1]
    if not candidate:
        raise WorkspaceError("The duplicate file name cannot fit on this filesystem.")
    return candidate


def next_duplicate_name(source_name: str, occupied_names: tuple[str, ...] | list[str]) -> str:
    """Return a deterministic, same-parent duplicate basename without overwriting."""
    source_name = _validated_basename(source_name, label="file name")
    if not isinstance(occupied_names, (tuple, list)) or not all(isinstance(name, str) for name in occupied_names):
        raise TypeError("occupied_names must be a tuple or list of strings")
    suffix = Path(source_name).suffix
    stem = source_name[:-len(suffix)] if suffix else source_name
    occupied = {name.casefold() for name in occupied_names}
    for index in range(1, 10001):
        marker = " copy" if index == 1 else f" copy {index}"
        tail = marker + suffix
        fitted_stem = _truncate_utf8_component(stem, MAX_BASENAME_BYTES - len(os.fsencode(tail)))
        candidate = f"{fitted_stem}{tail}"
        if candidate.casefold() not in occupied:
            return candidate
    raise WorkspaceError("No safe duplicate name is available in this folder.")


def plan_workspace_duplicate(
    root: str,
    source_path: str,
    occupied_names: tuple[str, ...] | list[str],
    *,
    source_token: WorkspacePathToken,
) -> WorkspaceDuplicatePlan:
    if not isinstance(source_path, str) or not source_path.strip():
        raise WorkspaceError("Select one regular Workspace file to duplicate.")
    if not isinstance(source_token, WorkspacePathToken):
        raise TypeError("source_token must be WorkspacePathToken")
    canonical_root = normalize_root(root)
    source = os.path.abspath(source_path)
    parent = os.path.dirname(source)
    if source == canonical_root:
        raise WorkspaceError("The Workspace root cannot be duplicated.")
    if not path_is_within_root(canonical_root, source) or not path_is_within_root(canonical_root, parent):
        raise WorkspaceError("The selected file resolves outside the Workspace.")
    source_name = os.path.basename(source)
    display_name = next_duplicate_name(source_name, occupied_names)
    target = os.path.abspath(os.path.join(parent, display_name))
    if os.path.dirname(target) != parent or not path_is_within_root(canonical_root, target):
        raise WorkspaceError("The duplicate would escape the Workspace.")
    return WorkspaceDuplicatePlan(
        kind="duplicate-file",
        root=canonical_root,
        parent_path=parent,
        source_path=source,
        target_path=target,
        source_name=source_name,
        display_name=display_name,
        source_token=source_token,
    )

def plan_workspace_trash(
    root: str,
    source_path: str,
    *,
    source_is_directory: bool,
    source_token: WorkspacePathToken,
) -> WorkspaceTrashPlan:
    """Build one root-confined system-Trash plan with no delete fallback."""
    if not isinstance(source_path, str) or not source_path.strip():
        raise WorkspaceError("Select one Workspace file or folder to move to Trash.")
    if not isinstance(source_is_directory, bool):
        raise TypeError("source_is_directory must be boolean")
    if not isinstance(source_token, WorkspacePathToken):
        raise TypeError("source_token must be WorkspacePathToken")

    canonical_root = normalize_root(root)
    source = os.path.abspath(source_path)
    parent = os.path.dirname(source)
    if source == canonical_root:
        raise WorkspaceError("The Workspace root itself cannot be moved to Trash here.")
    if not path_is_within_root(canonical_root, source) or not path_is_within_root(canonical_root, parent):
        raise WorkspaceError("The selected item resolves outside the Workspace.")
    return WorkspaceTrashPlan(
        kind="move-to-trash",
        root=canonical_root,
        parent_path=parent,
        source_path=source,
        source_name=os.path.basename(source),
        source_is_directory=source_is_directory,
        source_token=source_token,
    )

