"""Bounded GTK3 appearance projection for Graphium.

Graphium owns exactly three semantic modes: System, Light and Dark. System removes
Graphium's explicit palette and restores the GTK baseline captured at process startup.
Light and Dark use one process-local application CSS provider so their visible meaning
does not depend on whether the desktop theme itself is currently light or dark.
"""
from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from graphium.application.view_settings import (
    APPEARANCE_DARK,
    APPEARANCE_LIGHT,
    APPEARANCE_SYSTEM,
    APPEARANCE_VALUES,
)


_LIGHT_CSS = b"""
window, dialog, messagedialog, .background, menu, popover,
menubar, toolbar, searchbar {
  background-color: #f6f5f4;
  color: #202020;
}
menuitem, modelbutton, label, checkbutton, radiobutton {
  color: #202020;
}
textview, textview text, entry, spinbutton, treeview.view, list, listbox, row,
dialog viewport.view {
  background-color: #ffffff;
  color: #202020;
}
button {
  background-image: none;
  background-color: #e9e7e5;
  color: #202020;
  border-color: #b8b8b8;
}
button:hover { background-color: #deddda; }
button:disabled, entry:disabled, spinbutton:disabled { color: #77767b; }
*:selected {
  background-color: #3584e4;
  color: #ffffff;
}
treeview.view:selected,
treeview.view:selected:focus,
treeview.view:selected:backdrop,
treeview.view:backdrop:selected {
  background-image: none;
  background-color: #3584e4;
  color: #ffffff;
}
tooltip {
  background-color: #202020;
  color: #ffffff;
}
"""

_DARK_CSS = b"""
window, dialog, messagedialog, .background, menu, popover,
menubar, toolbar, searchbar {
  background-color: #242424;
  color: #f6f5f4;
}
menuitem, modelbutton, label, checkbutton, radiobutton {
  color: #f6f5f4;
}
textview, textview text, entry, spinbutton, treeview.view, list, listbox, row,
dialog viewport.view {
  background-color: #1e1e1e;
  color: #f6f5f4;
}
button {
  background-image: none;
  background-color: #383838;
  color: #f6f5f4;
  border-color: #5e5c64;
}
button:hover { background-color: #4a4a4a; }
button:disabled, entry:disabled, spinbutton:disabled { color: #9a9996; }
*:selected {
  background-color: #3584e4;
  color: #ffffff;
}
treeview.view:selected,
treeview.view:selected:focus,
treeview.view:selected:backdrop,
treeview.view:backdrop:selected {
  background-image: none;
  background-color: #3584e4;
  color: #ffffff;
}
tooltip {
  background-color: #f6f5f4;
  color: #202020;
}
"""


class GtkAppearanceRenderer:
    """Single owner of Graphium's explicit GTK3 Light/Dark projection."""

    __slots__ = (
        "_settings",
        "_screen",
        "_system_prefer_dark_theme",
        "_provider",
        "_provider_installed",
        "_mode",
    )

    def __init__(self, settings, screen, *, system_prefer_dark_theme: bool) -> None:
        self._settings = settings
        self._screen = screen
        self._system_prefer_dark_theme = bool(system_prefer_dark_theme)
        self._provider = None
        self._provider_installed = False
        self._mode = APPEARANCE_SYSTEM

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def explicit_projection_active(self) -> bool:
        return self._provider_installed

    def _remove_provider(self) -> None:
        if self._provider_installed and self._provider is not None and self._screen is not None:
            Gtk.StyleContext.remove_provider_for_screen(self._screen, self._provider)
        self._provider = None
        self._provider_installed = False

    def apply(self, value: str) -> None:
        if value not in APPEARANCE_VALUES:
            raise ValueError(f"unsupported appearance: {value!r}")
        if self._settings is None:
            if value == APPEARANCE_SYSTEM:
                self._remove_provider()
                self._mode = value
                return
            raise RuntimeError("GTK settings are unavailable")

        if value == APPEARANCE_SYSTEM:
            old_provider = self._provider
            old_installed = self._provider_installed
            try:
                self._remove_provider()
                self._settings.set_property(
                    "gtk-application-prefer-dark-theme", self._system_prefer_dark_theme
                )
            except Exception:
                if old_installed and old_provider is not None and self._screen is not None:
                    Gtk.StyleContext.add_provider_for_screen(
                        self._screen, old_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )
                    self._provider = old_provider
                    self._provider_installed = True
                raise
            self._mode = value
            return

        if self._screen is None:
            raise RuntimeError("GTK screen is unavailable")

        css = _DARK_CSS if value == APPEARANCE_DARK else _LIGHT_CSS
        candidate = Gtk.CssProvider()
        candidate.load_from_data(css)
        prefer_dark = value == APPEARANCE_DARK

        old_provider = self._provider
        old_installed = self._provider_installed
        old_prefer_dark = bool(
            self._settings.get_property("gtk-application-prefer-dark-theme")
        )
        Gtk.StyleContext.add_provider_for_screen(
            self._screen, candidate, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        try:
            self._settings.set_property("gtk-application-prefer-dark-theme", prefer_dark)
        except Exception:
            Gtk.StyleContext.remove_provider_for_screen(self._screen, candidate)
            self._settings.set_property("gtk-application-prefer-dark-theme", old_prefer_dark)
            raise

        if old_installed and old_provider is not None:
            Gtk.StyleContext.remove_provider_for_screen(self._screen, old_provider)
        self._provider = candidate
        self._provider_installed = True
        self._mode = value

    def close(self) -> None:
        self._remove_provider()
