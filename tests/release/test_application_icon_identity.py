from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.release._common import ROOT

ICON_NAME = "io.github.leviagravia.Graphium"
ICON_ROOT = ROOT / "data" / "icons" / "hicolor"
EXPECTED_ICON_FILES = {
    "16x16/apps/io.github.leviagravia.Graphium.svg": "e25f48614b53f6bab1a40ef74b2b90daaee4c68868bd581238b3998d47d8a6cb",
    "24x24/apps/io.github.leviagravia.Graphium.svg": "9823311674bbb7f755009dc2370d2109e392fa92772a33d63713f81807b61498",
    "32x32/apps/io.github.leviagravia.Graphium.svg": "052067696b1e3f8f55f93ed2f94be45d5a361144ef232d2f7ba2030029b6695f",
    "48x48/apps/io.github.leviagravia.Graphium.svg": "5abfdb8dc6d148cc9b056e2887dac53d2495b6d0ee6ff82cd8dea0d729532a68",
    "scalable/apps/io.github.leviagravia.Graphium.svg": "e5711782c106c88da6b13fe05f5c464619d1c12d65323d578c774bf1a6491e06",
}


class ApplicationIconIdentityTests(unittest.TestCase):
    def test_product_icon_identity_is_application_id(self):
        from graphium import product

        self.assertEqual(product.APPLICATION_ICON_NAME, product.DESKTOP_APPLICATION_ID)
        self.assertEqual(product.APPLICATION_ICON_NAME, ICON_NAME)

    def test_runtime_icon_assets_are_exact_bounded_user_design(self):
        actual = {
            path.relative_to(ICON_ROOT).as_posix()
            for path in ICON_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, set(EXPECTED_ICON_FILES))
        for rel, expected_sha256 in EXPECTED_ICON_FILES.items():
            data = (ICON_ROOT / rel).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected_sha256, rel)
            text = data.decode("utf-8")
            self.assertIn("<svg", text)

    def test_desktop_entry_uses_stable_icon_name_not_path_or_generic_icon(self):
        desktop = (ROOT / "data" / f"{ICON_NAME}.desktop").read_text(encoding="utf-8")
        self.assertIn(f"Icon={ICON_NAME}\n", desktop)
        self.assertNotIn("Icon=accessories-text-editor", desktop)
        icon_line = next(line for line in desktop.splitlines() if line.startswith("Icon="))
        self.assertNotIn("/", icon_line.removeprefix("Icon="))

    def test_installer_projects_only_bounded_hicolor_icons(self):
        with tempfile.TemporaryDirectory() as td:
            stage = Path(td) / "stage"
            stage.mkdir()
            subprocess.run(
                [sys.executable, str(ROOT / "bin" / "graphium-install"), "--prefix", "/usr", "--destdir", str(stage)],
                check=True,
            )
            installed_root = stage / "usr" / "share" / "icons" / "hicolor"
            actual = {
                path.relative_to(installed_root).as_posix()
                for path in installed_root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual, set(EXPECTED_ICON_FILES))
            for rel, expected_sha256 in EXPECTED_ICON_FILES.items():
                data = (installed_root / rel).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected_sha256, rel)

    def test_gtk_adapter_has_one_local_fallback_without_resource_framework(self):
        source = (ROOT / "graphium" / "adapters" / "gtk" / "application.py").read_text(encoding="utf-8")
        self.assertIn("identity.application_icon_name", source)
        self.assertIn("Gtk.Window.set_default_icon_name(identity.application_icon_name)", source)
        self.assertIn("Gtk.Window.set_default_icon_list", source)
        self.assertIn("application_icon_paths", source)
        for forbidden in ("GResource", "resource_register", "gtk-update-icon-cache", "subprocess.run"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
