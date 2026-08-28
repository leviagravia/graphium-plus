"""Graphium Plus window: Core editor, compact toolbar and bounded Workspace."""
from __future__ import annotations

import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk

from graphium.adapters.gtk.window import GraphiumWindow
from graphium.adapters.gtk.dialogs import show_text_document
from graphium.application.commands import COMMANDS
from graphium_plus.product import PLUS_PRODUCT_IDENTITY
from graphium_plus.workspace.controller import WorkspaceController
from graphium_plus.workspace.model import WorkspaceItem
from graphium_plus.workspace.operations import plan_new_folder, plan_new_text_file
from graphium_plus.workspace.gio import WorkspaceGioAdapter
from graphium_plus.workspace.state import RecentWorkspaces
from .workspace_panel import WorkspacePanel


_TOOLBAR_LAYOUT = (
    ("new", "document-new"),
    ("open", "document-open"),
    ("save", "document-save"),
    None,
    ("undo", "edit-undo"),
    ("redo", "edit-redo"),
    None,
    ("cut", "edit-cut"),
    ("copy", "edit-copy"),
    ("paste", "edit-paste"),
    None,
    ("reload", "view-refresh"),
    ("find", "edit-find"),
    ("replace", "edit-find-replace"),
)
_COMMANDS = {spec.action: spec for spec in COMMANDS}
_DEFAULT_WORKSPACE_PANE_WIDTH = 260


