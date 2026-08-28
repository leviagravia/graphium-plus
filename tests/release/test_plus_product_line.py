from __future__ import annotations

import ast
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from graphium.paths import resolve_xdg_paths
from graphium.product import CORE_PRODUCT_IDENTITY
from graphium_plus.product import PLUS_PRODUCT_IDENTITY
from tests.release._common import ROOT, imports


class PlusProductLineTests(unittest.TestCase):
    def test_core_defaults_and_plus_identity_are_separate(self):
        self.assertEqual(CORE_PRODUCT_IDENTITY.product_name, "Graphium")
        self.assertEqual(CORE_PRODUCT_IDENTITY.xdg_namespace, "graphium")
        self.assertEqual(PLUS_PRODUCT_IDENTITY.product_name, "Graphium Plus")
        self.assertEqual(PLUS_PRODUCT_IDENTITY.executable_name, "graphium-plus")
        self.assertEqual(
            PLUS_PRODUCT_IDENTITY.desktop_application_id,
            "io.github.leviagravia.GraphiumPlus",
        )
        self.assertEqual(PLUS_PRODUCT_IDENTITY.xdg_namespace, "graphium-plus")
        self.assertEqual(
            PLUS_PRODUCT_IDENTITY.repository_url,
            "https://github.com/leviagravia/graphium-plus",
        )
        self.assertEqual(PLUS_PRODUCT_IDENTITY.version, "0.0.1")
        self.assertEqual(PLUS_PRODUCT_IDENTITY.author, CORE_PRODUCT_IDENTITY.author)
        self.assertEqual(PLUS_PRODUCT_IDENTITY.copyright, CORE_PRODUCT_IDENTITY.copyright)
        self.assertEqual(PLUS_PRODUCT_IDENTITY.license_id, CORE_PRODUCT_IDENTITY.license_id)
        core = resolve_xdg_paths({"HOME": "/tmp/home"})
        plus = resolve_xdg_paths({"HOME": "/tmp/home"}, namespace="graphium-plus")
        self.assertNotEqual(core, plus)

    def test_core_never_imports_plus(self):
        bad = []
        for path in (ROOT / "graphium").rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            for imported in imports(rel):
                if imported == "graphium_plus" or imported.startswith("graphium_plus."):
                    bad.append((rel, imported))
        self.assertEqual(bad, [])

    def test_plus_composes_core_without_duplicate_document_authorities(self):
        forbidden = {
            "DocumentSession",
            "GuardedFileWriter",
            "FileLifecycleController",
            "NativeEditorController",
        }
        offenders = []
        for path in (ROOT / "graphium_plus").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id in forbidden:
                    offenders.append((path.name, node.id))
        self.assertEqual(offenders, [])
        plus_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "graphium_plus").rglob("*.py")
        )
        for forbidden in ("threading", "ThreadPoolExecutor", "subprocess.Popen", "monitor_file(", "monitor_directory("):
            self.assertNotIn(forbidden, plus_source)

    def test_toolbar_is_a_projection_of_canonical_window_actions(self):
        source = (ROOT / "graphium_plus/adapters/gtk/window.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assign = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "_TOOLBAR_LAYOUT" for t in node.targets)
        )
        layout = ast.literal_eval(assign.value)
        self.assertEqual(
            layout,
            (
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
            ),
        )
        self.assertIn('button.set_action_name(f"win.{action}")', source)
        self.assertIn('"toolbar-visible"', source)
        self.assertIn('menu_item.set_action_name("win.toolbar-visible")', source)
        self.assertIn('"ShowItems" if selected is not None else "ShowFolders"', source)
        self.assertIn('org.freedesktop.FileManager1', source)
        self.assertIn('on_open_in_graphium=self._open_workspace_text_item', source)
        panel_source = (ROOT / "graphium_plus/adapters/gtk/workspace_panel.py").read_text(encoding="utf-8")
        self.assertIn('"Open with Graphium Plus"', panel_source)
        self.assertIn('self.tree.connect("button-press-event", self._tree_button_press)', panel_source)
        self.assertIn('if item.text_document:', panel_source)
        self.assertIn('self._on_open_in_graphium(item)', panel_source)
        toolbar_builder = next(
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_build_toolbar"
        )
        toolbar_source = ast.get_source_segment(source, toolbar_builder) or ""
        self.assertNotRegex(toolbar_source, r'connect\s*\(\s*["\'](?:clicked|activate)["\']')

    def test_plus_user_guide_matches_final_toolbar_and_workspace_contract(self):
        guide = (ROOT / "docs/user/GRAPHIUM_PLUS_USER_GUIDE.txt").read_text(encoding="utf-8")
        for marker in (
            "22. COMPACT TOOLBAR — GRAPHIUM PLUS",
            "New, Open, Save, Undo, Redo, Cut, Copy, Paste, Reload, Find and Replace",
            "View -> Toolbar",
            "23. WORKSPACE — GRAPHIUM PLUS",
            "A single click selects a row; it does not open the file.",
            "Double-click or Enter on a regular .txt",
            "Open with Graphium Plus",
            "chapter2.txt sorts before chapter10.txt",
            "selected Workspace row remains visibly highlighted",
            "surviving selected relative path",
            "org.freedesktop.FileManager1.ShowItems",
            "Partial-view diagnostics",
        ):
            self.assertIn(marker, guide)
        self.assertNotIn("15. WORKSPACE — GRAPHIUM PLUS", guide)
        self.assertNotIn("14. WORKSPACE REVEAL", guide)
        self.assertNotIn("Graphium adds no toolbar", guide)
        headings = [int(value) for value in re.findall(r"(?m)^(\d+)\. ", guide)]
        self.assertEqual(headings, list(range(1, 24)))
        plus_window = (ROOT / "graphium_plus/adapters/gtk/window.py").read_text(encoding="utf-8")
        self.assertIn('path=self._help_path("GRAPHIUM_PLUS_USER_GUIDE.txt")', plus_window)
        self.assertIn('title="Graphium Plus User Guide"', plus_window)

    def test_plus_launcher_is_repo_relative_and_executable(self):
        launcher = ROOT / "bin/graphium-plus"
        installer = ROOT / "bin/graphium-plus-install"
        for executable in (launcher, installer):
            self.assertTrue(executable.is_file())
            self.assertTrue(executable.stat().st_mode & stat.S_IXUSR)
            self.assertNotIn("/home/", executable.read_text(encoding="utf-8"))
        source = launcher.read_text(encoding="utf-8")
        self.assertIn("__file__", source)
        self.assertIn("GraphiumPlusApplication", source)

        desktop_source = ROOT / "graphium_plus/data/io.github.leviagravia.GraphiumPlus.desktop"
        guide_source = ROOT / "docs/user/GRAPHIUM_PLUS_USER_GUIDE.txt"
        self.assertTrue(desktop_source.is_file())
        self.assertTrue(guide_source.is_file())
        with tempfile.TemporaryDirectory() as td:
            stage = Path(td) / "stage"
            stage.mkdir()
            subprocess.run(
                [sys.executable, str(installer), "--prefix", "/usr", "--destdir", str(stage)],
                check=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            prefix = stage / "usr"
            private = prefix / "lib/graphium-plus"
            public = prefix / "bin/graphium-plus"
            self.assertTrue(public.is_symlink())
            self.assertEqual(public.readlink(), Path("../lib/graphium-plus/bin/graphium-plus"))
            self.assertTrue((private / "graphium").is_dir())
            self.assertTrue((private / "graphium_plus").is_dir())
            self.assertTrue((private / "docs/user/GRAPHIUM_PLUS_USER_GUIDE.txt").is_file())
            desktop = (prefix / "share/applications/io.github.leviagravia.GraphiumPlus.desktop").read_text(encoding="utf-8")
            for marker in (
                "Name=Graphium Plus",
                "Exec=graphium-plus %F",
                "Icon=io.github.leviagravia.GraphiumPlus",
                "Terminal=false",
            ):
                self.assertIn(marker, desktop)
            for size in ("16x16", "24x24", "32x32", "48x48", "scalable"):
                self.assertTrue(
                    (prefix / "share/icons/hicolor" / size / "apps/io.github.leviagravia.GraphiumPlus.svg").is_file()
                )
            self.assertFalse((private / "tests").exists())
            self.assertFalse((private / "evidence").exists())

            home = Path(td) / "home with space"
            home.mkdir()
            subprocess.run(
                [sys.executable, str(installer)],
                check=True,
                env={**os.environ, "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertTrue((home / ".local/bin/graphium-plus").is_symlink())

    def test_plus_icons_preserve_core_geometry_and_change_only_red_palette(self):
        core_root = ROOT / "data/icons/hicolor"
        plus_root = ROOT / "graphium_plus/data/icons/hicolor"
        core_name = "io.github.leviagravia.Graphium.svg"
        plus_name = "io.github.leviagravia.GraphiumPlus.svg"
        for size in ("16x16", "24x24", "32x32", "48x48", "scalable"):
            core = (core_root / size / "apps" / core_name).read_text(encoding="utf-8")
            plus = (plus_root / size / "apps" / plus_name).read_text(encoding="utf-8")
            restored = plus.replace("#B51F31", "#18232E").replace("#E0707C", "#6B7C8F")
            self.assertEqual(restored, core, size)
            self.assertIn("#B51F31", plus)
            self.assertNotIn("#18232E", plus)


if __name__ == "__main__":
    unittest.main()
