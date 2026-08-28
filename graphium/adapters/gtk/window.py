"""Thin GTK3 single-document editor window for Graphium."""
from __future__ import annotations

import os
import time
from pathlib import Path

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gio, GLib, GObject, Gtk

from graphium.application.commands import (COMMANDS, TOP_LEVEL_MENUS, command_availability, encoding_choice_target, encoding_choice_value, line_ending_choice_target)
from graphium.application.document_properties import CheckNowResult, CheckNowStatus
from graphium.application.file_lifecycle import DocumentReplacementPermit
from graphium.application.view_status import project_compact_status
from graphium.application.view_settings import (
    APPEARANCE_DARK, APPEARANCE_LIGHT, APPEARANCE_SYSTEM, APPEARANCE_VALUES,
    MAX_WINDOW_HEIGHT, MAX_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, MIN_WINDOW_WIDTH,
)
from graphium.application.text_statistics import count_text_statistics
from graphium.application.recovery_startup import RecoveryStartupCoordinator, RecoveryStartupResult, RecoveryStartupStatus
from graphium.application.text_transform import build_transformation_plan
from graphium.application.print_model import build_print_snapshot
from graphium.domain.document_serialization import (
    DocumentSerializationProfile, MixedLineEndingConfirmationRequired,
)
from graphium.domain.document_save import SaveDisposition
from graphium.domain.text_search import SearchInputError, SearchMatch
from graphium.composition import build_core
from graphium.paths import XdgPaths, resolve_xdg_paths
from graphium.domain.edit_history import ViewState
from graphium.application.renderability import (
    InteractiveRenderabilityError,
    ensure_insert_renderable,
    ensure_join_renderable,
)
from graphium.product import CORE_PRODUCT_IDENTITY, ProductIdentity
from .dialogs import (
    GtkLifecycleUI, choose_copy_path, choose_font, choose_line_number, choose_tab_width, show_about,
    show_properties, show_statistics, show_text_document,
)
from .editor_buffer import GtkTextBufferPort
from .editor_view import GraphiumTextView
from .external_monitor import StrongExternalFileMonitor
from .recovery_runtime import GLibRecoveryScheduler


