from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.release._common import ROOT

GPL3_BODY_SHA256 = "0ae0485a5bd37a63e63603596417e4eb0e653334fa6c7f932ca3a0e85d4af227"
LICENSE_BODY_MARKER = "The full GNU General Public License version 3 follows.\n\n"
AUTHOR = "leviagravia@zohomail.eu"
COPYRIGHT = "Copyright © 2026 leviagravia"
LICENSE_ID = "GPL-3.0-or-later"
REPOSITORY_URL = "https://github.com/leviagravia/graphium"
REPOSITORY_LABEL = "Graphium repository"
NAME_NOTE = (
    "Crash recovery is a narrow safety mechanism, not a session manager. "
    "The name Graphium comes from Latin graphium, the stylus used to write on wax tablets: "
    "a simple tool for writing."
)


class HelpAboutLegalClosureTests(unittest.TestCase):
    def test_license_is_single_top_level_utf8_authority_with_or_later_grant(self):
        license_path = ROOT / "LICENSE"
        self.assertTrue(license_path.is_file())
        text = license_path.read_text(encoding="utf-8")
        self.assertIn("Graphium\nCopyright © 2026 leviagravia\n", text)
        normalized = " ".join(text.split())
        self.assertIn(
            "either version 3 of the License, or (at your option) any later version.",
            normalized,
        )
        self.assertIn("WITHOUT ANY WARRANTY", text)
        self.assertEqual(len(list(ROOT.glob("LICENSE*"))), 1)
        self.assertFalse((ROOT / "COPYING").exists())

    def test_license_contains_exact_mature_gplv3_body(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn(LICENSE_BODY_MARKER, text)
        body = text.split(LICENSE_BODY_MARKER, 1)[1].encode("utf-8")
        self.assertEqual(hashlib.sha256(body).hexdigest(), GPL3_BODY_SHA256)

    def test_product_metadata_is_exact_and_candidate_ready_version_is_serial(self):
        from graphium import product

        self.assertEqual(product.AUTHOR, AUTHOR)
        self.assertEqual(product.COPYRIGHT, COPYRIGHT)
        self.assertEqual(product.LICENSE_ID, LICENSE_ID)
        self.assertEqual(product.REPOSITORY_URL, REPOSITORY_URL)
        self.assertEqual(product.REPOSITORY_LABEL, REPOSITORY_LABEL)
        self.assertEqual(product.VERSION, "0.0.16")

    def test_about_uses_standard_metadata_and_keeps_support_information(self):
        source = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        self.assertIn("Gtk.AboutDialog", source)
        self.assertIn("dialog.set_authors([identity.author])", source)
        self.assertIn("dialog.set_copyright(identity.copyright)", source)
        self.assertIn("dialog.set_license_type(Gtk.License.GPL_3_0)", source)
        self.assertIn("dialog.set_website(identity.repository_url)", source)
        self.assertIn("dialog.set_website_label(identity.repository_label)", source)
        for marker in ("Python {sys.version_info.major}", "GTK {Gtk.get_major_version()}", "Display {backend}"):
            self.assertIn(marker, source)
        self.assertNotIn("Gtk.License.CUSTOM", source)
        self.assertNotIn("GPL_3_0_ONLY", source)

    def test_about_explicitly_projects_existing_application_icon_authority(self):
        source = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        self.assertIn("identity.application_icon_name", source)
        self.assertIn("Gtk.IconTheme.get_default()", source)
        self.assertIn("theme.has_icon(identity.application_icon_name)", source)
        self.assertIn("dialog.set_logo_icon_name(identity.application_icon_name)", source)
        self.assertIn("Gtk.Window.get_default_icon_list()", source)
        self.assertIn("icon.get_width() == 48 and icon.get_height() == 48", source)
        self.assertIn("dialog.set_logo(icon)", source)
        for forbidden in (
            ".svg",
            "image-missing",
            "GResource",
            "resource_register",
            "data/icons",
        ):
            self.assertNotIn(forbidden, source)

    def test_repository_is_retained_without_reachability_logic(self):
        product = (ROOT / "graphium/product.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        self.assertIn(REPOSITORY_URL, product)
        self.assertIn(REPOSITORY_LABEL, product)
        combined = product + dialogs
        for forbidden in ("urllib", "requests", "urlopen", "http.client", "socket"):
            self.assertNotIn(forbidden, combined)

    def test_installer_carries_license_once_into_private_root(self):
        with tempfile.TemporaryDirectory() as td:
            stage = Path(td) / "stage"
            stage.mkdir()
            subprocess.run(
                [sys.executable, str(ROOT / "bin/graphium-install"), "--prefix", "/usr", "--destdir", str(stage)],
                check=True,
            )
            installed = stage / "usr/lib/graphium/LICENSE"
            self.assertTrue(installed.is_file())
            self.assertEqual(installed.read_bytes(), (ROOT / "LICENSE").read_bytes())
            copies = [p for p in stage.rglob("*") if p.is_file() and p.name in {"LICENSE", "COPYING"}]
            self.assertEqual(copies, [installed])

    def test_user_guide_intro_is_natural_and_has_exact_one_sentence_name_note(self):
        guide = (ROOT / "docs/user/GRAPHIUM_USER_GUIDE.txt").read_text(encoding="utf-8")
        intro = guide.split("\n\n1. THE BASIC MODEL", 1)[0]
        self.assertNotIn("Graphium does not use\ntabs", intro)
        self.assertNotIn("Graphium does not use\r\ntabs", intro)
        self.assertIn(NAME_NOTE, intro)
        self.assertEqual(intro.count("The name Graphium comes from Latin graphium"), 1)
        self.assertNotIn("http://", intro)
        self.assertNotIn("https://", intro)

    def test_help_topology_is_unchanged_and_no_legal_menu_is_added(self):
        from graphium.application.commands import COMMANDS

        help_items = [(c.action, c.label) for c in COMMANDS if c.menu == "Help"]
        self.assertEqual(
            help_items,
            [("user-guide", "User Guide"), ("keyboard-shortcuts", "Keyboard Shortcuts"), ("about", "About")],
        )
        self.assertFalse(any(c.action in {"legal", "license", "diagnostics"} for c in COMMANDS))

    def test_g15_s4_shortcut_help_remains_authoritative(self):
        shortcuts = (ROOT / "docs/user/GRAPHIUM_KEYBOARD_SHORTCUTS.txt").read_text(encoding="utf-8")
        self.assertIn("Ctrl+U          Uppercase", shortcuts)
        self.assertIn("Ctrl+Shift+L    Lowercase", shortcuts)

    def test_no_new_legal_runtime_subsystem_or_process_boundary(self):
        dialogs = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        installer = (ROOT / "bin/graphium-install").read_text(encoding="utf-8")
        product_modules = {p.name for p in (ROOT / "graphium").glob("*.py")}
        self.assertNotIn("license.py", product_modules)
        self.assertNotIn("legal.py", product_modules)
        for marker in ("threading", "ThreadPoolExecutor", "subprocess", "urllib", "requests", "socket"):
            self.assertNotIn(marker, dialogs)
        self.assertNotIn("urllib", installer)
        self.assertNotIn("requests", installer)


if __name__ == "__main__":
    unittest.main()
