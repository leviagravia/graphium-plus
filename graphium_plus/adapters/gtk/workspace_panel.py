"""GTK3 projection for the bounded Graphium Plus Workspace."""
from __future__ import annotations

from collections.abc import Callable
import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from graphium_plus.workspace.model import DirectoryListing, WorkspaceItem


COL_ICON = 0
COL_NAME = 1
COL_ITEM = 2
COL_PLACEHOLDER = 3


class WorkspacePanel:
    def __init__(
        self,
        *,
        on_open_folder: Callable[[], None],
        on_recent_requested: Callable[[], tuple[str, ...]],
        on_recent_selected: Callable[[str], None],
        on_refresh: Callable[[], None],
        on_reveal: Callable[[], None],
        on_locate_active: Callable[[], None],
        on_new_text_file: Callable[[], None],
        on_new_folder: Callable[[], None],
        on_rename: Callable[[], None],
        on_duplicate: Callable[[], None],
        on_trash: Callable[[], None],
        on_open_in_graphium: Callable[[WorkspaceItem], None],
        on_activate: Callable[[WorkspaceItem], None],
        on_expand: Callable[[WorkspaceItem], DirectoryListing | None],
        report_error: Callable[[str], None],
    ) -> None:
        self._on_recent_requested = on_recent_requested
        self._on_recent_selected = on_recent_selected
        self._on_open_in_graphium = on_open_in_graphium
        self._on_activate = on_activate
        self._on_expand = on_expand
        self._report_error = report_error

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.widget.set_border_width(6)

        title = Gtk.Label(label="Workspace")
        title.set_xalign(0.0)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_markup("<b>Workspace</b>")
        self.widget.pack_start(title, False, False, 0)

        navigation_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        navigation_actions.pack_start(
            self._action_button("folder-open-symbolic", "Open Workspace folder", on_open_folder),
            False, False, 0,
        )

        self.recent_button = Gtk.MenuButton(label="Recent")
        self.recent_menu = Gtk.Menu()
        self.recent_button.set_popup(self.recent_menu)
        self.recent_button.connect("button-press-event", self._prepare_recent_menu)
        navigation_actions.pack_start(self.recent_button, False, False, 0)
        for icon, tooltip, callback in (
            ("go-jump-symbolic", "Locate Active Document", on_locate_active),
            ("view-refresh-symbolic", "Refresh Workspace", on_refresh),
            ("folder-symbolic", "Reveal in File Manager", on_reveal),
        ):
            navigation_actions.pack_start(self._action_button(icon, tooltip, callback), False, False, 0)
        self.widget.pack_start(navigation_actions, False, False, 0)

        mutation_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        for icon, tooltip, callback in (
            ("document-new-symbolic", "New Text File", on_new_text_file),
            ("folder-new-symbolic", "New Folder", on_new_folder),
            ("document-edit-symbolic", "Rename Selected Item", on_rename),
            ("edit-copy-symbolic", "Duplicate Selected File", on_duplicate),
            ("user-trash-symbolic", "Move Selected Item to Trash", on_trash),
        ):
            mutation_actions.pack_start(self._action_button(icon, tooltip, callback), False, False, 0)
        self.widget.pack_start(mutation_actions, False, False, 0)

        self.root_label = Gtk.Label(label="No folder selected")
        self.root_label.set_xalign(0.0)
        self.root_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.root_label.set_max_width_chars(24)
        self.widget.pack_start(self.root_label, False, False, 0)

        self.store = Gtk.TreeStore(str, str, object, bool)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.set_headers_visible(False)
        self.tree.set_enable_search(True)
        self.tree.set_search_column(COL_NAME)
        self.tree.set_activate_on_single_click(False)
        selection = self.tree.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)

        icon = Gtk.CellRendererPixbuf()
        text = Gtk.CellRendererText()
        text.set_property("ellipsize", Pango.EllipsizeMode.MIDDLE)
        column = Gtk.TreeViewColumn("Workspace")
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        column.set_fixed_width(1)
        column.set_expand(True)
        column.pack_start(icon, False)
        column.add_attribute(icon, "icon-name", COL_ICON)
        column.pack_start(text, True)
        column.add_attribute(text, "text", COL_NAME)
        self.tree.append_column(column)
        self.tree.connect("row-activated", self._row_activated)
        self.tree.connect("row-expanded", self._row_expanded)
        self.tree.connect("button-press-event", self._tree_button_press)
        self.context_menu = self._build_context_menu(
            on_reveal=on_reveal,
            on_new_text_file=on_new_text_file,
            on_new_folder=on_new_folder,
            on_rename=on_rename,
            on_duplicate=on_duplicate,
            on_trash=on_trash,
        )

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.add(self.tree)
        self.widget.pack_start(scroll, True, True, 0)

        self.status = Gtk.Label(label="Choose one local folder.")
        self.status.set_xalign(0.0)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.widget.pack_start(self.status, False, False, 0)

    @staticmethod
    def _action_button(icon: str, tooltip: str, callback: Callable[[], None]) -> Gtk.Button:
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        button.set_tooltip_text(tooltip)
        button.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU))
        button.connect("clicked", lambda _button: callback())
        return button

    @staticmethod
    def _menu_item(label: str, callback: Callable[[], None]) -> Gtk.MenuItem:
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda _item: callback())
        return item

    def _build_context_menu(
        self,
        *,
        on_reveal: Callable[[], None],
        on_new_text_file: Callable[[], None],
        on_new_folder: Callable[[], None],
        on_rename: Callable[[], None],
        on_duplicate: Callable[[], None],
        on_trash: Callable[[], None],
    ) -> Gtk.Menu:
        menu = Gtk.Menu()
        self.context_open_in_graphium = self._menu_item(
            "Open with Graphium Plus", self._open_selected_in_graphium
        )
        menu.append(self.context_open_in_graphium)
        menu.append(self._menu_item("Reveal in File Manager", on_reveal))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(self._menu_item("New Text File", on_new_text_file))
        menu.append(self._menu_item("New Folder", on_new_folder))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(self._menu_item("Rename", on_rename))
        menu.append(self._menu_item("Duplicate", on_duplicate))
        menu.append(self._menu_item("Move to Trash", on_trash))
        menu.show_all()
        return menu

    def _open_selected_in_graphium(self) -> None:
        item = self.selected_item()
        if item is not None:
            self._on_open_in_graphium(item)

    def _tree_button_press(self, _tree, event) -> bool:
        if event.button != 3:
            return False
        hit = self.tree.get_path_at_pos(int(event.x), int(event.y))
        if hit is None:
            return False
        path = hit[0]
        self.tree.get_selection().select_path(path)
        item = self.selected_item()
        self.context_open_in_graphium.set_sensitive(
            bool(item is not None and item.text_document and not item.is_symlink)
        )
        self.context_menu.popup_at_pointer(event)
        return True

    def render_root(self, listing: DirectoryListing | None, *, restore_expanded: tuple[str, ...] = ()) -> None:
        self.store.clear()
        if listing is None:
            self.root_label.set_text("No folder selected")
            self.root_label.set_tooltip_text(None)
            self.status.set_text("Choose one local folder.")
            return
        display = os.path.basename(listing.root.rstrip(os.sep)) or listing.root
        self.root_label.set_text(display)
        self.root_label.set_tooltip_text(listing.root)
        self._append_items(None, listing.items)
        self._set_status(listing)
        for relative in sorted(restore_expanded, key=lambda value: (value.count(os.sep), value)):
            path = self.path_for_relative(relative)
            if path is not None:
                self.tree.expand_row(path, False)

    def expanded_paths(self) -> tuple[str, ...]:
        values: list[str] = []
        def collect(model, path, tree_iter, _data):
            item = model[tree_iter][COL_ITEM]
            if isinstance(item, WorkspaceItem) and item.is_directory and self.tree.row_expanded(path):
                values.append(item.relative_path)
            return False
        self.store.foreach(collect, None)
        return tuple(values)

    def selected_item(self) -> WorkspaceItem | None:
        model, tree_iter = self.tree.get_selection().get_selected()
        if tree_iter is None:
            return None
        item = model[tree_iter][COL_ITEM]
        return item if isinstance(item, WorkspaceItem) else None

    def select_relative_path(self, relative_path: str, *, parent_relative: str = "") -> bool:
        if parent_relative:
            parent_path = self.path_for_relative(parent_relative)
            if parent_path is not None:
                self.tree.expand_row(parent_path, False)
        path = self.path_for_relative(relative_path)
        if path is None:
            return False
        self.tree.get_selection().select_path(path)
        self.tree.scroll_to_cell(path, None, False, 0.0, 0.0)
        return True

    def locate_relative_path(self, relative_path: str) -> bool:
        if not isinstance(relative_path, str) or not relative_path or os.path.isabs(relative_path):
            return False
        normalized = os.path.normpath(relative_path)
        if normalized in ("", ".") or normalized == ".." or normalized.startswith(".." + os.sep):
            return False
        parts = normalized.split(os.sep)
        current = ""
        for part in parts[:-1]:
            current = os.path.join(current, part) if current else part
            path = self.path_for_relative(current)
            if path is None:
                return False
            if not self.tree.row_expanded(path):
                self.tree.expand_row(path, False)
        path = self.path_for_relative(normalized)
        if path is None:
            return False
        self.tree.get_selection().select_path(path)
        self.tree.scroll_to_cell(path, None, False, 0.0, 0.0)
        return True

    def path_for_relative(self, relative_path: str):
        found = None
        def find(model, path, tree_iter, _data):
            nonlocal found
            item = model[tree_iter][COL_ITEM]
            if isinstance(item, WorkspaceItem) and item.relative_path == relative_path:
                found = path.copy()
                return True
            return False
        self.store.foreach(find, None)
        return found

    def _append_items(self, parent, items: tuple[WorkspaceItem, ...]) -> None:
        for item in items:
            tree_iter = self.store.append(parent, [self._icon_for(item), item.name, item, False])
            if item.is_directory and not item.is_symlink:
                self.store.append(tree_iter, ["", "", None, True])

    def _row_activated(self, _tree, path, _column) -> None:
        tree_iter = self.store.get_iter(path)
        item = self.store[tree_iter][COL_ITEM]
        if not isinstance(item, WorkspaceItem):
            return
        if item.is_directory:
            if self.tree.row_expanded(path):
                self.tree.collapse_row(path)
            else:
                self.tree.expand_row(path, False)
            return
        if item.text_document:
            self._on_open_in_graphium(item)
            return
        self._on_activate(item)

    def _row_expanded(self, _tree, tree_iter, _path) -> None:
        item = self.store[tree_iter][COL_ITEM]
        if not isinstance(item, WorkspaceItem) or not item.is_directory or item.is_symlink:
            return
        if not self._has_placeholder(tree_iter):
            return
        try:
            listing = self._on_expand(item)
        except Exception as exc:
            self._report_error(str(exc))
            return
        if listing is None:
            return
        self._materialize_placeholder(tree_iter, listing.items)
        self._set_status(listing)

    def _has_placeholder(self, parent) -> bool:
        child = self.store.iter_children(parent)
        return child is not None and bool(self.store[child][COL_PLACEHOLDER])

    def _materialize_placeholder(self, parent, items: tuple[WorkspaceItem, ...]) -> None:
        placeholder = self.store.iter_children(parent)
        if placeholder is None or not bool(self.store[placeholder][COL_PLACEHOLDER]):
            return
        if not items:
            self.store.remove(placeholder)
            return

        first = items[0]
        self.store.set_value(placeholder, COL_ICON, self._icon_for(first))
        self.store.set_value(placeholder, COL_NAME, first.name)
        self.store.set_value(placeholder, COL_ITEM, first)
        self.store.set_value(placeholder, COL_PLACEHOLDER, False)
        if first.is_directory and not first.is_symlink:
            self.store.append(placeholder, ["", "", None, True])
        self._append_items(parent, items[1:])

    def _set_status(self, listing: DirectoryListing) -> None:
        if listing.diagnostics:
            self.status.set_text(f"Partial view — {listing.diagnostics[0]}")
            self.status.set_tooltip_text("\n".join(listing.diagnostics))
            return
        self.status.set_text("")
        self.status.set_tooltip_text(None)

    def _prepare_recent_menu(self, *_args) -> bool:
        for child in self.recent_menu.get_children():
            self.recent_menu.remove(child)
        roots = self._on_recent_requested()
        if not roots:
            empty = Gtk.MenuItem(label="No recent folders")
            empty.set_sensitive(False)
            self.recent_menu.append(empty)
        else:
            for root in roots:
                label = os.path.basename(root.rstrip(os.sep)) or root
                item = Gtk.MenuItem(label=label)
                item.set_tooltip_text(root)
                item.connect("activate", lambda _item, value=root: self._on_recent_selected(value))
                self.recent_menu.append(item)
        self.recent_menu.show_all()
        return False

    @staticmethod
    def _icon_for(item: WorkspaceItem) -> str:
        if item.is_symlink:
            return "emblem-symbolic-link"
        if item.is_directory:
            return "folder-symbolic"
        if item.text_document:
            return "text-x-generic-symbolic"
        return "document-open-symbolic"
