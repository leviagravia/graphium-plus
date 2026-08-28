"""GTK3 application root for Graphium.

Graphium is deliberately NON_UNIQUE: one invocation/process owns one window and one active
document, matching the quick-edit mental model of Leafpad/L3afpad and Airpad. Multiple
command-line files are split into separate Graphium processes rather than tabs/windows in
one server instance.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gio, GLib, Gtk

from graphium.application.commands import COMMANDS
from graphium.product import CORE_PRODUCT_IDENTITY, ProductIdentity
from .window import GraphiumWindow


def application_icon_paths(
    identity: ProductIdentity = CORE_PRODUCT_IDENTITY,
    icon_root: Path | None = None,
) -> tuple[Path, ...]:
    """Return the bundled, hand-tuned application icon set for one product identity."""
    root = (
        Path(__file__).resolve().parents[3] / "data" / "icons" / "hicolor"
        if icon_root is None
        else icon_root
    )
    return tuple(
        root / size / "apps" / f"{identity.application_icon_name}.svg"
        for size in ("16x16", "24x24", "32x32", "48x48", "scalable")
    )


def _install_application_icon_identity(
    identity: ProductIdentity, icon_root: Path | None = None
) -> None:
    """Use the installed theme identity, with exact repo-local icons for source runs."""
    Gtk.Window.set_default_icon_name(identity.application_icon_name)
    paths = application_icon_paths(identity, icon_root)
    if not all(path.is_file() for path in paths):
        return
    try:
        icons = [GdkPixbuf.Pixbuf.new_from_file(str(path)) for path in paths]
    except (GLib.Error, OSError):
        return
    Gtk.Window.set_default_icon_list(icons)


class GraphiumApplication(Gtk.Application):
    def __init__(
        self,
        *,
        identity: ProductIdentity = CORE_PRODUCT_IDENTITY,
        window_factory=GraphiumWindow,
        icon_root: Path | None = None,
    ) -> None:
        super().__init__(
            application_id=identity.desktop_application_id,
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.product_identity = identity
        self._window_factory = window_factory
        self._icon_root = icon_root
        self.window: GraphiumWindow | None = None
        self.system_prefer_dark_theme = False

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        _install_application_icon_identity(self.product_identity, self._icon_root)
        settings = Gtk.Settings.get_default()
        if settings is not None:
            self.system_prefer_dark_theme = bool(
                settings.get_property("gtk-application-prefer-dark-theme")
            )
        for spec in COMMANDS:
            if spec.accelerator:
                self.set_accels_for_action(f"win.{spec.action}", [spec.accelerator])

    def _ensure_window(self) -> GraphiumWindow:
        if self.window is None:
            self.window = self._window_factory(self)
            self.window.connect("destroy", self._on_window_destroyed)
        return self.window

    def _on_window_destroyed(self, *_args) -> None:
        self.window = None

    def do_activate(self) -> None:
        window = self._ensure_window()
        window.begin_startup_open()
        window.show_all()
        window.present()
        try:
            window.offer_startup_recovery()
        finally:
            window.finish_startup_open()

    @staticmethod
    def _spawn_additional_paths(paths) -> None:
        launcher = Path(sys.argv[0]).resolve()
        for path in paths:
            if not path:
                continue
            subprocess.Popen(
                [str(launcher), str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )

    @classmethod
    def _spawn_additional_files(cls, files) -> None:
        cls._spawn_additional_paths(
            path for path in (gfile.get_path() for gfile in files) if path
        )

    def do_open(self, files, _n_files, _hint) -> None:
        window = self._ensure_window()
        first_path = files[0].get_path() if files else None
        window.begin_startup_open()
        window.show_all()
        window.present()
        try:
            startup = window.offer_startup_recovery(first_path)
            if first_path and not startup.recovered:
                window.open_path(first_path)
        finally:
            window.finish_startup_open()
        if len(files) > 1:
            self._spawn_additional_files(files[1:])
