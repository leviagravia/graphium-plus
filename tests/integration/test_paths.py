from __future__ import annotations
from pathlib import Path
import unittest
from graphium.paths import resolve_xdg_paths

class XdgPathTests(unittest.TestCase):

    def test_default_graphium_paths_are_product_isolated(self):
        got = resolve_xdg_paths({'HOME': '/home/tester'})
        self.assertEqual(got.config, Path('/home/tester/.config/graphium'))
        self.assertEqual(got.data, Path('/home/tester/.local/share/graphium'))
        self.assertEqual(got.cache, Path('/home/tester/.cache/graphium'))
        self.assertEqual(got.state, Path('/home/tester/.local/state/graphium'))

    def test_explicit_xdg_roots_are_respected(self):
        got = resolve_xdg_paths({'HOME': '/home/tester', 'XDG_CONFIG_HOME': '/tmp/cfg', 'XDG_DATA_HOME': '/tmp/data', 'XDG_CACHE_HOME': '/tmp/cache', 'XDG_STATE_HOME': '/tmp/state'})
        self.assertEqual(got.config, Path('/tmp/cfg/graphium'))
        self.assertEqual(got.data, Path('/tmp/data/graphium'))
        self.assertEqual(got.cache, Path('/tmp/cache/graphium'))
        self.assertEqual(got.state, Path('/tmp/state/graphium'))

    def test_explicit_product_namespace_is_isolated(self):
        got = resolve_xdg_paths({'HOME': '/home/tester'}, namespace='graphium-plus')
        self.assertEqual(got.config, Path('/home/tester/.config/graphium-plus'))
        self.assertEqual(got.data, Path('/home/tester/.local/share/graphium-plus'))
        self.assertEqual(got.cache, Path('/home/tester/.cache/graphium-plus'))
        self.assertEqual(got.state, Path('/home/tester/.local/state/graphium-plus'))

    def test_missing_home_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_xdg_paths({})
if __name__ == '__main__':
    unittest.main()
