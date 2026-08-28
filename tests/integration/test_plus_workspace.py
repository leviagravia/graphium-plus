from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from graphium_plus.workspace.controller import WorkspaceController
from graphium_plus.workspace.gio import WorkspaceGioAdapter
from graphium_plus.workspace.model import WorkspaceError, normalize_root, scan_directory
from graphium_plus.workspace.operations import plan_new_folder, plan_new_text_file, workspace_path_token
from graphium_plus.workspace.state import RECENT_LIMIT, RecentWorkspaces


class PlusWorkspaceTests(unittest.TestCase):
    def test_one_directory_loading_is_lazy_sorted_and_hidden_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "zeta.txt").write_text("z", encoding="utf-8")
            (root / "chapter10.txt").write_text("10", encoding="utf-8")
            (root / "chapter2.txt").write_text("2", encoding="utf-8")
            (root / "Alpha.md").write_text("a", encoding="utf-8")
            (root / ".hidden.txt").write_text("h", encoding="utf-8")
            nested = root / "Folder"
            nested.mkdir()
            (nested / "deep.md").write_text("deep", encoding="utf-8")
            controller = WorkspaceController()
            listing = controller.bind_root(str(root))
            self.assertEqual(
                [item.name for item in listing.items],
                ["Folder", "Alpha.md", "chapter2.txt", "chapter10.txt", "zeta.txt"],
            )
            folder = listing.items[0]
            loaded = controller.load_directory(folder)
            self.assertEqual([item.name for item in loaded.items], ["deep.md"])
            self.assertTrue(loaded.items[0].text_document)
            self.assertEqual(
                controller.relative_path_for_document(str(nested / "deep.md")),
                os.path.join("Folder", "deep.md"),
            )
            with self.assertRaises(WorkspaceError):
                controller.relative_path_for_document(str(Path(tmp).parent / "outside.md"))

    def test_root_transition_stale_items_and_symlinks_fail_closed(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "first"; first.mkdir()
            second = base / "second"; second.mkdir()
            (first / "doc.md").write_text("one", encoding="utf-8")
            (first / "dir").mkdir()
            outside = base / "outside"; outside.mkdir()
            (first / "link").symlink_to(outside, target_is_directory=True)
            controller = WorkspaceController()
            first_listing = controller.bind_root(str(first))
            old_doc = next(item for item in first_listing.items if item.name == "doc.md")
            link = next(item for item in first_listing.items if item.name == "link")
            self.assertTrue(link.is_symlink)
            self.assertEqual(controller.activation_for(link).kind, "blocked")
            with self.assertRaises(WorkspaceError):
                controller.load_directory(link)
            previous_root = controller.root
            with self.assertRaises(WorkspaceError):
                controller.bind_root(str(first / "missing"))
            self.assertEqual(controller.root, previous_root)
            controller.bind_root(str(second))
            with self.assertRaises(WorkspaceError):
                controller.activation_for(old_doc)
            root_link = base / "root-link"
            root_link.symlink_to(first, target_is_directory=True)
            with self.assertRaises(WorkspaceError):
                normalize_root(str(root_link))

    def test_refresh_invalidates_old_items_and_activation_rechecks_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "doc.md"
            other = root / "image.bin"
            doc.write_text("a", encoding="utf-8")
            other.write_bytes(b"x")
            controller = WorkspaceController()
            listing = controller.bind_root(str(root))
            doc_item = next(item for item in listing.items if item.name == "doc.md")
            other_item = next(item for item in listing.items if item.name == "image.bin")
            self.assertEqual(controller.activation_for(doc_item).kind, "internal")
            self.assertEqual(controller.activation_for(other_item).kind, "external")
            fresh_listing = controller.refresh()
            with self.assertRaises(WorkspaceError):
                controller.activation_for(doc_item)
            fresh = next(item for item in fresh_listing.items if item.name == "doc.md")
            doc.unlink()
            self.assertEqual(controller.activation_for(fresh).kind, "missing")

    def test_recent_workspaces_are_atomic_bounded_and_do_not_persist_active_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            state = RecentWorkspaces(base / "state" / "recent-workspaces.json")
            roots = []
            for index in range(RECENT_LIMIT + 2):
                root = base / f"root-{index}"
                root.mkdir()
                roots.append(str(root))
                state.touch(str(root))
            visible = state.paths()
            self.assertEqual(len(visible), RECENT_LIMIT)
            self.assertEqual(visible[0], os.path.abspath(roots[-1]))
            payload = json.loads(state.path.read_text(encoding="utf-8"))
            self.assertEqual(set(payload), {"schema", "recent_roots"})
            self.assertNotIn("root", payload)
            Path(visible[0]).rmdir()
            self.assertNotIn(visible[0], state.paths())
            leftovers = list(state.path.parent.glob("*.tmp"))
            self.assertEqual(leftovers, [])

    def test_creation_plans_are_single_basename_confined_and_text_suffix_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "nested"; nested.mkdir()
            text = plan_new_text_file(str(root), str(nested), "Chapter_1", suffix=".md")
            self.assertEqual((text.kind, text.display_name, text.target_path), ("new-text-file", "Chapter_1.md", str(nested / "Chapter_1.md")))
            folder = plan_new_folder(str(root), str(nested), "Drafts")
            self.assertEqual((folder.kind, folder.display_name, folder.target_path), ("new-folder", "Drafts", str(nested / "Drafts")))
            for bad in ("../escape", ".hidden", "wrong.pdf"):
                with self.subTest(bad=bad):
                    with self.assertRaises(WorkspaceError):
                        plan_new_text_file(str(root), str(nested), bad, suffix=".txt")
            for bad in ("../escape", ".hidden"):
                with self.subTest(folder=bad):
                    with self.assertRaises(WorkspaceError):
                        plan_new_folder(str(root), str(nested), bad)

    def test_creation_destination_is_current_selection_or_its_parent_and_stale_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Folder"; folder.mkdir()
            doc = folder / "doc.md"; doc.write_text("x", encoding="utf-8")
            controller = WorkspaceController()
            root_listing = controller.bind_root(str(root))
            folder_item = next(item for item in root_listing.items if item.name == "Folder")
            self.assertEqual(controller.creation_parent(None), str(root))
            self.assertEqual(controller.creation_parent(folder_item), str(folder))
            nested_listing = controller.load_directory(folder_item)
            doc_item = next(item for item in nested_listing.items if item.name == "doc.md")
            self.assertEqual(controller.creation_parent(doc_item), str(folder))
            controller.refresh()
            with self.assertRaises(WorkspaceError):
                controller.creation_parent(doc_item)

    def test_scanner_is_one_level_and_does_not_need_global_item_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "nested"; nested.mkdir()
            for index in range(25):
                (nested / f"file-{index}.txt").write_text("x", encoding="utf-8")
            listing = scan_directory(str(root), str(root), generation=1)
            self.assertEqual([item.name for item in listing.items], ["nested"])
            self.assertFalse(any("max" in diagnostic.lower() for diagnostic in listing.diagnostics))

    def test_safe_rename_plan_is_current_confined_identity_bound_and_blocks_active_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Folder"; folder.mkdir()
            child = folder / "child.md"; child.write_text("x", encoding="utf-8")
            sibling = root / "draft.md"; sibling.write_text("draft", encoding="utf-8")
            controller = WorkspaceController()
            listing = controller.bind_root(str(root))
            folder_item = next(item for item in listing.items if item.name == "Folder")
            sibling_item = next(item for item in listing.items if item.name == "draft.md")

            plan = controller.plan_rename(sibling_item, "chapter.md", active_document_path=str(child))
            self.assertEqual((plan.source_path, plan.target_path), (str(sibling), str(root / "chapter.md")))
            observed = os.lstat(sibling)
            self.assertEqual(plan.source_token, workspace_path_token(observed))
            self.assertEqual(
                (
                    plan.source_token.device, plan.source_token.inode, plan.source_token.mode,
                    plan.source_token.size, plan.source_token.mtime_ns, plan.source_token.ctime_ns,
                    plan.source_token.uid, plan.source_token.gid, plan.source_token.nlink,
                ),
                (
                    observed.st_dev, observed.st_ino, observed.st_mode, observed.st_size,
                    observed.st_mtime_ns, observed.st_ctime_ns, observed.st_uid, observed.st_gid,
                    observed.st_nlink,
                ),
            )
            adapter = WorkspaceGioAdapter()
            pinned_fd = adapter._open_pinned_source(plan)
            self.assertIsNotNone(pinned_fd)
            os.close(pinned_fd)
            sibling.unlink()
            sibling.write_text("replacement", encoding="utf-8")
            self.assertNotEqual(plan.source_token, workspace_path_token(os.lstat(sibling)))
            self.assertIsNone(adapter._open_pinned_source(plan))

            # Restore a current item for the remaining planner fences.
            listing = controller.refresh()
            sibling_item = next(item for item in listing.items if item.name == "draft.md")

            with self.assertRaises(WorkspaceError):
                controller.plan_rename(sibling_item, "renamed.md", active_document_path=str(sibling))
            with self.assertRaises(WorkspaceError):
                controller.plan_rename(folder_item, "RenamedFolder", active_document_path=str(child))
            with self.assertRaises(WorkspaceError):
                controller.plan_rename(sibling_item, "../escape", active_document_path=str(child))
            with self.assertRaises(WorkspaceError):
                controller.plan_rename(sibling_item, "draft.md", active_document_path=str(child))
            controller.refresh()
            with self.assertRaises(WorkspaceError):
                controller.plan_rename(sibling_item, "stale.md", active_document_path=str(child))


    def test_system_trash_plan_is_strongly_pinned_confined_and_blocks_active_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Folder"; folder.mkdir()
            child = folder / "child.md"; child.write_text("child", encoding="utf-8")
            victim = root / "victim.md"; victim.write_text("victim", encoding="utf-8")
            link = root / "link.md"
            if hasattr(os, "symlink"):
                link.symlink_to(victim)

            controller = WorkspaceController()
            listing = controller.bind_root(str(root))
            victim_item = next(item for item in listing.items if item.name == "victim.md")
            folder_item = next(item for item in listing.items if item.name == "Folder")
            plan = controller.plan_trash(victim_item, active_document_path=str(child))
            self.assertEqual((plan.source_path, plan.parent_path), (str(victim), str(root)))
            self.assertEqual(plan.source_token, workspace_path_token(os.lstat(victim)))

            adapter = WorkspaceGioAdapter()
            pinned_fd = adapter._open_pinned_source(plan)
            self.assertIsNotNone(pinned_fd)
            os.close(pinned_fd)
            victim.unlink()
            victim.write_text("replacement", encoding="utf-8")
            self.assertIsNone(adapter._open_pinned_source(plan))

            listing = controller.refresh()
            victim_item = next(item for item in listing.items if item.name == "victim.md")
            folder_item = next(item for item in listing.items if item.name == "Folder")
            with self.assertRaises(WorkspaceError):
                controller.plan_trash(victim_item, active_document_path=str(victim))
            with self.assertRaises(WorkspaceError):
                controller.plan_trash(folder_item, active_document_path=str(child))
            if hasattr(os, "symlink"):
                link_item = next(item for item in listing.items if item.name == "link.md")
                with self.assertRaises(WorkspaceError):
                    controller.plan_trash(link_item, active_document_path=str(child))
            controller.refresh()
            with self.assertRaises(WorkspaceError):
                controller.plan_trash(victim_item, active_document_path=str(child))

    def test_verified_duplicate_uses_saved_disk_bytes_no_overwrite_and_strong_stale_fence(self):
        if not hasattr(os, "link"):
            self.skipTest("hard-link commit unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "draft.md"
            source.write_bytes(b"saved bytes\n")
            (root / "draft copy.md").write_bytes(b"occupied")
            folder = root / "Folder"; folder.mkdir()
            link = root / "link.md"
            if hasattr(os, "symlink"):
                link.symlink_to(source)

            controller = WorkspaceController()
            listing = controller.bind_root(str(root))
            source_item = next(item for item in listing.items if item.name == "draft.md")
            plan = controller.plan_duplicate(source_item)
            self.assertEqual(plan.target_path, str(root / "draft copy 2.md"))
            before_source = source.read_bytes()

            adapter = WorkspaceGioAdapter()
            result = adapter.duplicate(plan)
            self.assertTrue(result.success, result.message)
            target = Path(result.path)
            self.assertEqual(target.read_bytes(), before_source)
            self.assertEqual(source.read_bytes(), before_source)
            self.assertFalse(any(path.name.startswith(".graphium-plus-duplicate-") for path in root.iterdir()))

            # No-overwrite is commit-time, not just name-planning evidence.
            listing = controller.refresh()
            source_item = next(item for item in listing.items if item.name == "draft.md")
            collision_plan = controller.plan_duplicate(source_item)
            collision_target = Path(collision_plan.target_path)
            collision_target.write_bytes(b"racer")
            collision = adapter.duplicate(collision_plan)
            self.assertFalse(collision.success)
            self.assertEqual(collision_target.read_bytes(), b"racer")

            # Replacement after planning must never acquire source authority.
            collision_target.unlink()
            listing = controller.refresh()
            source_item = next(item for item in listing.items if item.name == "draft.md")
            stale_plan = controller.plan_duplicate(source_item)
            source.unlink()
            source.write_bytes(b"replacement")
            stale = adapter.duplicate(stale_plan)
            self.assertFalse(stale.success)
            self.assertFalse(Path(stale_plan.target_path).exists())
            self.assertEqual(source.read_bytes(), b"replacement")

            listing = controller.refresh()
            folder_item = next(item for item in listing.items if item.name == "Folder")
            with self.assertRaises(WorkspaceError):
                controller.plan_duplicate(folder_item)
            if hasattr(os, "symlink"):
                link_item = next(item for item in listing.items if item.name == "link.md")
                with self.assertRaises(WorkspaceError):
                    controller.plan_duplicate(link_item)


if __name__ == "__main__":
    unittest.main()
