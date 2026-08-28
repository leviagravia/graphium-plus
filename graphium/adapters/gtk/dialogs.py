"""Small GTK dialog/chooser adapter for Graphium lifecycle and View UI."""
from __future__ import annotations

import sys

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, Gtk, Pango

from graphium.application.file_lifecycle import ReloadDecision, UnsavedDecision
from graphium.application.recovery_startup import RecoveryStartupDecision
from graphium.domain.recovery_artifact import RecoveryDocumentKind, RecoveryRecord
from graphium.product import CORE_PRODUCT_IDENTITY, ProductIdentity


class GtkLifecycleUI:
    __slots__ = ("parent",)

    def __init__(self, parent: Gtk.Window) -> None:
        self.parent = parent

    def choose_open_path(self) -> str | None:
        dialog = Gtk.FileChooserNative.new(
            "Open File", self.parent, Gtk.FileChooserAction.OPEN, "Open", "Cancel"
        )
        try:
            response = dialog.run()
            return dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
        finally:
            dialog.destroy()

    def choose_save_path(self, current_path: str | None) -> str | None:
        dialog = Gtk.FileChooserNative.new(
            "Save File", self.parent, Gtk.FileChooserAction.SAVE, "Save", "Cancel"
        )
        dialog.set_do_overwrite_confirmation(False)
        if current_path:
            dialog.set_filename(current_path)
        else:
            dialog.set_current_name("Untitled.txt")
        try:
            response = dialog.run()
            return dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
        finally:
            dialog.destroy()

    def confirm_unsaved_changes(self, action_label: str) -> UnsavedDecision:
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Save changes before continuing?",
        )
        dialog.format_secondary_text(
            f"The document has unsaved changes. Save them before you {action_label}?"
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Discard Changes", Gtk.ResponseType.REJECT)
        dialog.add_button("Save", Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        try:
            response = dialog.run()
        finally:
            dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            return UnsavedDecision.SAVE
        if response == Gtk.ResponseType.REJECT:
            return UnsavedDecision.DISCARD
        return UnsavedDecision.CANCEL

    def confirm_modified_reload(self) -> ReloadDecision:
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Discard changes and reload from disk?",
        )
        dialog.set_title("Reload from Disk")
        dialog.format_secondary_text(
            "The current document has unsaved changes. Reloading will discard those changes and accept the file currently on disk."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Discard Changes and Reload", Gtk.ResponseType.REJECT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        try:
            response = dialog.run()
        finally:
            dialog.destroy()
        if response == Gtk.ResponseType.REJECT:
            return ReloadDecision.DISCARD_AND_RELOAD
        return ReloadDecision.CANCEL

    def choose_startup_recovery(self, record: RecoveryRecord) -> RecoveryStartupDecision:
        if not isinstance(record, RecoveryRecord):
            raise TypeError("record must be RecoveryRecord")
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Recovered unsaved content",
        )
        if record.document_kind is RecoveryDocumentKind.NAMED and record.named_baseline is not None:
            detail = (
                "Graphium found unsaved content from an interrupted session for:\n"
                f"{record.named_baseline.logical_path}\n\n"
                "Recover it, discard this recovery, or continue without recovering it now."
            )
        else:
            detail = (
                "Graphium found unsaved content from an interrupted Untitled document.\n\n"
                "Recover it, discard this recovery, or continue without recovering it now."
            )
        dialog.format_secondary_text(detail)
        dialog.add_button("Start Without Recovering", Gtk.ResponseType.CANCEL)
        dialog.add_button("Discard Recovery", Gtk.ResponseType.REJECT)
        dialog.add_button("Recover Unsaved Content", Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        try:
            response = dialog.run()
        finally:
            dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            return RecoveryStartupDecision.RECOVER
        if response == Gtk.ResponseType.REJECT:
            return RecoveryStartupDecision.DISCARD
        return RecoveryStartupDecision.START_WITHOUT

    def show_recovered_unbound(self, provenance_path: str, reason: str) -> None:
        self.show_warning(
            "Recovered unsaved content",
            f"{reason}\n\nThe recovered content is open as an unsaved document and is not bound to the original file.\nOriginal location: {provenance_path}",
        )

    def confirm_overwrite(self, path: str) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Replace existing file?",
        )
        dialog.format_secondary_text(
            f"A file already exists at:\n{path}\n\nGraphium will replace it only if it is still the same file at commit time."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Replace", Gtk.ResponseType.ACCEPT)
        try:
            return dialog.run() == Gtk.ResponseType.ACCEPT
        finally:
            dialog.destroy()

    def confirm_mixed_eol_normalization(self) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Normalize mixed line endings?",
        )
        dialog.format_secondary_text(
            "This file contains mixed line endings. Saving will normalize them to the dominant style."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save and Normalize", Gtk.ResponseType.ACCEPT)
        try:
            return dialog.run() == Gtk.ResponseType.ACCEPT
        finally:
            dialog.destroy()

    def _message(self, message_type, title: str, message: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=message_type,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(message)
        try:
            dialog.run()
        finally:
            dialog.destroy()

    def show_error(self, title: str, message: str) -> None:
        self._message(Gtk.MessageType.ERROR, title, message)

    def show_warning(self, title: str, message: str) -> None:
        self._message(Gtk.MessageType.WARNING, title, message)


def show_text_document(parent: Gtk.Window, *, title: str, path: str) -> None:
    """Show a UTF-8 offline help document, loading it only on explicit user request."""
    from pathlib import Path

    try:
        text = Path(path).read_text(encoding="utf-8")
    except Exception as exc:
        GtkLifecycleUI(parent).show_error("Could not open Help", str(exc))
        return
    dialog = Gtk.Dialog(title=title, transient_for=parent, modal=True)
    dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(720, 560)
    area = dialog.get_content_area()
    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    view = Gtk.TextView()
    view.set_editable(False)
    view.set_cursor_visible(False)
    view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    view.set_left_margin(12)
    view.set_right_margin(12)
    view.set_top_margin(10)
    view.set_bottom_margin(10)
    view.get_buffer().set_text(text)
    scroller.add(view)
    area.pack_start(scroller, True, True, 0)
    dialog.show_all()
    try:
        dialog.run()
    finally:
        dialog.destroy()


def _project_about_application_icon(
    dialog: Gtk.AboutDialog, identity: ProductIdentity
) -> None:
    """Project the selected application-icon authority into About."""
    theme = Gtk.IconTheme.get_default()
    if theme is not None and theme.has_icon(identity.application_icon_name):
        dialog.set_logo_icon_name(identity.application_icon_name)
        return
    for icon in Gtk.Window.get_default_icon_list() or ():
        if icon.get_width() == 48 and icon.get_height() == 48:
            dialog.set_logo(icon)
            return


def show_about(
    parent: Gtk.Window,
    *,
    identity: ProductIdentity = CORE_PRODUCT_IDENTITY,
) -> None:
    dialog = Gtk.AboutDialog(transient_for=parent, modal=True)
    _project_about_application_icon(dialog, identity)
    dialog.set_program_name(identity.product_name)
    if identity.version is not None:
        dialog.set_version(identity.version)
    display = Gdk.Display.get_default()
    backend = type(display).__name__ if display is not None else "Unavailable"
    system = (f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}; "
              f"GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}; "
              f"Display {backend}")
    dialog.set_comments("Fast, simple and safety-focused plain-text editor for Linux.\n\n" + system)
    dialog.set_authors([identity.author])
    dialog.set_copyright(identity.copyright)
    dialog.set_license_type(Gtk.License.GPL_3_0)
    dialog.set_website(identity.repository_url)
    dialog.set_website_label(identity.repository_label)
    try:
        dialog.run()
    finally:
        dialog.destroy()



def choose_font(
    parent: Gtk.Window,
    *,
    family: str,
    size_points: float,
) -> tuple[str, float] | None:
    """Choose only the persistent family+size owned by View -> Font."""
    dialog = Gtk.FontChooserDialog(title="Font", transient_for=parent)
    try:
        if hasattr(dialog, "set_level"):
            dialog.set_level(Gtk.FontChooserLevel.FAMILY | Gtk.FontChooserLevel.SIZE)
        initial = Pango.FontDescription()
        initial.set_family(family)
        initial.set_size(int(round(float(size_points) * Pango.SCALE)))
        dialog.set_font_desc(initial)
        if dialog.run() != Gtk.ResponseType.OK:
            return None
        chosen = dialog.get_font_desc()
        chosen_family = chosen.get_family() or family
        chosen_size = chosen.get_size() / Pango.SCALE
        if chosen_size <= 0:
            chosen_size = float(size_points)
        return chosen_family, float(chosen_size)
    finally:
        dialog.destroy()

def choose_line_number(
    parent: Gtk.Window,
    *,
    current_line: int,
    max_line: int,
) -> int | None:
    """Return a 1-based line number without creating navigation/session state."""
    maximum = max(1, int(max_line))
    current = min(max(1, int(current_line)), maximum)
    dialog = Gtk.Dialog(title="Go to Line", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Go", Gtk.ResponseType.ACCEPT)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    area = dialog.get_content_area()
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    row.set_border_width(12)
    label = Gtk.Label(label="Line:")
    adjustment = Gtk.Adjustment(
        value=current, lower=1, upper=maximum, step_increment=1, page_increment=10, page_size=0
    )
    spin = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
    spin.set_numeric(True)
    spin.set_activates_default(True)
    row.pack_start(label, False, False, 0)
    row.pack_start(spin, True, True, 0)
    area.pack_start(row, True, True, 0)
    dialog.show_all()
    spin.grab_focus()
    try:
        if dialog.run() != Gtk.ResponseType.ACCEPT:
            return None
        return min(max(1, spin.get_value_as_int()), maximum)
    finally:
        dialog.destroy()


def choose_copy_path(
    parent: Gtk.Window,
    *,
    current_path: str | None,
    suggested_name: str | None = None,
    title: str = "Save a Copy",
) -> str | None:
    """Choose a non-binding copy destination; caller owns guarded observation/commit."""
    dialog = Gtk.FileChooserNative.new(
        title, parent, Gtk.FileChooserAction.SAVE, "Save", "Cancel"
    )
    dialog.set_do_overwrite_confirmation(False)
    if suggested_name:
        if current_path:
            dialog.set_current_folder(str(__import__('pathlib').Path(current_path).parent))
        dialog.set_current_name(suggested_name)
    elif current_path:
        current = __import__('pathlib').Path(current_path)
        dialog.set_current_folder(str(current.parent))
        dialog.set_current_name(current.name)
    else:
        dialog.set_current_name("Untitled.txt")
    try:
        response = dialog.run()
        return dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
    finally:
        dialog.destroy()


def _format_mtime_ns(value: int | None) -> str:
    if value is None:
        return "Not available"
    from datetime import datetime
    try:
        return datetime.fromtimestamp(value / 1_000_000_000).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return str(value)


def show_properties(parent: Gtk.Window, controller) -> None:
    """Show accepted disk facts plus current representation; Check Now never accepts/reloads."""
    from graphium.application.document_properties import CheckNowStatus

    props = controller.snapshot()
    dialog = Gtk.Dialog(title="Properties", transient_for=parent, modal=True)
    CHECK_RESPONSE = 1001
    check_button = dialog.add_button("Check Now", CHECK_RESPONSE)
    dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    check_button.set_sensitive(props.logical_path is not None)
    dialog.set_default_size(640, 360)
    grid = Gtk.Grid(column_spacing=14, row_spacing=7)
    grid.set_border_width(14)
    grid.set_column_homogeneous(False)
    area = dialog.get_content_area()
    area.pack_start(grid, True, True, 0)

    eol_text = "Mixed" if props.eol_mixed else props.eol.value.upper()
    if eol_text == "NONE":
        eol_text = "None"
    resolved = props.canonical_path or "Not available"
    if props.logical_path and resolved == props.logical_path:
        resolved = "Same as logical path"
    facts = (
        ("Path", props.logical_path or "Not saved"),
        ("Resolved target", resolved if props.logical_path else "Not available"),
        ("Accepted size", f"{props.size} bytes" if props.size is not None else "Not available"),
        ("Accepted modified", _format_mtime_ns(props.mtime_ns)),
        ("Encoding", props.encoding.upper()),
        ("BOM", props.bom.value),
        ("Line endings", eol_text),
        ("Document state", "Modified" if props.modified else "Saved"),
        ("Access", "Read-only" if props.read_only else ("Writable" if props.read_only is False else "Not available")),
        ("Hard links", str(props.nlink) if props.nlink is not None else "Not available"),
    )
    for row, (name, value) in enumerate(facts):
        left = Gtk.Label(label=name + ":")
        left.set_xalign(0.0)
        right = Gtk.Label(label=value)
        right.set_xalign(0.0)
        right.set_selectable(True)
        right.set_line_wrap(True)
        grid.attach(left, 0, row, 1, 1)
        grid.attach(right, 1, row, 1, 1)

    status_title = Gtk.Label(label="Disk check:")
    status_title.set_xalign(0.0)
    status = Gtk.Label(label="Not checked in this dialog")
    status.set_xalign(0.0)
    status.set_line_wrap(True)
    grid.attach(status_title, 0, len(facts), 1, 1)
    grid.attach(status, 1, len(facts), 1, 1)
    dialog.show_all()

    labels = {
        CheckNowStatus.UNCHANGED: "Unchanged — disk matches the accepted baseline",
        CheckNowStatus.CONTENT_CHANGED: "Content changed on disk",
        CheckNowStatus.METADATA_CHANGED: "Metadata changed on disk",
        CheckNowStatus.REPLACED_OR_RETARGETED: "File was replaced or the logical path was retargeted",
        CheckNowStatus.MISSING: "File is missing",
        CheckNowStatus.UNAVAILABLE_OR_UNSTABLE: "Disk state is unavailable or unstable",
    }
    try:
        while True:
            response = dialog.run()
            if response != CHECK_RESPONSE:
                break
            result = controller.check_now()
            text = labels[result.status]
            if result.detail:
                text += f" — {result.detail}"
            status.set_text(text)
    finally:
        dialog.destroy()


def show_statistics(parent: Gtk.Window, *, document, selection) -> None:
    """Render precomputed on-demand statistics; no live subscription is created."""
    dialog = Gtk.Dialog(title="Statistics", transient_for=parent, modal=True)
    dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    grid = Gtk.Grid(column_spacing=18, row_spacing=8)
    grid.set_border_width(14)
    area = dialog.get_content_area()
    area.pack_start(grid, True, True, 0)

    headers = ("", "Lines", "Words", "Characters")
    for col, text in enumerate(headers):
        label = Gtk.Label(label=text)
        label.set_xalign(0.0)
        grid.attach(label, col, 0, 1, 1)
    rows = [("Document", document)]
    if selection is not None:
        rows.append(("Selection", selection))
    for row, (name, stats) in enumerate(rows, start=1):
        values = (name, str(stats.lines), str(stats.words), str(stats.characters))
        for col, text in enumerate(values):
            label = Gtk.Label(label=text)
            label.set_xalign(0.0)
            grid.attach(label, col, row, 1, 1)
    if selection is None:
        label = Gtk.Label(label="Selection: No selection")
        label.set_xalign(0.0)
        grid.attach(label, 0, 2, 4, 1)
    dialog.show_all()
    try:
        dialog.run()
    finally:
        dialog.destroy()


def choose_tab_width(parent: Gtk.Window, *, current: int) -> int | None:
    """Choose one custom tab width; persistence remains outside the dialog."""
    dialog = Gtk.Dialog(title="Tab Width", transient_for=parent, modal=True, destroy_with_parent=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("OK", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    content = dialog.get_content_area(); content.set_border_width(12)
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    label = Gtk.Label(label="Tab width:"); label.set_xalign(0.0)
    adjustment = Gtk.Adjustment(
        value=float(current), lower=1.0, upper=32.0, step_increment=1.0, page_increment=4.0, page_size=0.0
    )
    spin = Gtk.SpinButton(adjustment=adjustment, climb_rate=1.0, digits=0)
    spin.set_numeric(True); spin.set_value(float(current))
    row.pack_start(label, False, False, 0); row.pack_start(spin, False, False, 0)
    content.pack_start(row, True, True, 0); dialog.show_all()
    try:
        return int(spin.get_value_as_int()) if dialog.run() == Gtk.ResponseType.OK else None
    finally:
        dialog.destroy()
