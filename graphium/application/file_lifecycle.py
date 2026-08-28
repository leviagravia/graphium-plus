"""GTK-free single-document file lifecycle orchestration for Graphium.

Graphium uses a native delta editor runtime. Full buffer text is synchronized only when a
physical Save needs it; merely checking whether New/Open/Quit needs confirmation must not
copy the whole document.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

from graphium.application.document_save_service import DocumentSaveService
from graphium.application.document_session import DocumentSession
from graphium.application.recent_files import RecentFilesController
from graphium.domain.document_identity import DocumentLoadResult
from graphium.domain.document_save import SaveDisposition
from graphium.domain.document_serialization import MixedLineEndingConfirmationRequired
from graphium.application.renderability import (
    InteractiveRenderabilityError,
    ensure_interactive_text_renderable,
)


class UnsavedDecision(str, Enum):
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


class ReloadDecision(str, Enum):
    DISCARD_AND_RELOAD = "discard-and-reload"
    CANCEL = "cancel"


class LifecycleUI(Protocol):
    def choose_open_path(self) -> str | None: ...
    def choose_save_path(self, current_path: str | None) -> str | None: ...
    def confirm_unsaved_changes(self, action_label: str) -> UnsavedDecision: ...
    def confirm_modified_reload(self) -> ReloadDecision: ...
    def confirm_overwrite(self, path: str) -> bool: ...
    def confirm_mixed_eol_normalization(self) -> bool: ...
    def show_error(self, title: str, message: str) -> None: ...
    def show_warning(self, title: str, message: str) -> None: ...


class EditorLifecyclePort(Protocol):
    def prepare_for_save(self) -> int: ...
    def initialize_new_text(self, text: str = "", *, clean: bool = True): ...
    def initialize_open(self, result: DocumentLoadResult): ...


class RecoveryLifecyclePort(Protocol):
    def document_state_changed(self) -> None: ...
    def invalidate(self) -> None: ...


@dataclass(frozen=True)
class LifecycleResult:
    completed: bool
    changed_document: bool = False
    saved: bool = False
    cancelled: bool = False


_REPLACEMENT_PERMIT_AUTHORITY = object()


@dataclass(frozen=True)
class DocumentReplacementPermit:
    _authority: object
    session_revision: int


class FileLifecycleController:
    __slots__ = ("session", "editor", "save_service", "loader", "ui", "recent_files", "recovery")

    def __init__(
        self,
        *,
        session: DocumentSession,
        editor: EditorLifecyclePort,
        save_service: DocumentSaveService,
        loader: Callable[[str], DocumentLoadResult],
        ui: LifecycleUI,
        recent_files: RecentFilesController | None = None,
        recovery: RecoveryLifecyclePort | None = None,
    ) -> None:
        if not isinstance(session, DocumentSession):
            raise TypeError("session must be DocumentSession")
        if editor is None:
            raise TypeError("editor is required")
        for method in ("prepare_for_save", "initialize_new_text", "initialize_open"):
            if not callable(getattr(editor, method, None)):
                raise TypeError(f"editor must implement {method}()")
        if not isinstance(save_service, DocumentSaveService):
            raise TypeError("save_service must be DocumentSaveService")
        if not callable(loader):
            raise TypeError("loader must be callable")
        if ui is None:
            raise TypeError("ui is required")
        self.session = session
        self.editor = editor
        self.save_service = save_service
        self.loader = loader
        self.ui = ui
        self.recent_files = recent_files
        self.recovery = recovery


    def _touch_recent_nonfatal(self, path: str) -> None:
        if self.recent_files is None:
            return
        try:
            self.recent_files.touch(path)
        except Exception as exc:
            self.ui.show_warning(
                "Recent file history was not saved",
                str(exc),
            )

    def _prepare_save(self) -> bool:
        try:
            self.editor.prepare_for_save()
            return True
        except Exception as exc:
            self.ui.show_error("Could not prepare editor state for saving", str(exc))
            return False

    def _show_save_warnings(self, result) -> None:
        if result.warnings:
            self.ui.show_warning("Save completed with warnings", "\n".join(result.warnings))
        elif result.disposition is not SaveDisposition.COMMITTED_CONFIRMED:
            self.ui.show_warning(
                "Save completed with uncertainty",
                "The file was committed, but Graphium could not confirm every post-save property.",
            )

    def save(self) -> LifecycleResult:
        if not self._prepare_save():
            return LifecycleResult(False)
        if self.session.logical_path is None or self.session.file_state is None:
            return self.save_as(_prepared=True)
        try:
            result = self.save_service.save()
        except MixedLineEndingConfirmationRequired:
            if not self.ui.confirm_mixed_eol_normalization():
                return LifecycleResult(False, cancelled=True)
            try:
                result = self.save_service.save(allow_mixed_eol_normalization=True)
            except Exception as exc:
                self.ui.show_error("Could not save file", str(exc))
                return LifecycleResult(False)
        except Exception as exc:
            self.ui.show_error("Could not save file", str(exc))
            return LifecycleResult(False)
        self._show_save_warnings(result)
        if self.recovery is not None:
            self.recovery.document_state_changed()
        return LifecycleResult(True, saved=True)

    def save_as(self, path: str | None = None, *, _prepared: bool = False) -> LifecycleResult:
        previous_logical_path = self.session.logical_path
        if not _prepared and not self._prepare_save():
            return LifecycleResult(False)
        target_path = path if path is not None else self.ui.choose_save_path(self.session.logical_path)
        if not target_path:
            return LifecycleResult(False, cancelled=True)
        try:
            observation = self.save_service.observe_save_as_target(target_path)
        except Exception as exc:
            self.ui.show_error("Could not inspect save destination", str(exc))
            return LifecycleResult(False)
        if observation.existing is not None and not self.ui.confirm_overwrite(observation.logical_target_path):
            return LifecycleResult(False, cancelled=True)
        try:
            result = self.save_service.save_as(observation)
        except MixedLineEndingConfirmationRequired:
            if not self.ui.confirm_mixed_eol_normalization():
                return LifecycleResult(False, cancelled=True)
            try:
                result = self.save_service.save_as(
                    observation,
                    allow_mixed_eol_normalization=True,
                )
            except Exception as exc:
                self.ui.show_error("Could not save file", str(exc))
                return LifecycleResult(False)
        except Exception as exc:
            self.ui.show_error("Could not save file", str(exc))
            return LifecycleResult(False)
        self._show_save_warnings(result)
        if self.recovery is not None:
            self.recovery.document_state_changed()
        if self.session.logical_path is not None and self.session.logical_path != previous_logical_path:
            self._touch_recent_nonfatal(self.session.logical_path)
        return LifecycleResult(True, saved=True)

    def _resolve_modified_before_replace(self, action_label: str) -> bool:
        # Deliberately do NOT synchronize/copy the whole live buffer just to ask whether
        # the user wants to discard it. State-ID savepoint semantics are sufficient.
        if not self.session.modified:
            return True
        decision = self.ui.confirm_unsaved_changes(action_label)
        if decision is UnsavedDecision.CANCEL:
            return False
        if decision is UnsavedDecision.DISCARD:
            return True
        if decision is UnsavedDecision.SAVE:
            return self.save().completed
        raise RuntimeError(f"unexpected unsaved decision: {decision!r}")

    def prepare_document_replacement(self, action_label: str) -> DocumentReplacementPermit | None:
        if not isinstance(action_label, str) or not action_label.strip():
            raise ValueError("action_label must be a non-empty string")
        if not self._resolve_modified_before_replace(action_label.strip()):
            return None
        return DocumentReplacementPermit(_REPLACEMENT_PERMIT_AUTHORITY, self.session.revision)

    def _replacement_permit_is_current(self, permit: DocumentReplacementPermit) -> bool:
        return (
            isinstance(permit, DocumentReplacementPermit)
            and permit._authority is _REPLACEMENT_PERMIT_AUTHORITY
            and permit.session_revision == self.session.revision
        )

    def new_document(self) -> LifecycleResult:
        if not self._resolve_modified_before_replace("create a new document"):
            return LifecycleResult(False, cancelled=True)
        try:
            self.editor.initialize_new_text("", clean=True)
        except Exception as exc:
            self.ui.show_error("Could not create new document", str(exc))
            return LifecycleResult(False)
        return LifecycleResult(True, changed_document=True)

    def open_document(
        self,
        path: str | None = None,
        *,
        replacement_permit: DocumentReplacementPermit | None = None,
    ) -> LifecycleResult:
        if replacement_permit is None:
            if not self._resolve_modified_before_replace("open another file"):
                return LifecycleResult(False, cancelled=True)
        elif not self._replacement_permit_is_current(replacement_permit):
            self.ui.show_error(
                "Could not open file",
                "The active document changed after replacement was authorized.",
            )
            return LifecycleResult(False)
        selected = path if path is not None else self.ui.choose_open_path()
        if not selected:
            return LifecycleResult(False, cancelled=True)
        # Load fully before replacing the active document. Failed Open preserves the
        # existing buffer/session/history.
        try:
            result = self.loader(selected)
        except Exception as exc:
            self.ui.show_error("Could not open file", str(exc))
            return LifecycleResult(False)
        # Loading establishes that this is valid supported text. The editor separately
        # protects the interactive Gtk.TextView surface from pathological logical lines.
        # The guard is content-neutral: reject before buffer installation, never truncate.
        try:
            ensure_interactive_text_renderable(result.text)
        except InteractiveRenderabilityError as exc:
            self.ui.show_error("File not opened — line too long for safe editing", str(exc))
            return LifecycleResult(False)
        try:
            self.editor.initialize_open(result)
        except Exception as exc:
            self.ui.show_error("Could not install opened file", str(exc))
            return LifecycleResult(False)
        self._touch_recent_nonfatal(result.file_state.binding.logical_path)
        return LifecycleResult(True, changed_document=True)

    def reload_document(self) -> LifecycleResult:
        """Reload the active named document from its current logical path.

        Reload is a deliberate disk re-acceptance boundary, not a generic document
        replacement. A modified buffer therefore gets a dedicated destructive choice:
        Cancel or Discard Changes and Reload. Reload never invokes the writer.
        """
        path = self.session.logical_path
        if path is None:
            return LifecycleResult(False)

        # Do not reuse the generic New/Open/Quit SAVE/DISCARD/CANCEL helper here.
        # Mature Revert/Reload ownership is intentionally asymmetric with Save: a user
        # choosing Reload either keeps the modified in-memory document or explicitly
        # discards it and accepts a complete fresh disk load.
        if self.session.modified:
            decision = self.ui.confirm_modified_reload()
            if decision is ReloadDecision.CANCEL:
                return LifecycleResult(False, cancelled=True)
            if decision is not ReloadDecision.DISCARD_AND_RELOAD:
                raise RuntimeError(f"unexpected reload decision: {decision!r}")

        try:
            result = self.loader(path)
        except Exception as exc:
            self.ui.show_error("Could not reload file", str(exc))
            return LifecycleResult(False)
        try:
            ensure_interactive_text_renderable(result.text)
        except InteractiveRenderabilityError as exc:
            self.ui.show_error("File not reloaded — line too long for safe editing", str(exc))
            return LifecycleResult(False)
        try:
            self.editor.initialize_open(result)
        except Exception as exc:
            self.ui.show_error("Could not install reloaded file", str(exc))
            return LifecycleResult(False)
        return LifecycleResult(True, changed_document=True)

    def request_close(self) -> LifecycleResult:
        if not self._resolve_modified_before_replace("quit Graphium"):
            return LifecycleResult(False, cancelled=True)
        if self.recovery is not None:
            self.recovery.invalidate()
        return LifecycleResult(True)
