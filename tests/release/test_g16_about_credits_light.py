from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class G16AboutCreditsLightTests(unittest.TestCase):
    def test_existing_appearance_authority_owns_dialog_viewport_view_in_both_explicit_modes(self):
        source = (ROOT / "graphium/adapters/gtk/appearance.py").read_text(encoding="utf-8")
        light = source[source.index("_LIGHT_CSS"):source.index("_DARK_CSS")]
        dark = source[source.index("_DARK_CSS"):source.index("class GtkAppearanceRenderer")]
        selector = "dialog viewport.view"
        self.assertIn(selector, light)
        self.assertIn(selector, dark)


    def test_treeview_selection_is_explicit_in_active_and_backdrop_states(self):
        source = (ROOT / "graphium/adapters/gtk/appearance.py").read_text(encoding="utf-8")
        light = source[source.index("_LIGHT_CSS"):source.index("_DARK_CSS")]
        dark = source[source.index("_DARK_CSS"):source.index("class GtkAppearanceRenderer")]
        for block in (light, dark):
            self.assertIn("treeview.view:selected", block)
            self.assertIn("treeview.view:selected:focus", block)
            self.assertIn("treeview.view:selected:backdrop", block)
            self.assertIn("background-image: none", block)
            self.assertIn("background-color: #3584e4", block)
            self.assertIn("color: #ffffff", block)

    def test_credits_fix_does_not_create_dialog_specific_styling_owner(self):
        dialogs = (ROOT / "graphium/adapters/gtk/dialogs.py").read_text(encoding="utf-8")
        for forbidden in (
            "CssProvider",
            "StyleContext.add_provider",
            "viewport.view",
            "set_name(\"credits",
            "get_children()[",
        ):
            self.assertNotIn(forbidden, dialogs)

    def test_credits_fix_adds_no_new_independent_palette_constants(self):
        source = (ROOT / "graphium/adapters/gtk/appearance.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"CREDITS_(?:LIGHT|DARK|BACKGROUND|FOREGROUND)")
        self.assertNotIn("ABOUT_CREDITS", source)

    def test_viewport_projection_uses_existing_light_and_dark_background_families(self):
        source = (ROOT / "graphium/adapters/gtk/appearance.py").read_text(encoding="utf-8")
        # The selector must join an existing background/color rule, not define a second palette.
        light = source[source.index("_LIGHT_CSS"):source.index("_DARK_CSS")]
        dark = source[source.index("_DARK_CSS"):source.index("class GtkAppearanceRenderer")]
        for block in (light, dark):
            self.assertRegex(
                block,
                r"textview, textview text, entry, spinbutton, treeview\.view, list, listbox, row,\s*\n?dialog viewport\.view\s*\{\s*\n?\s*background-color:",
            )


if __name__ == "__main__":
    unittest.main()