class GraphiumPlusWindow(GraphiumWindow):
    def __init__(self, application: Gtk.Application) -> None:
        super().__init__(application, identity=PLUS_PRODUCT_IDENTITY)
        self.toolbar = self._build_toolbar()
        self._root_box.pack_start(self.toolbar, False, False, 0)
        self._root_box.reorder_child(self.toolbar, 1)
        self._install_toolbar_visibility_control()

        self.workspace = WorkspaceController()
        self.workspace_gio = WorkspaceGioAdapter()
        self.recent_workspaces = RecentWorkspaces(self._xdg_paths.state / "recent-workspaces.json")
        self.workspace_panel = WorkspacePanel(
            on_open_folder=self._choose_workspace_root,
            on_recent_requested=self.recent_workspaces.paths,
            on_recent_selected=self._open_workspace_root,
            on_refresh=self._refresh_workspace,
            on_reveal=self._reveal_workspace,
            on_locate_active=self._locate_active_document,
            on_new_text_file=self._new_workspace_text_file,
            on_new_folder=self._new_workspace_folder,
            on_rename=self._rename_workspace_item,
            on_duplicate=self._duplicate_workspace_item,
            on_trash=self._trash_workspace_item,
            on_open_in_graphium=self._open_workspace_text_item,
            on_activate=self._activate_workspace_item,
            on_expand=self.workspace.load_directory,
            report_error=self._report_workspace_error,
        )
        self.workspace_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.workspace_paned.pack1(self.workspace_panel.widget, resize=False, shrink=False)
        self._root_box.remove(self._editor_scroller)
        self.workspace_paned.pack2(self._editor_scroller, resize=True, shrink=False)
        self.workspace_paned.set_position(_DEFAULT_WORKSPACE_PANE_WIDTH)
        self._root_box.pack_start(self.workspace_paned, True, True, 0)
        self.workspace_toggle = self._build_workspace_toggle()
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.workspace_toggle, -1)

    def _build_workspace_toggle(self) -> Gtk.ToggleToolButton:
        button = Gtk.ToggleToolButton()
        button.set_label("Workspace")
        button.set_icon_name("folder-symbolic")
        button.set_tooltip_text("Show or hide Workspace")
        button.set_active(True)
        button.connect("toggled", self._on_workspace_visibility_toggled)
        return button

    def _on_workspace_visibility_toggled(self, button: Gtk.ToggleToolButton) -> None:
        visible = bool(button.get_active())
        self.workspace_panel.widget.set_no_show_all(not visible)
        if visible:
            self.workspace_panel.widget.show_all()
        else:
            self.workspace_panel.widget.hide()

    def _install_toolbar_visibility_control(self) -> None:
        action = Gio.SimpleAction.new_stateful(
            "toolbar-visible", None, GLib.Variant.new_boolean(True)
        )
        action.connect("activate", self._action_toolbar_visible)
        self.add_action(action)
        self._actions["toolbar-visible"] = action

        menubar = next(
            (child for child in self._root_box.get_children() if isinstance(child, Gtk.MenuBar)),
            None,
        )
        if menubar is None:
            raise RuntimeError("Graphium Plus View menu is unavailable")
        view_item = next(
            (item for item in menubar.get_children() if item.get_label() == "View"),
            None,
        )
        if view_item is None or view_item.get_submenu() is None:
            raise RuntimeError("Graphium Plus View submenu is unavailable")
        menu_item = Gtk.CheckMenuItem(label="Toolbar")
        menu_item.set_action_name("win.toolbar-visible")
        view_item.get_submenu().append(menu_item)
        menu_item.show()

    def _action_toolbar_visible(self, action: Gio.SimpleAction, _parameter) -> None:
        state = action.get_state()
        visible = not bool(state.get_boolean())
        action.set_state(GLib.Variant.new_boolean(visible))
        self.toolbar.set_no_show_all(not visible)
        if visible:
            self.toolbar.show_all()
        else:
            self.toolbar.hide()

    @staticmethod
    def _build_toolbar() -> Gtk.Toolbar:
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        for item in _TOOLBAR_LAYOUT:
            if item is None:
                toolbar.insert(Gtk.SeparatorToolItem(), -1)
                continue
            action, icon_name = item
            spec = _COMMANDS[action]
            button = Gtk.ToolButton()
            button.set_label(spec.label)
            button.set_icon_name(icon_name)
            button.set_tooltip_text(spec.label)
            button.set_action_name(f"win.{action}")
            toolbar.insert(button, -1)
        return toolbar

    def _choose_workspace_root(self) -> None:
        dialog = Gtk.FileChooserNative.new(
            "Open Workspace Folder",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            "Open",
            "Cancel",
        )
        try:
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                path = dialog.get_filename()
                if path:
                    self._open_workspace_root(path)
        finally:
            dialog.destroy()

    def _open_workspace_root(self, path: str) -> None:
        try:
            listing = self.workspace.bind_root(path)
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return
        self.workspace_panel.render_root(listing)
        try:
            self.recent_workspaces.touch(listing.root)
        except Exception as exc:
            self._report_workspace_error(f"Workspace opened, but Recent Workspaces could not be saved: {exc}")

    def _refresh_workspace(self) -> None:
        expanded = self.workspace_panel.expanded_paths()
        selected = self.workspace_panel.selected_item()
        selected_relative = selected.relative_path if selected is not None else None
        try:
            listing = self.workspace.refresh()
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return
        self.workspace_panel.render_root(listing, restore_expanded=expanded)
        if selected_relative:
            self.workspace_panel.select_relative_path(selected_relative)

    def _locate_active_document(self) -> bool:
        try:
            relative = self.workspace.relative_path_for_document(
                self._active_document_physical_path()
            )
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return False
        if not self.workspace_toggle.get_active():
            self.workspace_toggle.set_active(True)
        if self.workspace_panel.locate_relative_path(relative):
            return True
        self._report_workspace_error("The active document is not currently visible in Workspace.")
        return False

    def _creation_destination(self) -> str | None:
        try:
            return self.workspace.creation_parent(self.workspace_panel.selected_item())
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return None

    def _prompt_workspace_creation(
        self,
        *,
        title: str,
        action_label: str,
        destination: str,
        name_label: str,
        placeholder: str = "",
        choose_text_format: bool = False,
    ) -> tuple[str, str | None] | None:
        dialog = Gtk.Dialog(title=title, transient_for=self, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, action_label, Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)
        location = Gtk.Label(label=f"Create inside: {destination}")
        location.set_xalign(0.0)
        box.pack_start(location, False, False, 0)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        entry.set_activates_default(True)
        row.pack_start(Gtk.Label(label=name_label), False, False, 0)
        row.pack_start(entry, True, True, 0)
        box.pack_start(row, False, False, 0)
        formats = None
        if choose_text_format:
            formats = Gtk.ComboBoxText()
            formats.append(".txt", "Plain text (.txt)")
            formats.append(".md", "Markdown (.md)")
            formats.set_active_id(".txt")
            format_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            format_row.pack_start(Gtk.Label(label="Format:"), False, False, 0)
            format_row.pack_start(formats, False, False, 0)
            box.pack_start(format_row, False, False, 0)
        ok = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        ok.set_sensitive(False)
        entry.connect("changed", lambda widget: ok.set_sensitive(bool(widget.get_text().strip())))
        dialog.show_all()
        entry.grab_focus()
        try:
            if dialog.run() != Gtk.ResponseType.OK:
                return None
            suffix = formats.get_active_id() if formats is not None else None
            return entry.get_text(), suffix
        finally:
            dialog.destroy()

    def _prompt_new_text_file(self, destination: str) -> tuple[str, str] | None:
        result = self._prompt_workspace_creation(
            title="New Text File",
            action_label="Create and Open",
            destination=destination,
            name_label="File name:",
            placeholder="Chapter_1",
            choose_text_format=True,
        )
        return None if result is None else (result[0], result[1] or ".txt")

    def _prompt_new_folder(self, destination: str) -> str | None:
        result = self._prompt_workspace_creation(
            title="New Folder",
            action_label="Create Folder",
            destination=destination,
            name_label="Folder name:",
        )
        return None if result is None else result[0]

    def _refresh_workspace_after_mutation(self, target_path: str, parent_path: str) -> None:
        expanded = self.workspace_panel.expanded_paths()
        try:
            listing = self.workspace.refresh()
        except Exception as exc:
            self._report_workspace_error(f"The item was created, but Workspace could not refresh: {exc}")
            return
        self.workspace_panel.render_root(listing, restore_expanded=expanded)
        relative = os.path.relpath(target_path, listing.root)
        parent_relative = os.path.relpath(parent_path, listing.root)
        if parent_relative == ".":
            parent_relative = ""
        self.workspace_panel.select_relative_path(relative, parent_relative=parent_relative)

    def _refresh_workspace_after_removal(self, parent_path: str) -> None:
        expanded = self.workspace_panel.expanded_paths()
        try:
            listing = self.workspace.refresh()
        except Exception as exc:
            self._report_workspace_error(f"The item was moved to Trash, but Workspace could not refresh: {exc}")
            return
        self.workspace_panel.render_root(listing, restore_expanded=expanded)
        parent_relative = os.path.relpath(parent_path, listing.root)
        if parent_relative == ".":
            self.workspace_panel.tree.get_selection().unselect_all()
            return
        grandparent = os.path.dirname(parent_relative)
        if grandparent == ".":
            grandparent = ""
        self.workspace_panel.select_relative_path(parent_relative, parent_relative=grandparent)

    def _new_workspace_text_file(self) -> None:
        parent = self._creation_destination()
        if parent is None:
            return
        request = self._prompt_new_text_file(parent)
        if request is not None:
            self.create_workspace_text_file(request[0], request[1], parent_path=parent)

    def _resume_after_aborted_workspace_open(self) -> None:
        self._schedule_external_monitor_bind()
        self._refresh_projection()
        self.text_view.grab_focus()

    def create_workspace_text_file(self, name: str, suffix: str = ".txt", *, parent_path: str | None = None) -> bool:
        parent = self._creation_destination() if parent_path is None else parent_path
        if parent is None:
            return False
        try:
            plan = plan_new_text_file(self.workspace.root, parent, name, suffix=suffix)
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return False

        self._suspend_external_monitor()
        permit = self.core.lifecycle.prepare_document_replacement("open a new Workspace text file")
        if permit is None:
            self._resume_after_aborted_workspace_open()
            return False
        try:
            result = self.workspace_gio.create(plan)
        except Exception as exc:
            self._report_workspace_error(f"The text file could not be created: {exc}")
            self._resume_after_aborted_workspace_open()
            return False
        if not result.success:
            if result.committed:
                self._refresh_workspace_after_mutation(result.path, plan.parent_path)
            self._report_workspace_error(result.message or "The text file could not be created.")
            self._resume_after_aborted_workspace_open()
            return False

        self._refresh_workspace_after_mutation(result.path, plan.parent_path)
        opened = self.open_path(result.path, replacement_permit=permit)
        if not opened:
            self._report_workspace_error("The text file was created, but it could not be opened in Graphium Plus.")
        return opened

    def _new_workspace_folder(self) -> None:
        parent = self._creation_destination()
        if parent is None:
            return
        name = self._prompt_new_folder(parent)
        if name is not None:
            self.create_workspace_folder(name, parent_path=parent)

    def create_workspace_folder(self, name: str, *, parent_path: str | None = None) -> bool:
        parent = self._creation_destination() if parent_path is None else parent_path
        if parent is None:
            return False
        try:
            plan = plan_new_folder(self.workspace.root, parent, name)
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return False
        try:
            result = self.workspace_gio.create(plan)
        except Exception as exc:
            self._report_workspace_error(f"The folder could not be created: {exc}")
            return False
        if not result.success:
            if result.committed:
                self._refresh_workspace_after_mutation(result.path, plan.parent_path)
            self._report_workspace_error(result.message or "The folder could not be created.")
            return False
        self._refresh_workspace_after_mutation(result.path, plan.parent_path)
        return True

    def _prompt_workspace_rename(self, item: WorkspaceItem) -> str | None:
        dialog = Gtk.Dialog(title="Rename Workspace Item", transient_for=self, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Rename", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        entry = Gtk.Entry()
        entry.set_text(item.name)
        entry.select_region(0, -1)
        entry.set_activates_default(True)
        row.pack_start(Gtk.Label(label="New name:"), False, False, 0)
        row.pack_start(entry, True, True, 0)
        box.pack_start(row, False, False, 0)
        ok = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        entry.connect("changed", lambda widget: ok.set_sensitive(bool(widget.get_text().strip())))
        dialog.show_all()
        entry.grab_focus()
        try:
            return entry.get_text() if dialog.run() == Gtk.ResponseType.OK else None
        finally:
            dialog.destroy()

    def _active_document_physical_path(self) -> str | None:
        state = self.core.session.file_state
        if state is not None and state.binding.canonical_path:
            return state.binding.canonical_path
        return self.core.session.logical_path

    def _rename_workspace_item(self) -> None:
        selected = self.workspace_panel.selected_item()
        if selected is None:
            self._report_workspace_error("Select one Workspace file or folder to rename.")
            return
        name = self._prompt_workspace_rename(selected)
        if name is not None:
            self.rename_workspace_item(name)

    def rename_workspace_item(self, name: str) -> bool:
        selected = self.workspace_panel.selected_item()
        try:
            plan = self.workspace.plan_rename(
                selected, name, active_document_path=self._active_document_physical_path()
            )
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return False
        try:
            result = self.workspace_gio.rename(plan)
        except Exception as exc:
            self._report_workspace_error(f"The selected item could not be renamed: {exc}")
            return False
        if not result.success:
            if result.committed:
                self._refresh_workspace_after_mutation(result.path, plan.parent_path)
            self._report_workspace_error(result.message or "The selected item could not be renamed.")
            return False
        self._refresh_workspace_after_mutation(result.path, plan.parent_path)
        return True

    def _duplicate_workspace_item(self) -> None:
        self.duplicate_workspace_item()

    def duplicate_workspace_item(self) -> bool:
        selected = self.workspace_panel.selected_item()
        try:
            plan = self.workspace.plan_duplicate(selected)
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return False
        try:
            result = self.workspace_gio.duplicate(plan)
        except Exception as exc:
            self._report_workspace_error(f"The selected file could not be duplicated: {exc}")
            return False
        if not result.success:
            if result.committed:
                self._refresh_workspace_after_mutation(result.path, plan.parent_path)
            self._report_workspace_error(result.message or "The selected file could not be duplicated.")
            return False
        self._refresh_workspace_after_mutation(result.path, plan.parent_path)
        if result.message:
            self.workspace_panel.status.set_text(result.message)
        return True

    def _confirm_workspace_trash(self, plan) -> bool:
        kind = "folder" if plan.source_is_directory else "file"
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Move “{plan.source_name}” to Trash?",
        )
        dialog.format_secondary_text(
            f"This {kind} will be moved to the system Trash. "
            "Graphium Plus will not permanently delete it as a fallback."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Move to Trash", Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        try:
            return dialog.run() == Gtk.ResponseType.ACCEPT
        finally:
            dialog.destroy()

    def _trash_workspace_item(self) -> None:
        selected = self.workspace_panel.selected_item()
        try:
            plan = self.workspace.plan_trash(
                selected, active_document_path=self._active_document_physical_path()
            )
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return
        if not self._confirm_workspace_trash(plan):
            return
        try:
            result = self.workspace_gio.trash(plan)
        except Exception as exc:
            self._report_workspace_error(f"The selected item could not be moved to Trash: {exc}")
            return
        if result.accepted:
            self._refresh_workspace_after_removal(plan.parent_path)
        if not result.success:
            self._report_workspace_error(result.message or "The selected item could not be moved to Trash.")

    def _open_workspace_text_item(self, item: WorkspaceItem) -> None:
        """Open one current Workspace text item through Graphium's canonical lifecycle."""
        try:
            activation = self.workspace.activation_for(item)
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return
        if activation.kind in ("blocked", "missing"):
            self._report_workspace_error(activation.message)
            return
        if activation.kind != "internal":
            self._report_workspace_error("Only .txt and .md Workspace files open in Graphium Plus.")
            return
        self.open_path(activation.path)

    def _activate_workspace_item(self, item: WorkspaceItem) -> None:
        try:
            activation = self.workspace.activation_for(item)
        except Exception as exc:
            self._report_workspace_error(str(exc))
            return
        if activation.kind in ("blocked", "missing"):
            self._report_workspace_error(activation.message)
            return
        if activation.kind == "internal":
            self.open_path(activation.path)
            return
        if activation.kind == "external":
            try:
                Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(activation.path).get_uri(), None)
            except Exception as exc:
                self._report_workspace_error(f"Could not open the selected file: {exc}")

    @staticmethod
    def _file_manager_request(method: str, target_path: str) -> None:
        uri = Gio.File.new_for_path(target_path).get_uri()
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        connection.call_sync(
            "org.freedesktop.FileManager1",
            "/org/freedesktop/FileManager1",
            "org.freedesktop.FileManager1",
            method,
            GLib.Variant("(ass)", ([uri], "")),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _reveal_workspace(self) -> None:
        selected = self.workspace_panel.selected_item()
        target = selected.path if selected is not None else self.workspace.root
        if not target:
            self._report_workspace_error("No Workspace folder is selected.")
            return
        method = "ShowItems" if selected is not None else "ShowFolders"
        try:
            self._file_manager_request(method, target)
            return
        except Exception:
            pass

        # FileManager1 is optional. Fall back to opening the containing directory,
        # without pretending that the selected item can still be highlighted.
        directory = (
            target
            if selected is None or (os.path.isdir(target) and not os.path.islink(target))
            else os.path.dirname(target)
        )
        try:
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(directory).get_uri(), None)
        except Exception as exc:
            self._report_workspace_error(f"Could not reveal the Workspace location: {exc}")


    def _action_user_guide(self, *_args) -> None:
        show_text_document(
            self,
            title="Graphium Plus User Guide",
            path=self._help_path("GRAPHIUM_PLUS_USER_GUIDE.txt"),
        )

    def _action_keyboard_shortcuts(self, *_args) -> None:
        show_text_document(
            self,
            title="Graphium Plus Keyboard Shortcuts",
            path=self._help_path("GRAPHIUM_KEYBOARD_SHORTCUTS.txt"),
        )

    def _report_workspace_error(self, message: str) -> None:
        self._ui.show_warning("Workspace", message)
