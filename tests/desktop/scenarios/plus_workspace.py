from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

from tests.desktop.harness.runtime import drain, load_gtk3, text_of




class _DecisionUI:
    def __init__(self, base, decision):
        self._base = base
        self._decision = decision
        self.prompts = []

    def confirm_unsaved_changes(self, action_label):
        self.prompts.append(action_label)
        return self._decision

    def __getattr__(self, name):
        return getattr(self._base, name)


def _append_user_text(window, text: str) -> None:
    window.buffer.begin_user_action()
    try:
        window.buffer.insert(window.buffer.get_end_iter(), text)
    finally:
        window.buffer.end_user_action()


def _root_items(panel):
    model = panel.store
    values = []
    tree_iter = model.get_iter_first()
    while tree_iter is not None:
        item = model[tree_iter][2]
        if item is not None:
            values.append(item)
        tree_iter = model.iter_next(tree_iter)
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, args.repo)

    _Gdk, _GLib, Gtk = load_gtk3()
    from graphium_plus.adapters.gtk.application import GraphiumPlusApplication
    from graphium.application.file_lifecycle import UnsavedDecision

    app = GraphiumPlusApplication()
    assert app.register(None)
    app.activate(); drain(Gtk)
    window = app.window
    assert window is not None
    try:
        assert isinstance(window.workspace_paned, Gtk.Paned)
        assert window.workspace_paned.get_child1() is window.workspace_panel.widget
        assert window.workspace_paned.get_child2() is window._editor_scroller
        assert window.text_view.get_parent() is window._editor_scroller
        assert window.workspace.root is None
        assert window.workspace_panel.tree.get_enable_search()
        assert window.workspace_panel.tree.get_search_column() == 1
        assert window.workspace_panel.tree.get_selection().get_mode() == Gtk.SelectionMode.SINGLE
        assert window.workspace_toggle.get_active()
        assert window.workspace_panel.widget.get_visible()
        pane_position = window.workspace_paned.get_position()
        assert pane_position > 0
        assert pane_position < window.get_allocated_width() - pane_position

        window.workspace_toggle.set_active(False); drain(Gtk)
        assert not window.workspace_panel.widget.get_visible()
        window.workspace_toggle.set_active(True); drain(Gtk)
        assert window.workspace_panel.widget.get_visible()

        with tempfile.TemporaryDirectory(prefix="graphium-plus-workspace-") as td:
            root = Path(td)
            folder = root / "Chapter"; folder.mkdir()
            (folder / "deep.md").write_text("deep text", encoding="utf-8")
            (root / "draft.md").write_text("draft text", encoding="utf-8")
            (root / "image.bin").write_bytes(b"x")
            (root / ".hidden.md").write_text("hidden", encoding="utf-8")

            window._open_workspace_root(str(root)); drain(Gtk)
            root_items = _root_items(window.workspace_panel)
            assert [item.name for item in root_items] == ["Chapter", "draft.md", "image.bin"]
            assert all(item.name != "deep.md" for item in root_items)

            folder_path = window.workspace_panel.path_for_relative("Chapter")
            assert folder_path is not None
            window.workspace_panel.tree.expand_row(folder_path, False); drain(Gtk)
            assert window.workspace_panel.tree.row_expanded(folder_path)
            deep_tree_path = window.workspace_panel.path_for_relative("Chapter/deep.md")
            assert deep_tree_path is not None
            assert window.workspace_panel.select_relative_path("draft.md")

            window._refresh_workspace(); drain(Gtk)
            refreshed_path = window.workspace_panel.path_for_relative("Chapter")
            assert refreshed_path is not None
            assert window.workspace_panel.tree.row_expanded(refreshed_path)
            assert window.workspace_panel.path_for_relative("Chapter/deep.md") is not None
            selected = window.workspace_panel.selected_item()
            assert selected is not None and selected.relative_path == "draft.md"

            menu_labels = [
                child.get_label() for child in window.workspace_panel.context_menu.get_children()
                if isinstance(child, Gtk.MenuItem) and not isinstance(child, Gtk.SeparatorMenuItem)
            ]
            assert menu_labels == [
                "Open with Graphium Plus", "Reveal in File Manager",
                "New Text File", "New Folder", "Rename", "Duplicate", "Move to Trash",
            ]
            assert window.workspace_panel.context_open_in_graphium.get_sensitive()
            window.workspace_panel.context_open_in_graphium.activate(); drain(Gtk)
            assert text_of(window.text_view) == "draft text"
            assert window.core.session.logical_path == str(root / "draft.md")

            doc_path = window.workspace_panel.path_for_relative("draft.md")
            assert doc_path is not None
            reveal_calls = []
            window._file_manager_request = lambda method, path: reveal_calls.append((method, path))
            assert window.workspace_panel.select_relative_path("draft.md")
            window._reveal_workspace()
            assert reveal_calls[-1] == ("ShowItems", str(root / "draft.md"))
            window.workspace_panel.tree.get_selection().unselect_all()
            window._reveal_workspace()
            assert reveal_calls[-1] == ("ShowFolders", str(root))
            window.workspace_panel.tree.emit(
                "row-activated", doc_path, window.workspace_panel.tree.get_column(0)
            )
            drain(Gtk)
            assert text_of(window.text_view) == "draft text"
            assert window.core.session.logical_path == str(root / "draft.md")
            assert window._locate_active_document()
            drain(Gtk)
            selected = window.workspace_panel.selected_item()
            assert selected is not None and selected.path == str(root / "draft.md")

            deep = folder / "deep.md"
            assert window.open_path(str(deep)); drain(Gtk)
            window.workspace_panel.tree.collapse_all(); drain(Gtk)
            assert window._locate_active_document(); drain(Gtk)
            chapter_path = window.workspace_panel.path_for_relative("Chapter")
            assert chapter_path is not None and window.workspace_panel.tree.row_expanded(chapter_path)
            selected = window.workspace_panel.selected_item()
            assert selected is not None and selected.path == str(deep)

            assert window.open_path(str(root / "draft.md")); drain(Gtk)
            original_ui = window.core.lifecycle.ui
            _append_user_text(window, " modified"); drain(Gtk)
            assert window.core.session.modified
            cancel_ui = _DecisionUI(original_ui, UnsavedDecision.CANCEL)
            window.core.lifecycle.ui = cancel_ui
            cancelled = root / "cancelled.md"
            assert not window.create_workspace_text_file("cancelled", ".md", parent_path=str(root))
            drain(Gtk)
            assert not cancelled.exists()
            assert text_of(window.text_view) == "draft text modified"
            assert window.core.session.modified
            assert cancel_ui.prompts == ["open a new Workspace text file"]

            discard_ui = _DecisionUI(original_ui, UnsavedDecision.DISCARD)
            window.core.lifecycle.ui = discard_ui
            created = root / "created.md"
            assert window.create_workspace_text_file("created", ".md", parent_path=str(root))
            drain(Gtk)
            assert created.read_bytes() == b""
            assert window.core.session.logical_path == str(created)
            assert text_of(window.text_view) == ""
            assert not window.core.session.modified
            assert discard_ui.prompts == ["open a new Workspace text file"]
            selected = window.workspace_panel.selected_item()
            assert selected is not None and selected.path == str(created)

            assert not window.create_workspace_text_file("created.md", ".txt", parent_path=str(root))
            drain(Gtk)
            assert created.read_bytes() == b""
            assert window.core.session.logical_path == str(created)

            new_folder = root / "Notes"
            assert window.create_workspace_folder("Notes", parent_path=str(root))
            drain(Gtk)
            assert new_folder.is_dir() and not new_folder.is_symlink()
            selected = window.workspace_panel.selected_item()
            assert selected is not None and selected.path == str(new_folder)
            window.core.lifecycle.ui = original_ui
        return 0
    finally:
        window.destroy(); drain(Gtk)


if __name__ == "__main__":
    raise SystemExit(main())
