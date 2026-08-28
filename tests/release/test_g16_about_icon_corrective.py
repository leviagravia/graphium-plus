from __future__ import annotations

import unittest
from pathlib import Path

from tests.release._common import ROOT


class G16AboutIconCorrectiveTests(unittest.TestCase):
    def test_about_uses_existing_identity_not_an_about_asset(self):
        source = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        self.assertIn("identity.application_icon_name", source)
        self.assertIn("dialog.set_logo_icon_name(identity.application_icon_name)", source)
        self.assertIn("Gtk.Window.get_default_icon_list()", source)
        self.assertIn("dialog.set_logo(icon)", source)
        for forbidden in (".svg", "data/icons", "about.svg", "about-icon", "image-missing"):
            self.assertNotIn(forbidden, source)

    def test_source_fallback_is_exact_48_square(self):
        source = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        self.assertIn("icon.get_width() == 48 and icon.get_height() == 48", source)
        self.assertNotIn("== 16", source)

    def test_existing_hicolor_asset_set_is_unchanged_and_bounded(self):
        root = ROOT / "data/icons/hicolor"
        files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.svg"))
        self.assertEqual(files, [
            "16x16/apps/io.github.leviagravia.Graphium.svg",
            "24x24/apps/io.github.leviagravia.Graphium.svg",
            "32x32/apps/io.github.leviagravia.Graphium.svg",
            "48x48/apps/io.github.leviagravia.Graphium.svg",
            "scalable/apps/io.github.leviagravia.Graphium.svg",
        ])

    def test_no_new_resource_dependency_or_module(self):
        source = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        for forbidden in ("GResource", "resource_register", "importlib.resources", "subprocess", "threading"):
            self.assertNotIn(forbidden, source)
        self.assertFalse((ROOT / "graphium/adapters/gtk/about_icon.py").exists())

    def test_candidate_ready_version_is_serial_0_0_16(self):
        from graphium.product import VERSION
        self.assertEqual(VERSION, "0.0.16")


if __name__ == "__main__":
    unittest.main()