class GraphiumWindow(Gtk.ApplicationWindow):
    def __init__(
        self,
        application: Gtk.Application,
        *,
        identity: ProductIdentity = CORE_PRODUCT_IDENTITY,
        xdg_paths: XdgPaths | None = None,
    ) -> None:
        super().__init__(application=application)
        self._identity = identity
        self._xdg_paths = (
            resolve_xdg_paths(namespace=identity.xdg_namespace)
            if xdg_paths is None
            else xdg_paths
        )
        self.set_role(f"{identity.package_name}-editor")

        self._closing_accepted = False
        self._startup_open_pending = False
        self._startup_recovery_checked = False
        self._mapped = False
        self._benchmark_ready_emitted = False
        self._implicit_delete_group = False
        self._renderability_notice_pending = False
        self._normal_window_size = (720, 520)
        self._window_maximized = False
        self._window_fullscreen = False
        self._window_size_persisted = False
        self._system_prefer_dark_theme = bool(
            getattr(application, "system_prefer_dark_theme", False)
        )
        self._appearance_renderer = None
        self._external_monitor_bind_source_id = 0
        self._actions: dict[str, Gio.SimpleAction] = {}
        self._print_controller = None
        self._search_bar: Gtk.SearchBar | None = None
        self._search_query_entry: Gtk.Entry | None = None
        self._search_replace_entry: Gtk.Entry | None = None
        self._search_replace_row: Gtk.Widget | None = None
        self._search_match_case: Gtk.CheckButton | None = None
        self._search_status: Gtk.Label | None = None
        self._recent_menu = Gio.Menu()
        self._status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._status_bar.set_border_width(4)
        self._status_position = Gtk.Label(label="Ln 1, Col 1")
        self._status_position.set_xalign(0.0)
        self._status_document = Gtk.Label(label="UTF-8 · LF · Saved")
        self._status_document.set_xalign(1.0)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._root_box = box
        self.add(box)

        self._external_info_bar = Gtk.InfoBar()
        self._external_info_bar.set_no_show_all(True)
        self._external_info_bar.set_message_type(Gtk.MessageType.WARNING)
        self._external_info_label = Gtk.Label(label="")
        self._external_info_label.set_xalign(0.0)
        self._external_info_label.set_line_wrap(True)
        self._external_info_bar.get_content_area().pack_start(
            self._external_info_label, True, True, 0
        )
        self._external_info_reload_button = self._external_info_bar.add_button(
            "Reload from Disk", Gtk.ResponseType.APPLY
        )
        self._external_info_bar.connect("response", self._on_external_info_response)
        box.pack_start(self._external_info_bar, False, False, 0)
        self._external_info_bar.hide()

        self.text_view = GraphiumTextView()
        self.buffer = self.text_view.get_buffer()
        self.buffer_port = GtkTextBufferPort(self.buffer)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.add(self.text_view)
        self._editor_scroller = scroller
        box.pack_start(scroller, True, True, 0)

        self._status_bar.pack_start(self._status_position, False, False, 4)
        self._status_bar.pack_end(self._status_document, False, False, 4)
        box.pack_end(self._status_bar, False, False, 0)

        ui = GtkLifecycleUI(self)
        self._ui = ui
        self.core = build_core(
            buffer=self.buffer_port,
            ui=ui,
            recovery_scheduler=GLibRecoveryScheduler(),
            xdg_paths=self._xdg_paths,
        )
        if self.core.recovery is None:
            raise RuntimeError("Graphium recovery controller was not composed")
        self._startup_recovery = RecoveryStartupCoordinator(
            store=self.core.recovery.store,
            editor=self.core.editor,
            recovery=self.core.recovery,
            ui=ui,
        )
        self._external_file_monitor = StrongExternalFileMonitor(
            session=self.core.session, on_result=self._on_external_observation_result
        )
        self.core.editor.initialize_new_text("", clean=True)
        initial_settings = self.core.view_settings.current
        self._normal_window_size = (initial_settings.window_width, initial_settings.window_height)
        self.set_default_size(*self._normal_window_size)
        self._apply_initial_view_settings()
        if initial_settings.appearance != APPEARANCE_SYSTEM:
            self._apply_appearance(initial_settings.appearance)

        self._install_actions()
        self._install_menu()
        self._connect_native_edit_signals()
        self.buffer.connect("notify::has-selection", self._on_selection_changed)
        self.buffer.connect("notify::cursor-position", self._on_cursor_position_changed)
        self.connect("delete-event", self._on_delete_event)
        self.connect("destroy", self._on_destroy_appearance)
        self.connect("map-event", self._on_mapped)
        self.connect("window-state-event", self._on_window_state_event)
        self.connect("configure-event", self._on_configure_event)
        self._install_file_drop_target()
        self._refresh_projection()

    def _on_destroy_appearance(self, *_args) -> None:
        self._cancel_external_monitor_bind()
        self._external_file_monitor.close()
        if self.core.recovery is not None:
            self.core.recovery.close()
        if self._appearance_renderer is not None:
            self._appearance_renderer.close()

    def _cancel_external_monitor_bind(self) -> None:
        source_id = int(self._external_monitor_bind_source_id)
        self._external_monitor_bind_source_id = 0
        if source_id:
            try:
                GLib.source_remove(source_id)
            except Exception:
                pass

    def _suspend_external_monitor(self) -> None:
        self._cancel_external_monitor_bind()
        self._external_file_monitor.suspend()

    def _schedule_external_monitor_bind(self, delay_ms: int = 80) -> None:
        self._cancel_external_monitor_bind()
        self._external_monitor_bind_source_id = GLib.timeout_add(
            int(delay_ms), self._bind_external_monitor
        )

    def _bind_external_monitor(self) -> bool:
        self._external_monitor_bind_source_id = 0
        self._external_file_monitor.bind_current()
        return False

    def _clear_external_file_alert(self) -> None:
        self._external_info_label.set_text("")
        self._external_info_bar.set_no_show_all(True)
        self._external_info_bar.hide()

    def _on_external_observation_result(self, result: CheckNowResult) -> None:
        if result.status is CheckNowStatus.UNCHANGED:
            self._clear_external_file_alert()
            return
        messages = {
            CheckNowStatus.CONTENT_CHANGED: "File changed on disk.",
            CheckNowStatus.METADATA_CHANGED: "File metadata changed on disk.",
            CheckNowStatus.REPLACED_OR_RETARGETED:
                "File was replaced or this path now refers to a different file.",
            CheckNowStatus.MISSING: "File no longer exists on disk.",
            CheckNowStatus.UNAVAILABLE_OR_UNSTABLE:
                "Graphium could not reliably verify the file on disk.",
        }
        self._external_info_label.set_text(messages.get(result.status, result.detail or "File state changed."))
        self._external_info_bar.set_message_type(
            Gtk.MessageType.INFO
            if result.status is CheckNowStatus.METADATA_CHANGED
            else Gtk.MessageType.WARNING
        )
        can_reload = result.status in (
            CheckNowStatus.CONTENT_CHANGED, CheckNowStatus.REPLACED_OR_RETARGETED
        )
        self._external_info_bar.set_no_show_all(False)
        self._external_info_bar.show_all()
        self._external_info_reload_button.set_visible(can_reload)

    def _on_external_info_response(self, _bar, response_id) -> None:
        if response_id == Gtk.ResponseType.APPLY:
            self._actions["reload"].activate(None)

    def _install_actions(self) -> None:
        callbacks = {
            "new": self._action_new,
            "open": self._action_open,
            "open-recent": self._action_open_recent,
            "clear-recent": self._action_clear_recent,
            "save": self._action_save,
            "save-as": self._action_save_as,
            "save-copy": self._action_save_copy,
            "save-version-copy": self._action_save_version_copy,
            "reload": self._action_reload,
            "properties": self._action_properties,
            "page-setup": self._action_page_setup,
            "print-preview": self._action_print_preview,
            "print": self._action_print,
            "quit": self._action_quit,
            "undo": self._action_undo,
            "redo": self._action_redo,
            "cut": self._action_cut,
            "copy": self._action_copy,
            "paste": self._action_paste,
            "delete": self._action_delete,
            "select-all": self._action_select_all,
            "tab-width": self._action_tab_width,
            "insert-spaces": self._action_insert_spaces,
            "uppercase": self._action_uppercase,
            "lowercase": self._action_lowercase,
            "duplicate-line-selection": self._action_duplicate_line_selection,
            "move-lines-up": self._action_move_lines_up,
            "move-lines-down": self._action_move_lines_down,
            "trim-trailing-spaces": self._action_trim_trailing_spaces,
            "find": self._action_find,
            "find-next": self._action_find_next,
            "find-previous": self._action_find_previous,
            "replace": self._action_replace,
            "go-to-line": self._action_go_to_line,
            "status-bar": self._action_status_bar,
            "line-numbers": self._action_line_numbers,
            "word-wrap": self._action_word_wrap,
            "appearance": self._action_appearance,
            "font": self._action_font,
            "zoom-in": self._action_zoom_in,
            "zoom-out": self._action_zoom_out,
            "zoom-reset": self._action_zoom_reset,
            "full-screen": self._action_full_screen,
            "encoding": self._action_encoding,
            "line-endings": self._action_line_endings,
            "check-spelling": self._action_check_spelling,
            "statistics": self._action_statistics,
            "user-guide": self._action_user_guide,
            "keyboard-shortcuts": self._action_keyboard_shortcuts,
            "about": self._action_about,
        }
        for spec in COMMANDS:
            if spec.action == "open-recent":
                action = Gio.SimpleAction.new(spec.action, GLib.VariantType.new("s"))
            elif spec.choices:
                action = Gio.SimpleAction.new_stateful(
                    spec.action,
                    GLib.VariantType.new("s"),
                    GLib.Variant.new_string(self._initial_choice_state(spec.action)),
                )
            elif spec.stateful:
                action = Gio.SimpleAction.new_stateful(
                    spec.action, None, GLib.Variant.new_boolean(self._initial_action_state(spec.action))
                )
            else:
                action = Gio.SimpleAction.new(spec.action, None)
            action.connect("activate", callbacks[spec.action])
            self.add_action(action)
            self._actions[spec.action] = action

    def _initial_choice_state(self, action: str) -> str:
        if action == "appearance":
            return self.core.view_settings.current.appearance
        if action == "tab-width":
            width = self.core.view_settings.current.tab_width
            return str(width) if width in (2, 3, 4, 8) else "other"
        profile = self.core.session.current_representation_profile
        if action == "encoding":
            return encoding_choice_value(profile)
        if action == "line-endings":
            return profile.line_ending.value
        raise KeyError(action)

    def _initial_action_state(self, action: str) -> bool:
        settings = self.core.view_settings.current
        return {
            "status-bar": settings.status_bar,
            "line-numbers": settings.line_numbers,
            "word-wrap": settings.word_wrap,
            "full-screen": False,
            "insert-spaces": settings.insert_spaces,
        }[action]

    def _install_menu(self) -> None:
        root = Gio.Menu()
        for menu_name in TOP_LEVEL_MENUS:
            section = Gio.Menu()
            for spec in COMMANDS:
                if spec.menu != menu_name or spec.submenu is not None:
                    continue
                if spec.action == "open-recent":
                    section.append_submenu(spec.label, self._recent_menu)
                elif spec.choices:
                    choices_menu = Gio.Menu()
                    for choice_label, choice_value in spec.choices:
                        item = Gio.MenuItem.new(choice_label, None)
                        item.set_action_and_target_value(
                            f"win.{spec.action}", GLib.Variant.new_string(choice_value)
                        )
                        choices_menu.append_item(item)
                    section.append_submenu(spec.label, choices_menu)
                else:
                    section.append(spec.label, f"win.{spec.action}")
            if menu_name == "Edit":
                transform_menu = Gio.Menu()
                for spec in COMMANDS:
                    if spec.menu == "Edit" and spec.submenu == "Transform Text":
                        transform_menu.append(spec.label, f"win.{spec.action}")
                section.append_submenu("Transform Text", transform_menu)
            root.append_submenu(menu_name, section)
        menubar = Gtk.MenuBar.new_from_model(root)
        container = self.get_child()
        assert isinstance(container, Gtk.Box)
        container.pack_start(menubar, False, False, 0)
        container.reorder_child(menubar, 0)
        menubar.show_all()
        # Keep Recent truly lazy: state is first read only when File is explicitly shown.
        for item in menubar.get_children():
            if getattr(item, "get_label", lambda: None)() == "File":
                submenu = item.get_submenu()
                if submenu is not None:
                    submenu.connect("show", lambda *_args: self._refresh_recent_menu())
                break

    def _refresh_recent_menu(self) -> None:
        self._recent_menu.remove_all()
        paths = self.core.recent_files.paths
        for path in paths:
            item = Gio.MenuItem.new(path, None)
            item.set_action_and_target_value("win.open-recent", GLib.Variant.new_string(path))
            self._recent_menu.append_item(item)
        clear_section = Gio.Menu()
        clear_section.append("Clear Recent", "win.clear-recent")
        self._recent_menu.append_section(None, clear_section)
        self._actions["clear-recent"].set_enabled(bool(paths))

    def _apply_initial_view_settings(self) -> None:
        settings = self.core.view_settings.current
        self.text_view.set_wrap_mode(
            Gtk.WrapMode.WORD_CHAR if settings.word_wrap else Gtk.WrapMode.NONE
        )
        self.text_view.set_line_numbers_visible(settings.line_numbers)
        self.text_view.set_base_font(settings.font_family, settings.font_size_points)
        self.text_view.set_tab_width(settings.tab_width)
        self.text_view.set_insert_spaces(settings.insert_spaces)
        self._set_status_bar_visible(settings.status_bar)

    def _set_status_bar_visible(self, visible: bool) -> None:
        # Gtk.Window.show_all() must not resurrect a persistently hidden status bar.
        self._status_bar.set_no_show_all(not visible)
        if visible:
            self._status_bar.show_all()
        else:
            self._status_bar.hide()

    @staticmethod
    def _boolean_action_value(action: Gio.SimpleAction) -> bool:
        state = action.get_state()
        assert state is not None
        return state.get_boolean()

    @staticmethod
    def _set_boolean_action(action: Gio.SimpleAction, value: bool) -> None:
        action.set_state(GLib.Variant.new_boolean(bool(value)))

    def _persist_view_setting(self, **changes) -> bool:
        try:
            self.core.view_settings.update(**changes)
            return True
        except Exception as exc:
            self._ui.show_warning("View setting was not saved", str(exc))
            return False

    def _apply_appearance(self, value: str) -> None:
        if value not in APPEARANCE_VALUES:
            raise ValueError(f"unsupported appearance: {value!r}")
        if value == APPEARANCE_SYSTEM and self._appearance_renderer is None:
            return
        if self._appearance_renderer is None:
            from .appearance import GtkAppearanceRenderer

            self._appearance_renderer = GtkAppearanceRenderer(
                Gtk.Settings.get_default(),
                self.get_screen(),
                system_prefer_dark_theme=self._system_prefer_dark_theme,
            )
        self._appearance_renderer.apply(value)

    @staticmethod
    def _set_string_action(action: Gio.SimpleAction, value: str) -> None:
        action.set_state(GLib.Variant.new_string(value))

    def _install_file_drop_target(self) -> None:
        # GraphiumTextView is the single DnD negotiation authority. The window
        # owns only local-file filtering and the existing open/dirty/Cancel lifecycle.
        self.text_view.set_file_drop_handler(self._on_text_view_file_drop_uris)

    def _on_text_view_file_drop_uris(self, uris) -> bool:
        paths = self._local_file_paths_from_uris(uris)
        return self._open_dropped_paths(paths)

    @staticmethod
    def _local_file_paths_from_uris(uris) -> list[str]:
        paths: list[str] = []
        for uri in uris:
            try:
                path = Gio.File.new_for_uri(uri).get_path()
            except Exception:
                path = None
            if path and Path(path).is_file():
                paths.append(path)
        return paths

    def _open_dropped_paths(self, paths: list[str]) -> bool:
        if not paths:
            return False
        completed = self.open_path(paths[0])
        if completed and len(paths) > 1:
            application = self.get_application()
            spawn = getattr(application, "_spawn_additional_paths", None)
            if callable(spawn):
                spawn(paths[1:])
        return bool(completed)

    def _on_configure_event(self, _window, event) -> bool:
        native = self.get_window()
        state = native.get_state() if native is not None else Gdk.WindowState(0)
        if state & (Gdk.WindowState.MAXIMIZED | Gdk.WindowState.FULLSCREEN):
            return False
        width = int(event.width)
        height = int(event.height)
        if (
            MIN_WINDOW_WIDTH <= width <= MAX_WINDOW_WIDTH
            and MIN_WINDOW_HEIGHT <= height <= MAX_WINDOW_HEIGHT
        ):
            self._normal_window_size = (width, height)
        return False

    def _persist_normal_window_size_after_accepted_close(self) -> None:
        if self._window_size_persisted:
            return
        self._window_size_persisted = True
        width, height = self._normal_window_size
        try:
            self.core.view_settings.update(window_width=width, window_height=height)
        except Exception as exc:
            # Window geometry is convenience state. Closing remains accepted even when
            # config persistence fails, and the prior complete settings snapshot stays live.
            self._ui.show_warning("Window size was not saved", str(exc))

    def _connect_native_edit_signals(self) -> None:
        # Real semantic boundaries come from GtkTextBuffer user actions and structural
        # insert/delete deltas. No wall-clock timer participates in Undo grouping.
        self.buffer.connect("begin-user-action", self._on_begin_user_action)
        # Pre-default guards run before GtkTextBuffer mutates. They prevent a normal
        # document from being edited into the same pathological huge-line state that
        # The renderability policy rejects on Open. GTK documents that insertion/deletion occurs in the
        # default handler, after handlers connected with connect().
        self.buffer.connect("insert-text", self._on_insert_text_guard)
        self.buffer.connect_after("insert-text", self._on_insert_text_after)
        self.buffer.connect("delete-range", self._on_delete_range_guard)
        self.buffer.connect("delete-range", self._on_delete_range_before)
        self.buffer.connect_after("delete-range", self._on_delete_range_after)
        self.buffer.connect_after("end-user-action", self._on_end_user_action)

    def _editing_suppressed(self) -> bool:
        return self.core.editor.restoring or self.core.session.loading

    def _on_begin_user_action(self, _buffer) -> None:
        if self._editing_suppressed() or self.core.editor.native_group_active:
            return
        self.core.editor.begin_native_group(self.buffer_port.capture_view())

    def _queue_renderability_notice(self, message: str) -> None:
        if self._renderability_notice_pending:
            return
        self._renderability_notice_pending = True

        def show_notice() -> bool:
            self._renderability_notice_pending = False
            self._ui.show_warning("Edit blocked to keep Graphium responsive", message)
            return False

        GLib.idle_add(show_notice)

    def _on_insert_text_guard(self, buffer, location, text: str, _length: int) -> None:
        if self._editing_suppressed() or not text:
            return
        line_start = location.copy()
        line_start.set_line_offset(0)
        line_end = location.copy()
        line_end.forward_to_line_end()
        prefix = location.get_offset() - line_start.get_offset()
        suffix = line_end.get_offset() - location.get_offset()
        try:
            ensure_insert_renderable(
                prefix_chars=prefix,
                suffix_chars=suffix,
                inserted_text=text,
            )
        except InteractiveRenderabilityError as exc:
            GObject.signal_stop_emission_by_name(buffer, "insert-text")
            self._queue_renderability_notice(str(exc))

    def _on_delete_range_guard(self, buffer, start_iter, end_iter) -> None:
        if self._editing_suppressed() or start_iter.get_line() == end_iter.get_line():
            return
        end_line_end = end_iter.copy()
        end_line_end.forward_to_line_end()
        prefix = start_iter.get_line_offset()
        suffix = end_line_end.get_offset() - end_iter.get_offset()
        try:
            ensure_join_renderable(prefix_chars=prefix, suffix_chars=suffix)
        except InteractiveRenderabilityError as exc:
            GObject.signal_stop_emission_by_name(buffer, "delete-range")
            self._queue_renderability_notice(str(exc))

    def _begin_implicit_insert_group(self, start_offset: int) -> bool:
        if self.core.editor.native_group_active:
            return False
        # Fallback for programmatic GtkTextBuffer edits not wrapped in a user action.
        self.core.editor.begin_native_group(ViewState(start_offset, start_offset))
        return True

    def _on_insert_text_after(self, _buffer, location, text: str, _length: int) -> None:
        if self._editing_suppressed() or not text:
            return
        end = location.get_offset()
        start = end - len(text)
        implicit = self._begin_implicit_insert_group(start)
        self.core.editor.record_native_insert(start, text)
        if implicit:
            self.core.editor.end_native_group(self.buffer_port.capture_view())
            self._refresh_projection()

    def _on_delete_range_before(self, _buffer, start_iter, end_iter) -> None:
        if self._editing_suppressed():
            return
        start = start_iter.get_offset()
        end = end_iter.get_offset()
        if end <= start:
            return
        implicit = False
        if not self.core.editor.native_group_active:
            self.core.editor.begin_native_group(self.buffer_port.capture_view())
            implicit = True
        deleted = self.buffer_port.text_in_range(start, end)
        direction = self.buffer_port.delete_direction(start, end)
        self.core.editor.record_native_delete(start, deleted, direction=direction)
        self._implicit_delete_group = implicit

    def _on_delete_range_after(self, _buffer, _start_iter, _end_iter) -> None:
        if self._editing_suppressed():
            return
        if self._implicit_delete_group and self.core.editor.native_group_active:
            self._implicit_delete_group = False
            self.core.editor.end_native_group(self.buffer_port.capture_view())
            self._refresh_projection()

    def _on_end_user_action(self, _buffer) -> None:
        if self._editing_suppressed():
            return
        self._implicit_delete_group = False
        if self.core.editor.native_group_active:
            self.core.editor.end_native_group(self.buffer_port.capture_view())
        self._refresh_projection()

    def _on_selection_changed(self, _buffer, _pspec) -> None:
        self._refresh_projection()

    def _on_cursor_position_changed(self, _buffer, _pspec) -> None:
        self._refresh_status()

    def _title(self) -> str:
        path = self.core.session.logical_path
        name = Path(path).name if path else "Untitled"
        state = "Modified" if self.core.session.modified else "Saved"
        return f"{name} ({state}) — {self._identity.product_name}"

    def _refresh_projection(self) -> None:
        self.set_title(self._title())
        session = self.core.session
        profile = session.current_representation_profile
        self._set_string_action(self._actions["encoding"], encoding_choice_value(profile))
        self._set_string_action(self._actions["line-endings"], profile.line_ending.value)
        availability = command_availability(
            modified=session.modified,
            has_path=session.logical_path is not None,
            can_undo=self.core.editor.can_undo,
            can_redo=self.core.editor.can_redo,
            has_selection=self.buffer.get_has_selection(),
        )
        self._actions["save"].set_enabled(availability.save)
        self._actions["reload"].set_enabled(availability.reload)
        self._actions["undo"].set_enabled(availability.undo)
        self._actions["redo"].set_enabled(availability.redo)
        self._actions["cut"].set_enabled(availability.cut)
        self._actions["copy"].set_enabled(availability.copy)
        self._actions["delete"].set_enabled(availability.delete)
        self._actions["uppercase"].set_enabled(availability.uppercase)
        self._actions["lowercase"].set_enabled(availability.lowercase)
        self._refresh_status()

    def _refresh_status(self) -> None:
        insert = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        status = project_compact_status(
            line=insert.get_line() + 1,
            column=insert.get_line_offset() + 1,
            representation_profile=self.core.session.current_representation_profile,
            modified=self.core.session.modified,
        )
        self._status_position.set_text(status.position_text)
        self._status_document.set_text(status.document_text)

    def _action_new(self, *_args) -> None:
        self._suspend_external_monitor()
        result = self.core.lifecycle.new_document()
        if result.completed:
            self._clear_external_file_alert()
        self._schedule_external_monitor_bind()
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_open(self, *_args) -> None:
        self._suspend_external_monitor()
        result = self.core.lifecycle.open_document()
        if result.completed:
            self._clear_external_file_alert()
            self._refresh_recent_menu()
        self._schedule_external_monitor_bind()
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_open_recent(self, _action, parameter) -> None:
        if parameter is None:
            return
        self._suspend_external_monitor()
        result = self.core.lifecycle.open_document(parameter.get_string())
        if result.completed:
            self._clear_external_file_alert()
            self._refresh_recent_menu()
        self._schedule_external_monitor_bind()
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_clear_recent(self, *_args) -> None:
        try:
            self.core.recent_files.clear()
        except Exception as exc:
            self._ui.show_warning("Recent file history was not cleared", str(exc))
        self._refresh_recent_menu()

    def open_path(
        self,
        path: str,
        *,
        replacement_permit: DocumentReplacementPermit | None = None,
    ) -> bool:
        self._suspend_external_monitor()
        result = self.core.lifecycle.open_document(path, replacement_permit=replacement_permit)
        if result.completed:
            self._clear_external_file_alert()
            self._refresh_recent_menu()
        self._schedule_external_monitor_bind()
        self._refresh_projection()
        self.text_view.grab_focus()
        return result.completed

    def _action_save(self, *_args) -> None:
        self._suspend_external_monitor()
        result = self.core.lifecycle.save()
        if result.completed:
            self._clear_external_file_alert()
            self._refresh_recent_menu()
        self._schedule_external_monitor_bind()
        self._refresh_projection()

    def _action_save_as(self, *_args) -> None:
        self._suspend_external_monitor()
        result = self.core.lifecycle.save_as()
        if result.completed:
            self._clear_external_file_alert()
            self._refresh_recent_menu()
        self._schedule_external_monitor_bind()
        self._refresh_projection()

    def _action_reload(self, *_args) -> None:
        self._suspend_external_monitor()
        result = self.core.lifecycle.reload_document()
        if result.completed:
            self._clear_external_file_alert()
        self._schedule_external_monitor_bind()
        self._refresh_projection()
        self.text_view.grab_focus()

    def _prepare_nonbinding_copy(self) -> bool:
        try:
            self.core.editor.prepare_for_save()
            return True
        except Exception as exc:
            self._ui.show_error("Could not prepare editor state for copying", str(exc))
            return False

    def _show_copy_warnings(self, result) -> None:
        if result.warnings:
            self._ui.show_warning("Copy completed with warnings", "\n".join(result.warnings))
        elif result.disposition is not SaveDisposition.COMMITTED_CONFIRMED:
            self._ui.show_warning(
                "Copy completed with uncertainty",
                "The copy was committed, but Graphium could not confirm every post-write property.",
            )

    def _commit_copy_observation(self, observation) -> bool:
        try:
            result = self.core.document_copy.copy_to(observation)
        except MixedLineEndingConfirmationRequired:
            if not self._ui.confirm_mixed_eol_normalization():
                return False
            try:
                result = self.core.document_copy.copy_to(
                    observation, allow_mixed_eol_normalization=True
                )
            except Exception as exc:
                self._ui.show_error("Could not save copy", str(exc))
                return False
        except Exception as exc:
            self._ui.show_error("Could not save copy", str(exc))
            return False
        self._show_copy_warnings(result)
        return True

    def _action_save_copy(self, *_args) -> None:
        if not self._prepare_nonbinding_copy():
            return
        path = choose_copy_path(
            self, current_path=self.core.session.logical_path, title="Save a Copy"
        )
        if not path:
            self.text_view.grab_focus()
            return
        try:
            observation = self.core.document_copy.observe_target(path)
        except Exception as exc:
            self._ui.show_error("Could not inspect copy destination", str(exc))
            return
        if observation.existing is not None and not self._ui.confirm_overwrite(
            observation.logical_target_path
        ):
            return
        self._commit_copy_observation(observation)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_save_version_copy(self, *_args) -> None:
        if not self._prepare_nonbinding_copy():
            return
        try:
            if self.core.session.logical_path is None:
                path = choose_copy_path(
                    self,
                    current_path=None,
                    suggested_name="Untitled_v0001.txt",
                    title="Save Version Copy",
                )
                if not path:
                    self.text_view.grab_focus()
                    return
                observation = self.core.document_copy.observe_target(path)
                if observation.existing is not None and not self._ui.confirm_overwrite(
                    observation.logical_target_path
                ):
                    return
            else:
                plan = self.core.document_copy.plan_named_version_copy()
                observation = self.core.document_copy.observe_planned_version_target(plan)
        except Exception as exc:
            self._ui.show_error("Could not prepare version copy", str(exc))
            return
        self._commit_copy_observation(observation)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_properties(self, *_args) -> None:
        show_properties(self, self.core.document_properties)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _ensure_print_controller(self):
        # Printing startup boundary: importing the print adapter and reading Page Setup
        # are both deferred until the first explicit print-family action.
        if self._print_controller is None:
            from .printing import GraphiumPrintController

            self._print_controller = GraphiumPrintController(
                self,
                show_error=self._ui.show_error,
                show_warning=self._ui.show_warning,
                page_setup_path=self._xdg_paths.config / "page-setup.ini",
            )
        return self._print_controller

    def _capture_print_snapshot(self):
        captured = self.buffer_port.capture_full()
        return build_print_snapshot(
            text=captured.text,
            logical_path=self.core.session.logical_path,
            base_font=self.text_view.base_font,
        )

    def _action_page_setup(self, *_args) -> None:
        controller = self._ensure_print_controller()
        controller.run_page_setup()
        self.text_view.grab_focus()

    def _action_print_preview(self, *_args) -> None:
        controller = self._ensure_print_controller()
        snapshot = self._capture_print_snapshot()
        controller.preview(snapshot)
        self.text_view.grab_focus()

    def _action_print(self, *_args) -> None:
        controller = self._ensure_print_controller()
        snapshot = self._capture_print_snapshot()
        controller.print_dialog(snapshot)
        self.text_view.grab_focus()

    def _action_quit(self, *_args) -> None:
        self.close()

    def _action_undo(self, *_args) -> None:
        self.core.editor.undo()
        self._refresh_projection()

    def _action_redo(self, *_args) -> None:
        self.core.editor.redo()
        self._refresh_projection()

    def _action_cut(self, *_args) -> None:
        self.text_view.emit("cut-clipboard")

    def _action_copy(self, *_args) -> None:
        self.text_view.emit("copy-clipboard")

    def _action_paste(self, *_args) -> None:
        self.text_view.emit("paste-clipboard")

    def _action_delete(self, *_args) -> None:
        self.buffer.begin_user_action()
        try:
            self.buffer.delete_selection(True, True)
        finally:
            self.buffer.end_user_action()

    def _action_select_all(self, *_args) -> None:
        start, end = self.buffer.get_bounds()
        self.buffer.select_range(start, end)

    @staticmethod
    def _tab_width_action_state(width: int) -> str:
        return str(width) if width in (2, 3, 4, 8) else "other"

    def _action_tab_width(self, action: Gio.SimpleAction, parameter) -> None:
        if parameter is None:
            return
        value = parameter.get_string()
        if value == "other":
            width = choose_tab_width(self, current=self.core.view_settings.current.tab_width)
            if width is None:
                self.text_view.grab_focus(); return
        elif value in ("2", "3", "4", "8"):
            width = int(value)
        else:
            return
        if width != self.core.view_settings.current.tab_width:
            if not self._persist_view_setting(tab_width=width):
                return
            self.text_view.set_tab_width(width)
        self._set_string_action(action, self._tab_width_action_state(width))
        self.text_view.grab_focus()

    def _action_insert_spaces(self, action: Gio.SimpleAction, _parameter) -> None:
        value = not self._boolean_action_value(action)
        if self._persist_view_setting(insert_spaces=value):
            self._set_boolean_action(action, value)
            self.text_view.set_insert_spaces(value)
            self.text_view.grab_focus()

    def _perform_text_transform(self, action_name: str) -> None:
        captured = self.buffer_port.capture_full()
        before_view = ViewState(captured.insert_offset, captured.selection_bound_offset)
        try:
            plan = build_transformation_plan(
                action_name,
                source_text=captured.text,
                source_state_id=self.core.history.current_state_id,
                before_view=before_view,
            )
            if plan.changed:
                self.core.editor.apply_prevalidated_programmatic_group(
                    operations=plan.operations,
                    expected_source_state_id=plan.source_state_id,
                    final_text=plan.final_text,
                    before_view=plan.before_view,
                    target_view=plan.target_view,
                )
                self._refresh_projection()
                self.text_view.scroll_to_mark(
                    self.buffer.get_insert(), 0.08, False, 0.0, 0.0
                )
        except Exception as exc:
            self._ui.show_warning("Text transformation was not applied", str(exc))
        self.text_view.grab_focus()

    def _action_uppercase(self, *_args) -> None:
        self._perform_text_transform("uppercase")

    def _action_lowercase(self, *_args) -> None:
        self._perform_text_transform("lowercase")

    def _action_duplicate_line_selection(self, *_args) -> None:
        self._perform_text_transform("duplicate-line-selection")

    def _action_move_lines_up(self, *_args) -> None:
        self._perform_text_transform("move-lines-up")

    def _action_move_lines_down(self, *_args) -> None:
        self._perform_text_transform("move-lines-down")

    def _action_trim_trailing_spaces(self, *_args) -> None:
        self._perform_text_transform("trim-trailing-spaces")

    def _set_search_status(self, message: str) -> None:
        if self._search_status is not None:
            self._search_status.set_text(message)

    def _search_entry_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self._close_search_bar()
            return True
        return False

    def _ensure_search_bar(self) -> None:
        if self._search_bar is not None:
            return
        bar = Gtk.SearchBar()
        bar.set_show_close_button(True)
        grid = Gtk.Grid(column_spacing=8, row_spacing=5)
        grid.set_border_width(6)
        bar.add(grid)

        query_label = Gtk.Label(label="Find:")
        query_label.set_xalign(0.0)
        query = Gtk.SearchEntry()
        query.set_width_chars(24)
        previous = Gtk.Button(label="Previous")
        next_button = Gtk.Button(label="Next")
        match_case = Gtk.CheckButton(label="Match Case")
        status = Gtk.Label(label="")
        status.set_xalign(0.0)

        grid.attach(query_label, 0, 0, 1, 1)
        grid.attach(query, 1, 0, 1, 1)
        grid.attach(previous, 2, 0, 1, 1)
        grid.attach(next_button, 3, 0, 1, 1)
        grid.attach(match_case, 4, 0, 1, 1)
        grid.attach(status, 5, 0, 1, 1)

        replace_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        replace_label = Gtk.Label(label="Replace with:")
        replacement = Gtk.Entry()
        replacement.set_width_chars(24)
        replace_one = Gtk.Button(label="Replace")
        replace_all = Gtk.Button(label="Replace All")
        replace_row.pack_start(replace_label, False, False, 0)
        replace_row.pack_start(replacement, True, True, 0)
        replace_row.pack_start(replace_one, False, False, 0)
        replace_row.pack_start(replace_all, False, False, 0)
        grid.attach(replace_row, 0, 1, 6, 1)

        query.connect("activate", lambda *_args: self._perform_find_next())
        query.connect("key-press-event", self._search_entry_key_press)
        replacement.connect("activate", lambda *_args: self._perform_replace_one())
        replacement.connect("key-press-event", self._search_entry_key_press)
        previous.connect("clicked", lambda *_args: self._perform_find_previous())
        next_button.connect("clicked", lambda *_args: self._perform_find_next())
        replace_one.connect("clicked", lambda *_args: self._perform_replace_one())
        replace_all.connect("clicked", lambda *_args: self._perform_replace_all())
        match_case.connect("toggled", self._on_search_option_changed)
        query.connect("changed", self._on_query_entry_changed)
        replacement.connect("changed", self._on_replacement_entry_changed)
        bar.connect_entry(query)
        bar.connect("notify::search-mode-enabled", self._on_search_mode_changed)

        container = self.get_child()
        assert isinstance(container, Gtk.Box)
        container.pack_start(bar, False, False, 0)
        container.reorder_child(bar, 1)

        self._search_bar = bar
        self._search_query_entry = query
        self._search_replace_entry = replacement
        self._search_replace_row = replace_row
        self._search_match_case = match_case
        self._search_status = status
        bar.show_all()
        replace_row.hide()
        bar.set_search_mode(False)

    def _on_search_mode_changed(self, bar: Gtk.SearchBar, _param) -> None:
        if not bar.get_search_mode():
            self.text_view.grab_focus()

    def _on_query_entry_changed(self, entry: Gtk.Entry) -> None:
        query = entry.get_text()
        if not query:
            self.core.search.clear_query()
            self._set_search_status("")
            return
        try:
            self.core.search.configure(query=query)
            self._set_search_status("")
        except SearchInputError as exc:
            self._set_search_status(str(exc))

    def _on_replacement_entry_changed(self, entry: Gtk.Entry) -> None:
        try:
            self.core.search.configure(replacement=entry.get_text())
        except SearchInputError as exc:
            self._set_search_status(str(exc))

    def _on_search_option_changed(self, button: Gtk.CheckButton) -> None:
        self.core.search.configure(match_case=button.get_active())
        self._set_search_status("")

    def _sync_search_fields(self) -> bool:
        assert self._search_query_entry is not None
        assert self._search_replace_entry is not None
        assert self._search_match_case is not None
        query = self._search_query_entry.get_text()
        if not query:
            self.core.search.clear_query()
            self._set_search_status("Type text to find")
            self._search_query_entry.grab_focus()
            return False
        try:
            self.core.search.configure(
                query=query,
                replacement=self._search_replace_entry.get_text(),
                match_case=self._search_match_case.get_active(),
            )
        except SearchInputError as exc:
            self._set_search_status(str(exc))
            self._search_query_entry.grab_focus()
            return False
        return True

    def _selected_single_line_text(self) -> str | None:
        selected = self.buffer.get_selection_bounds()
        if not selected:
            return None
        start, end = selected
        text = self.buffer.get_text(start, end, True)
        if not text or "\n" in text or "\r" in text or len(text) > 4096:
            return None
        return text

    def _show_search_bar(self, *, replace_mode: bool) -> None:
        self._ensure_search_bar()
        assert self._search_bar is not None
        assert self._search_query_entry is not None
        assert self._search_replace_entry is not None
        assert self._search_replace_row is not None
        assert self._search_match_case is not None
        selected = self._selected_single_line_text()
        if selected is not None:
            self._search_query_entry.set_text(selected)
        elif self.core.search.has_query and self._search_query_entry.get_text() != self.core.search.query:
            self._search_query_entry.set_text(self.core.search.query)
        self._search_replace_entry.set_text(self.core.search.replacement)
        self._search_match_case.set_active(self.core.search.match_case)
        self._search_bar.set_search_mode(True)
        self._search_bar.show_all()
        self._search_replace_row.set_visible(replace_mode)
        self._set_search_status("")
        self._search_query_entry.grab_focus()
        self._search_query_entry.select_region(0, -1)

    def _close_search_bar(self) -> None:
        if self._search_bar is not None:
            self._search_bar.set_search_mode(False)
        self.text_view.grab_focus()

    def _search_snapshot(self) -> tuple[str, ViewState]:
        captured = self.buffer_port.capture_full()
        return captured.text, ViewState(captured.insert_offset, captured.selection_bound_offset)

    def _selection_offsets(self, view: ViewState | None = None) -> tuple[int, int]:
        if view is None:
            view = self.buffer_port.capture_view()
        return min(view.insert_offset, view.selection_bound_offset), max(
            view.insert_offset, view.selection_bound_offset
        )

    def _project_view(self, view: ViewState) -> None:
        insert = self.buffer.get_iter_at_offset(view.insert_offset)
        bound = self.buffer.get_iter_at_offset(view.selection_bound_offset)
        self.buffer.select_range(insert, bound)
        self.text_view.scroll_to_mark(self.buffer.get_insert(), 0.08, False, 0.0, 0.0)
        self._refresh_projection()

    def _project_match(self, match: SearchMatch) -> None:
        self._project_view(ViewState(match.end, match.start))

    def _perform_find_next(self) -> None:
        self._ensure_search_bar()
        if not self._sync_search_fields():
            return
        text, view = self._search_snapshot()
        start, end = self._selection_offsets(view)
        anchor = end if end > start else view.insert_offset
        result = self.core.search.find_next(text, anchor)
        if result.match is None:
            self._set_search_status("Not found")
            return
        self._project_match(result.match)
        self._set_search_status("Wrapped" if result.wrapped else "")

    def _perform_find_previous(self) -> None:
        self._ensure_search_bar()
        if not self._sync_search_fields():
            return
        text, view = self._search_snapshot()
        start, end = self._selection_offsets(view)
        anchor = start if end > start else view.insert_offset
        result = self.core.search.find_previous(text, anchor)
        if result.match is None:
            self._set_search_status("Not found")
            return
        self._project_match(result.match)
        self._set_search_status("Wrapped" if result.wrapped else "")

    def _apply_replacement_plan(self, plan) -> None:
        if plan.changed:
            self.core.editor.apply_prevalidated_programmatic_group(
                operations=plan.operations,
                expected_source_state_id=plan.source_state_id,
                final_text=plan.final_text,
                before_view=plan.before_view,
                target_view=plan.target_view,
            )
            self._refresh_projection()
        else:
            self._project_view(plan.target_view)
        self.text_view.scroll_to_mark(self.buffer.get_insert(), 0.08, False, 0.0, 0.0)

    def _perform_replace_one(self) -> None:
        self._ensure_search_bar()
        if not self._sync_search_fields():
            return
        text, view = self._search_snapshot()
        start, end = self._selection_offsets(view)
        try:
            plan = self.core.search.build_replace_one_plan(
                source_text=text,
                source_state_id=self.core.history.current_state_id,
                before_view=view,
                selection_start=start,
                selection_end=end,
            )
            if plan is None:
                self._set_search_status("Not found")
                return
            self._apply_replacement_plan(plan)
            self._set_search_status("Replaced" if plan.changed else "No text change")
        except Exception as exc:
            self._ui.show_warning("Replace was not applied", str(exc))

    def _perform_replace_all(self) -> None:
        self._ensure_search_bar()
        if not self._sync_search_fields():
            return
        text, view = self._search_snapshot()
        try:
            plan = self.core.search.build_replace_all_plan(
                source_text=text,
                source_state_id=self.core.history.current_state_id,
                before_view=view,
            )
            self._apply_replacement_plan(plan)
            if plan.changed_count == 0:
                self._set_search_status("No changes")
            elif plan.changed_count == 1:
                self._set_search_status("1 replacement")
            else:
                self._set_search_status(f"{plan.changed_count} replacements")
        except Exception as exc:
            self._ui.show_warning("Replace All was not applied", str(exc))

    def _action_find(self, *_args) -> None:
        self._show_search_bar(replace_mode=False)

    def _action_find_next(self, *_args) -> None:
        if not self.core.search.has_query:
            self._show_search_bar(replace_mode=False)
            return
        search_visible = self._search_bar is not None and self._search_bar.get_search_mode()
        self._ensure_search_bar()
        assert self._search_query_entry is not None
        if not self._search_query_entry.get_text():
            self._search_query_entry.set_text(self.core.search.query)
        self._perform_find_next()
        if not search_visible:
            self.text_view.grab_focus()

    def _action_find_previous(self, *_args) -> None:
        if not self.core.search.has_query:
            self._show_search_bar(replace_mode=False)
            return
        search_visible = self._search_bar is not None and self._search_bar.get_search_mode()
        self._ensure_search_bar()
        assert self._search_query_entry is not None
        if not self._search_query_entry.get_text():
            self._search_query_entry.set_text(self.core.search.query)
        self._perform_find_previous()
        if not search_visible:
            self.text_view.grab_focus()

    def _action_replace(self, *_args) -> None:
        self._show_search_bar(replace_mode=True)

    def _action_go_to_line(self, *_args) -> None:
        insert = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        chosen = choose_line_number(
            self,
            current_line=insert.get_line() + 1,
            max_line=self.buffer.get_line_count(),
        )
        if chosen is None:
            self.text_view.grab_focus()
            return
        target = self.buffer.get_iter_at_line(chosen - 1)
        self.buffer.place_cursor(target)
        self.text_view.scroll_to_iter(target, 0.08, False, 0.0, 0.0)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_status_bar(self, action: Gio.SimpleAction, _parameter) -> None:
        value = not self._boolean_action_value(action)
        if not self._persist_view_setting(status_bar=value):
            return
        self._set_boolean_action(action, value)
        self._set_status_bar_visible(value)

    def _action_line_numbers(self, action: Gio.SimpleAction, _parameter) -> None:
        value = not self._boolean_action_value(action)
        if not self._persist_view_setting(line_numbers=value):
            return
        self._set_boolean_action(action, value)
        self.text_view.set_line_numbers_visible(value)

    def _action_word_wrap(self, action: Gio.SimpleAction, _parameter) -> None:
        value = not self._boolean_action_value(action)
        if not self._persist_view_setting(word_wrap=value):
            return
        self._set_boolean_action(action, value)
        self.text_view.set_wrap_mode(
            Gtk.WrapMode.WORD_CHAR if value else Gtk.WrapMode.NONE
        )

    def _action_appearance(self, action: Gio.SimpleAction, parameter) -> None:
        if parameter is None:
            return
        value = parameter.get_string()
        if value not in APPEARANCE_VALUES:
            return
        previous = self.core.view_settings.current.appearance
        if value == previous:
            self._set_string_action(action, value)
            return
        try:
            self._apply_appearance(value)
        except Exception as exc:
            self._ui.show_warning("Appearance was not changed", str(exc))
            return
        try:
            self.core.view_settings.update(appearance=value)
        except Exception as exc:
            try:
                self._apply_appearance(previous)
            except Exception:
                pass
            self._ui.show_warning("Appearance was not saved", str(exc))
            return
        self._set_string_action(action, value)
        self.text_view.grab_focus()

    def _action_font(self, *_args) -> None:
        settings = self.core.view_settings.current
        chosen = choose_font(
            self, family=settings.font_family, size_points=settings.font_size_points
        )
        if chosen is None:
            self.text_view.grab_focus()
            return
        family, size_points = chosen
        if self._persist_view_setting(font_family=family, font_size_points=size_points):
            current = self.core.view_settings.current
            self.text_view.set_base_font(current.font_family, current.font_size_points)
        self.text_view.grab_focus()

    def _action_zoom_in(self, *_args) -> None:
        self.text_view.zoom_in()
        self.text_view.grab_focus()

    def _action_zoom_out(self, *_args) -> None:
        self.text_view.zoom_out()
        self.text_view.grab_focus()

    def _action_zoom_reset(self, *_args) -> None:
        self.text_view.reset_zoom()
        self.text_view.grab_focus()

    def _action_full_screen(self, action: Gio.SimpleAction, _parameter) -> None:
        value = not self._boolean_action_value(action)
        self._set_boolean_action(action, value)
        if value:
            self.fullscreen()
        else:
            self.unfullscreen()

    def _on_window_state_event(self, _window, event) -> bool:
        self._window_fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)
        self._window_maximized = bool(event.new_window_state & Gdk.WindowState.MAXIMIZED)
        action = self._actions.get("full-screen")
        if action is not None and self._boolean_action_value(action) != self._window_fullscreen:
            self._set_boolean_action(action, self._window_fullscreen)
        return False

    def _action_encoding(self, action: Gio.SimpleAction, parameter) -> None:
        if parameter is None:
            return
        value = parameter.get_string()
        target = encoding_choice_target(value)
        if target is None:
            return
        try:
            changed = self.core.session.select_representation_encoding(*target)
        except Exception as exc:
            self._ui.show_warning("Encoding was not changed", str(exc))
            return
        if changed and self.core.recovery is not None:
            self.core.recovery.document_state_changed()
        self._set_string_action(action, value)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_line_endings(self, action: Gio.SimpleAction, parameter) -> None:
        if parameter is None:
            return
        value = parameter.get_string()
        target = line_ending_choice_target(value)
        if target is None:
            return
        try:
            changed = self.core.session.select_representation_line_ending(target)
        except Exception as exc:
            self._ui.show_warning("Line endings were not changed", str(exc))
            return
        if changed and self.core.recovery is not None:
            self.core.recovery.document_state_changed()
        self._set_string_action(action, value)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_check_spelling(self, *_args) -> None:
        from .spelling import run_spell_check_dialog

        def changed() -> None:
            self._refresh_projection()
            self.text_view.scroll_to_mark(self.buffer.get_insert(), 0.08, False, 0.0, 0.0)

        run_spell_check_dialog(self, editor=self.core.editor, on_changed=changed)
        self._refresh_projection()
        self.text_view.grab_focus()

    def _action_statistics(self, *_args) -> None:
        captured = self.buffer_port.capture_full()
        document = count_text_statistics(captured.text)
        lo = min(captured.insert_offset, captured.selection_bound_offset)
        hi = max(captured.insert_offset, captured.selection_bound_offset)
        selection = count_text_statistics(captured.text[lo:hi]) if hi > lo else None
        show_statistics(self, document=document, selection=selection)
        self.text_view.grab_focus()

    @staticmethod
    def _help_path(name: str) -> str:
        return str(Path(__file__).resolve().parents[3] / "docs" / "user" / name)

    def _action_user_guide(self, *_args) -> None:
        show_text_document(
            self,
            title="Graphium User Guide",
            path=self._help_path("GRAPHIUM_USER_GUIDE.txt"),
        )

    def _action_keyboard_shortcuts(self, *_args) -> None:
        show_text_document(
            self,
            title="Graphium Keyboard Shortcuts",
            path=self._help_path("GRAPHIUM_KEYBOARD_SHORTCUTS.txt"),
        )

    def _action_about(self, *_args) -> None:
        show_about(self, identity=self._identity)

    def _on_delete_event(self, *_args) -> bool:
        if self._closing_accepted:
            return False
        self._suspend_external_monitor()
        result = self.core.lifecycle.request_close()
        if not result.completed:
            self._schedule_external_monitor_bind()
            self._refresh_projection()
            return True
        self._persist_normal_window_size_after_accepted_close()
        self._closing_accepted = True
        return False

    def offer_startup_recovery(self, explicit_path: str | None = None) -> RecoveryStartupResult:
        if self._startup_recovery_checked:
            return RecoveryStartupResult(RecoveryStartupStatus.NONE)
        self._startup_recovery_checked = True
        self._suspend_external_monitor()
        result = self._startup_recovery.run(explicit_path)
        if result.recovered:
            self._clear_external_file_alert()
            self._refresh_projection()
            self.text_view.grab_focus()
        self._schedule_external_monitor_bind()
        return result

    def begin_startup_open(self) -> None:
        self._startup_open_pending = True

    def finish_startup_open(self) -> None:
        self._startup_open_pending = False
        self._schedule_benchmark_ready_if_ready()

    def _on_mapped(self, *_args) -> bool:
        self._mapped = True
        self._schedule_benchmark_ready_if_ready()
        return False

    def _schedule_benchmark_ready_if_ready(self) -> None:
        if self._mapped and not self._startup_open_pending and not self._benchmark_ready_emitted:
            GLib.idle_add(self._emit_benchmark_ready)

    def _emit_benchmark_ready(self) -> bool:
        if self._benchmark_ready_emitted or self._startup_open_pending or not self._mapped:
            return False
        self.text_view.grab_focus()
        self._benchmark_ready_emitted = True
        raw_fd = os.environ.get("GRAPHIUM_BENCHMARK_READY_FD")
        if raw_fd:
            try:
                fd = int(raw_fd)
                payload = f"READY {os.getpid()} {time.monotonic_ns()}\n".encode("ascii")
                os.write(fd, payload)  # one short PIPE_BUF-bounded atomic write
                os.close(fd)
            except (OSError, ValueError):
                pass
        return False
