"""Single-root authority and lazy activation planning for Graphium Plus Workspace."""
from __future__ import annotations

from dataclasses import dataclass
import os
import stat
from collections.abc import Callable

from .model import DirectoryListing, WorkspaceError, WorkspaceItem, normalize_root, path_is_within_root, scan_directory
from .operations import (
    WorkspaceDuplicatePlan,
    WorkspaceRenamePlan,
    WorkspaceTrashPlan,
    plan_workspace_duplicate,
    plan_workspace_rename,
    plan_workspace_trash,
    workspace_path_token,
)


@dataclass(frozen=True)
class WorkspaceActivation:
    kind: str
    path: str
    message: str = ""


class WorkspaceController:
    def __init__(self, scanner: Callable[..., DirectoryListing] = scan_directory) -> None:
        if not callable(scanner):
            raise TypeError("scanner must be callable")
        self._scanner = scanner
        self._root: str | None = None
        self._generation = 0
        self._listings: dict[str, DirectoryListing] = {}

    @property
    def root(self) -> str | None:
        return self._root

    def bind_root(self, root: str) -> DirectoryListing:
        canonical = normalize_root(root)
        generation = self._generation + 1
        listing = self._scanner(canonical, canonical, generation=generation)
        if listing.root != canonical or listing.relative_directory != "":
            raise WorkspaceError("Workspace scanner returned a foreign root.")
        self._root = canonical
        self._generation = generation
        self._listings = {"": listing}
        return listing

    def refresh(self) -> DirectoryListing | None:
        if self._root is None:
            return None
        generation = self._generation + 1
        listing = self._scanner(self._root, self._root, generation=generation)
        if listing.root != self._root or listing.relative_directory != "":
            raise WorkspaceError("Workspace scanner changed the bound root.")
        self._generation = generation
        self._listings = {"": listing}
        return listing

    def load_directory(self, item: WorkspaceItem) -> DirectoryListing:
        current = self._require_current(item)
        if not current.is_directory:
            raise WorkspaceError("Workspace item is not a directory.")
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic-link directories are not expanded from Workspace.")
        if not path_is_within_root(self._require_root(), current.path):
            raise WorkspaceError("Workspace directory resolves outside the bound root.")
        listing = self._scanner(self._root, current.path, generation=self._generation)
        if listing.root != self._root or listing.relative_directory != current.relative_path:
            raise WorkspaceError("Workspace scanner returned a foreign directory.")
        self._listings[current.relative_path] = listing
        return listing

    def relative_path_for_document(self, path: str | None) -> str:
        root = self._require_root()
        if not isinstance(path, str) or not path:
            raise WorkspaceError("The active document has no filesystem path.")
        absolute = os.path.abspath(path)
        if os.path.islink(absolute):
            raise WorkspaceError("A symbolic-link document cannot be located in Workspace.")
        if not path_is_within_root(root, absolute):
            raise WorkspaceError("The active document is outside the current Workspace.")
        try:
            observed = os.lstat(absolute)
        except OSError as exc:
            raise WorkspaceError("The active document no longer exists on disk.") from exc
        if not stat.S_ISREG(observed.st_mode):
            raise WorkspaceError("The active document is not a regular Workspace file.")
        relative = os.path.relpath(absolute, root)
        if relative == "." or any(part.startswith(".") for part in relative.split(os.sep)):
            raise WorkspaceError("The active document is not visible in Workspace.")
        return relative

    def creation_parent(self, selected: WorkspaceItem | None) -> str:
        root = self._require_root()
        if selected is None:
            parent = root
        else:
            current = self._require_current(selected)
            if current.is_symlink or os.path.islink(current.path):
                raise WorkspaceError("A symbolic link cannot be used as a creation destination.")
            parent = current.path if current.is_directory else os.path.dirname(current.path)
        if os.path.islink(parent) or not os.path.isdir(parent):
            raise WorkspaceError("The selected destination folder no longer exists or is a symbolic link.")
        if not path_is_within_root(root, parent):
            raise WorkspaceError("The selected destination resolves outside the Workspace.")
        return parent


    def plan_rename(
        self,
        item: WorkspaceItem | None,
        raw_name: str,
        *,
        active_document_path: str | None = None,
    ) -> WorkspaceRenamePlan:
        if item is None:
            raise WorkspaceError("Select one Workspace file or folder to rename.")
        current = self._require_current(item)
        root = self._require_root()
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic links cannot be renamed from Workspace.")
        if not path_is_within_root(root, current.path):
            raise WorkspaceError("The selected item resolves outside the Workspace.")
        try:
            observed = os.lstat(current.path)
        except OSError as exc:
            raise WorkspaceError("The selected item no longer exists.") from exc
        if current.is_directory:
            if not stat.S_ISDIR(observed.st_mode):
                raise WorkspaceError("The selected folder changed before it could be renamed.")
        elif not stat.S_ISREG(observed.st_mode):
            raise WorkspaceError("Only regular files and folders can be renamed.")

        self._reject_active_document_scope(
            current, active_document_path,
            message="The active document or a folder containing it cannot be renamed from Workspace.",
        )

        return plan_workspace_rename(
            root,
            current.path,
            raw_name,
            source_is_directory=current.is_directory,
            source_token=workspace_path_token(observed),
        )

    def plan_trash(
        self,
        item: WorkspaceItem | None,
        *,
        active_document_path: str | None = None,
    ) -> WorkspaceTrashPlan:
        if item is None:
            raise WorkspaceError("Select one Workspace file or folder to move to Trash.")
        current = self._require_current(item)
        root = self._require_root()
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic links cannot be moved to Trash from Workspace.")
        if not path_is_within_root(root, current.path):
            raise WorkspaceError("The selected item resolves outside the Workspace.")
        try:
            observed = os.lstat(current.path)
        except OSError as exc:
            raise WorkspaceError("The selected item no longer exists.") from exc
        if current.is_directory:
            if not stat.S_ISDIR(observed.st_mode):
                raise WorkspaceError("The selected folder changed before it could be moved to Trash.")
        elif not stat.S_ISREG(observed.st_mode):
            raise WorkspaceError("Only regular files and folders can be moved to Trash.")

        self._reject_active_document_scope(
            current, active_document_path,
            message="The active document or a folder containing it cannot be moved to Trash from Workspace.",
        )
        return plan_workspace_trash(
            root,
            current.path,
            source_is_directory=current.is_directory,
            source_token=workspace_path_token(observed),
        )

    def plan_duplicate(self, item: WorkspaceItem | None) -> WorkspaceDuplicatePlan:
        if item is None:
            raise WorkspaceError("Select one regular Workspace file to duplicate.")
        current = self._require_current(item)
        root = self._require_root()
        if current.is_directory:
            raise WorkspaceError("Folder duplication is outside Workspace scope.")
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic links cannot be duplicated from Workspace.")
        if not path_is_within_root(root, current.path):
            raise WorkspaceError("The selected file resolves outside the Workspace.")
        try:
            observed = os.lstat(current.path)
        except OSError as exc:
            raise WorkspaceError("The selected file no longer exists.") from exc
        if not stat.S_ISREG(observed.st_mode):
            raise WorkspaceError("Only regular files can be duplicated from Workspace.")
        parent = os.path.dirname(current.path)
        try:
            occupied_names = tuple(os.listdir(parent))
        except OSError as exc:
            raise WorkspaceError(f"The containing folder cannot be read: {exc}") from exc
        return plan_workspace_duplicate(
            root,
            current.path,
            occupied_names,
            source_token=workspace_path_token(observed),
        )

    def activation_for(self, item: WorkspaceItem) -> WorkspaceActivation:
        current = self._require_current(item)
        if current.is_directory:
            if current.is_symlink or os.path.islink(current.path):
                return WorkspaceActivation("blocked", current.path, "Symbolic-link directories are not expanded from Workspace.")
            return WorkspaceActivation("directory", current.path)
        if current.is_symlink or os.path.islink(current.path):
            return WorkspaceActivation("blocked", current.path, "Symbolic links are not opened from Workspace.")
        if not path_is_within_root(self._require_root(), current.path):
            return WorkspaceActivation("blocked", current.path, "The selected file resolves outside the Workspace.")
        if not os.path.isfile(current.path):
            return WorkspaceActivation("missing", current.path, "The selected file no longer exists.")
        return WorkspaceActivation("internal" if current.text_document else "external", current.path)

    @staticmethod
    def _reject_active_document_scope(
        item: WorkspaceItem,
        active_document_path: str | None,
        *,
        message: str,
    ) -> None:
        if not active_document_path:
            return
        active = os.path.realpath(os.path.abspath(active_document_path))
        source = os.path.realpath(item.path)
        try:
            blocked = source == active if not item.is_directory else os.path.commonpath((source, active)) == source
        except ValueError:
            blocked = False
        if blocked:
            raise WorkspaceError(message)

    def _require_root(self) -> str:
        if self._root is None:
            raise WorkspaceError("No Workspace folder is selected.")
        return self._root

    def _require_current(self, item: WorkspaceItem) -> WorkspaceItem:
        if not isinstance(item, WorkspaceItem):
            raise TypeError("item must be WorkspaceItem")
        root = self._require_root()
        if item.root != root or item.generation != self._generation:
            raise WorkspaceError("Workspace item is stale or belongs to another root.")
        for listing in self._listings.values():
            for current in listing.items:
                if current.path == item.path:
                    if current != item:
                        raise WorkspaceError("Workspace item is stale or foreign.")
                    return current
        raise WorkspaceError("Workspace item is stale or foreign.")
