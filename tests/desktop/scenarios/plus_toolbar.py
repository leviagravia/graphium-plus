from __future__ import annotations

import argparse
import sys

from tests.desktop.harness.runtime import drain, load_gtk3


def _paths_use(window, namespace: str) -> bool:
    paths = window._xdg_paths
    return all(
        path.name == namespace
        for path in (paths.config, paths.data, paths.cache, paths.state)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, args.repo)

    _Gdk, _GLib, Gtk = load_gtk3()
    from graphium_plus.adapters.gtk.application import GraphiumPlusApplication

    app = GraphiumPlusApplication()
    assert app.register(None)
    app.activate(); drain(Gtk)
    window = app.window
    assert window is not None
    try:
        assert app.get_application_id() == "io.github.leviagravia.GraphiumPlus"
        assert Gtk.Window.get_default_icon_name() == "io.github.leviagravia.GraphiumPlus"
        assert window.get_title() == "Untitled (Saved) — Graphium Plus"
        assert _paths_use(window, "graphium-plus")
        toolbar = window.toolbar
        assert isinstance(toolbar, Gtk.Toolbar)
        assert toolbar.get_style() == Gtk.ToolbarStyle.ICONS
        root_children = window._root_box.get_children()
        assert isinstance(root_children[0], Gtk.MenuBar)
        assert root_children[1] is toolbar
        expected = (
            ("new", "document-new"), ("open", "document-open"),
            ("save", "document-save"), None,
            ("undo", "edit-undo"), ("redo", "edit-redo"), None,
            ("cut", "edit-cut"), ("copy", "edit-copy"),
            ("paste", "edit-paste"), None,
            ("reload", "view-refresh"), ("find", "edit-find"),
            ("replace", "edit-find-replace"),
        )
        items = toolbar.get_children()
        assert len(items) == len(expected) + 2
        command_items = items[:len(expected)]
        assert isinstance(items[-2], Gtk.SeparatorToolItem)
        assert items[-1] is window.workspace_toggle
        buttons = {}
        for widget, wanted in zip(command_items, expected):
            if wanted is None:
                assert isinstance(widget, Gtk.SeparatorToolItem)
                continue
            action, icon_name = wanted
            assert isinstance(widget, Gtk.ToolButton)
            assert widget.get_action_name() == f"win.{action}"
            assert widget.get_icon_name() == icon_name
            canonical = window.lookup_action(action)
            assert canonical is not None
            actionable = widget.get_child()
            assert isinstance(actionable, Gtk.Button)
            assert actionable.get_sensitive() == canonical.get_enabled()
            buttons[action] = actionable
        save = window.lookup_action("save")
        assert save is not None
        save.set_enabled(False); drain(Gtk); assert not buttons["save"].get_sensitive()
        save.set_enabled(True); drain(Gtk); assert buttons["save"].get_sensitive()

        toolbar_visible = window.lookup_action("toolbar-visible")
        assert toolbar_visible is not None and toolbar_visible.get_state().get_boolean()
        toolbar_visible.activate(None); drain(Gtk)
        assert not toolbar.get_visible()
        assert not toolbar_visible.get_state().get_boolean()
        toolbar_visible.activate(None); drain(Gtk)
        assert toolbar.get_visible()
        assert toolbar_visible.get_state().get_boolean()
        return 0
    finally:
        window.destroy(); drain(Gtk)


if __name__ == "__main__":
    raise SystemExit(main())
