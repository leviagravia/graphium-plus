"""GTK-free, lazy one-directory Workspace model."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re


TEXT_SUFFIXES = frozenset({".txt", ".md"})
_NATURAL_PARTS = re.compile(r"(\d+)")


class WorkspaceError(ValueError):
    """A Workspace root/item cannot be used safely."""


@dataclass(frozen=True)
class WorkspaceItem:
    root: str
    path: str
    relative_path: str
    name: str
    is_directory: bool
    is_symlink: bool
    text_document: bool
    generation: int


@dataclass(frozen=True)
class DirectoryListing:
    root: str
    directory: str
    relative_directory: str
    items: tuple[WorkspaceItem, ...]
    generation: int
    diagnostics: tuple[str, ...] = ()


def normalize_root(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise WorkspaceError("Choose a non-empty Workspace folder.")
    absolute = os.path.abspath(os.path.expanduser(path.strip()))
    if os.path.islink(absolute):
        raise WorkspaceError("The Workspace root cannot be a symbolic link.")
    if not os.path.isdir(absolute):
        raise WorkspaceError(f"Workspace folder does not exist: {absolute}")
    return absolute


def path_is_within_root(root: str, path: str) -> bool:
    try:
        real_root = os.path.realpath(normalize_root(root))
        real_path = os.path.realpath(os.path.abspath(path))
        return os.path.commonpath((real_root, real_path)) == real_root
    except (OSError, TypeError, ValueError, WorkspaceError):
        return False


def _relative(root: str, path: str) -> str:
    value = os.path.relpath(path, root)
    return "" if value == "." else value


def _natural_name_key(value: str) -> tuple[tuple[int, object, str], ...]:
    parts = []
    for part in _NATURAL_PARTS.split(value):
        if not part:
            continue
        if part.isdigit():
            parts.append((0, int(part), part))
        else:
            parts.append((1, part.casefold(), part))
    return tuple(parts)


def scan_directory(root: str, directory: str, *, generation: int) -> DirectoryListing:
    canonical_root = normalize_root(root)
    absolute = os.path.abspath(directory)
    if os.path.islink(absolute):
        raise WorkspaceError("Symbolic-link directories are not expanded from Workspace.")
    if not path_is_within_root(canonical_root, absolute):
        raise WorkspaceError("Workspace directory resolves outside the bound root.")
    if not os.path.isdir(absolute):
        raise WorkspaceError("Workspace directory no longer exists.")

    items: list[WorkspaceItem] = []
    diagnostics: list[str] = []
    try:
        entries = list(os.scandir(absolute))
    except OSError as exc:
        raise WorkspaceError(f"Cannot read Workspace directory: {exc}") from exc

    classified = []
    for entry in entries:
        if entry.name.startswith("."):
            continue
        try:
            is_symlink = entry.is_symlink()
            is_directory = entry.is_dir(follow_symlinks=False)
        except OSError as exc:
            diagnostics.append(f"Cannot inspect {entry.name}: {exc}")
            continue
        classified.append((entry, is_directory, is_symlink))

    classified.sort(
        key=lambda value: (not value[1], _natural_name_key(value[0].name), value[0].name)
    )
    for entry, is_directory, is_symlink in classified:
        path = os.path.abspath(entry.path)
        relative = _relative(canonical_root, path)
        suffix = Path(entry.name).suffix.casefold()
        items.append(WorkspaceItem(
            root=canonical_root,
            path=path,
            relative_path=relative,
            name=entry.name,
            is_directory=is_directory,
            is_symlink=is_symlink,
            text_document=(not is_directory and not is_symlink and suffix in TEXT_SUFFIXES),
            generation=generation,
        ))

    return DirectoryListing(
        root=canonical_root,
        directory=absolute,
        relative_directory=_relative(canonical_root, absolute),
        items=tuple(items),
        generation=generation,
        diagnostics=tuple(diagnostics),
    )
