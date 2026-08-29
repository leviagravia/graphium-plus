from __future__ import annotations
import ctypes
import errno
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from graphium.domain.document_save import GuardedWriteError, SaveDisposition, SaveTargetExpectation, StaleSaveTargetError, UnsafeSaveTargetError
from graphium.infrastructure.document_loader import load_document
import graphium.infrastructure.guarded_file_writer as guarded_writer_module
from graphium.infrastructure.guarded_file_writer import GuardedFileWriter
class GuardedWriterTests(unittest.TestCase):
    def _write(self, path: Path, data: bytes, mode: int=420) -> None:
        path.write_bytes(data)
        path.chmod(mode)
    def test_observe_absent_target_captures_parent_without_creation(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            obs = GuardedFileWriter().observe_target(str(target))
            self.assertEqual(obs.expectation, SaveTargetExpectation.EXPECTED_ABSENT)
            self.assertFalse(target.exists())
            self.assertIsNone(obs.existing)
    def test_observe_existing_matches_accepted_file_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'A\n')
            accepted = load_document(str(target)).file_state
            obs = GuardedFileWriter().observe_target(str(target), expected_file_state=accepted)
            self.assertEqual(obs.expectation, SaveTargetExpectation.EXPECTED_EXISTING)
            self.assertEqual(obs.existing.object_id, accepted.binding.object_id)
            self.assertEqual(obs.existing.content_fingerprint, accepted.content_fingerprint)
    def test_same_size_same_mtime_different_bytes_is_stale(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'AAAA')
            accepted = load_document(str(target)).file_state
            old_mtime = target.stat().st_mtime_ns
            target.write_bytes(b'BBBB')
            os.utime(target, ns=(old_mtime, old_mtime))
            with self.assertRaises(StaleSaveTargetError):
                GuardedFileWriter().observe_target(str(target), expected_file_state=accepted)
    def test_inode_replacement_is_stale_even_with_same_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'A\n')
            accepted = load_document(str(target)).file_state
            replacement = Path(td) / 'replacement'
            self._write(replacement, b'A\n')
            os.replace(replacement, target)
            with self.assertRaises(StaleSaveTargetError):
                GuardedFileWriter().observe_target(str(target), expected_file_state=accepted)
    @unittest.skipUnless(hasattr(os, 'link'), 'hardlinks required')
    def test_hardlinked_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            alias = Path(td) / 'alias.txt'
            self._write(target, b'A\n')
            os.link(target, alias)
            with self.assertRaises(UnsafeSaveTargetError):
                GuardedFileWriter().observe_target(str(target))
            self.assertEqual(target.read_bytes(), b'A\n')
            self.assertEqual(alias.read_bytes(), b'A\n')
    def test_read_only_existing_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'A\n', 292)
            with self.assertRaises(UnsafeSaveTargetError):
                GuardedFileWriter().observe_target(str(target))
    def test_existing_commit_replaces_bytes_and_preserves_mode(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n', 416)
            accepted = load_document(str(target)).file_state
            writer = GuardedFileWriter()
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            result = writer.commit(obs, b'new\n')
            self.assertEqual(target.read_bytes(), b'new\n')
            self.assertEqual(target.stat().st_mode & 511, 416)
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_CONFIRMED)
            self.assertEqual(result.committed_fingerprint.hex_digest, hashlib.sha256(b'new\n').hexdigest())
    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks required')
    def test_save_through_symlink_preserves_link_and_updates_physical_target(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'physical.txt'
            link = Path(td) / 'logical.txt'
            self._write(target, b'old\n')
            link.symlink_to(target.name)
            accepted = load_document(str(link)).file_state
            writer = GuardedFileWriter()
            obs = writer.observe_target(str(link), expected_file_state=accepted)
            result = writer.commit(obs, b'new\n')
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_bytes(), b'new\n')
            self.assertEqual(result.file_state.binding.logical_path, os.path.abspath(str(link)))
    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks required')
    def test_symlink_retarget_during_staging_fails_before_commit(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / 'a.txt'
            b = Path(td) / 'b.txt'
            link = Path(td) / 'logical.txt'
            self._write(a, b'A\n')
            self._write(b, b'B\n')
            link.symlink_to(a.name)
            accepted = load_document(str(link)).file_state
            def hook(phase, _ctx):
                if phase == 'before_late_revalidation':
                    link.unlink()
                    link.symlink_to(b.name)
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(link), expected_file_state=accepted)
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'NEW\n')
            self.assertEqual(a.read_bytes(), b'A\n')
            self.assertEqual(b.read_bytes(), b'B\n')
    def test_absent_target_commit_is_no_overwrite_and_creates_new_file(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            writer = GuardedFileWriter()
            obs = writer.observe_target(str(target))
            result = writer.commit(obs, b'Body\n')
            self.assertEqual(target.read_bytes(), b'Body\n')
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_CONFIRMED)
    def test_absent_target_primary_rename_noreplace_is_fd_relative_and_consumes_stage(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            calls = []
            cwd_before = os.getcwd()
            def renameat2(source_fd, source_name, target_fd, target_name, flags):
                calls.append((source_fd, source_name, target_fd, target_name, flags))
                os.rename(source_name, target_name, src_dir_fd=source_fd, dst_dir_fd=target_fd)
                return 0
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.os.link',
                side_effect=AssertionError('link fallback must not run after primary success'),
            ):
                result = GuardedFileWriter().commit(
                    GuardedFileWriter().observe_target(str(target)),
                    b'Body\n',
                )
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_CONFIRMED)
            self.assertEqual(target.read_bytes(), b'Body\n')
            self.assertEqual(os.getcwd(), cwd_before)
            self.assertEqual(len(calls), 1)
            source_fd, source_name, target_fd, target_name, flags = calls[0]
            self.assertEqual(source_fd, target_fd)
            self.assertIsInstance(source_name, bytes)
            self.assertIsInstance(target_name, bytes)
            self.assertNotIn(b'/', source_name)
            self.assertEqual(target_name, b'new.txt')
            self.assertEqual(flags, guarded_writer_module._RENAME_NOREPLACE)
            self.assertEqual(list(Path(td).glob('.graphium-save-*.tmp')), [])
    def test_primary_rename_noreplace_eexist_is_stale_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            def hook(phase, _ctx):
                if phase == 'before_namespace_commit':
                    target.write_bytes(b'attacker')
            def renameat2(*_args):
                return -1
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target))
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.ctypes.get_errno',
                return_value=errno.EEXIST,
            ):
                with self.assertRaises(StaleSaveTargetError):
                    writer.commit(obs, b'Graphium')
            self.assertEqual(target.read_bytes(), b'attacker')
    def test_rename_noreplace_unsupported_uses_hardlink_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            real_link = os.link
            def renameat2(*_args):
                return -1
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.ctypes.get_errno',
                return_value=errno.ENOSYS,
            ), patch(
                'graphium.infrastructure.guarded_file_writer.os.link',
                wraps=real_link,
            ) as link_mock:
                writer = GuardedFileWriter()
                result = writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_CONFIRMED)
            self.assertEqual(target.read_bytes(), b'Body\n')
            self.assertEqual(link_mock.call_count, 1)
            self.assertEqual(list(Path(td).glob('.graphium-save-*.tmp')), [])
    def test_missing_renameat2_symbol_uses_hardlink_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            real_link = os.link
            with patch.object(guarded_writer_module, '_RENAMEAT2', None), patch(
                'graphium.infrastructure.guarded_file_writer.os.link',
                wraps=real_link,
            ) as link_mock:
                writer = GuardedFileWriter()
                result = writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_CONFIRMED)
            self.assertEqual(link_mock.call_count, 1)
            self.assertEqual(target.read_bytes(), b'Body\n')
    def test_rename_noreplace_unsupported_and_hardlink_unsupported_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            def renameat2(*_args):
                return -1
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.ctypes.get_errno',
                return_value=errno.ENOSYS,
            ), patch(
                'graphium.infrastructure.guarded_file_writer.os.link',
                side_effect=OSError(errno.EPERM, 'hard links unsupported'),
            ):
                writer = GuardedFileWriter()
                with self.assertRaises(GuardedWriteError):
                    writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(td).glob('.graphium-save-*.tmp')), [])
    def test_nonunsupported_rename_noreplace_error_does_not_enter_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            def renameat2(*_args):
                return -1
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.ctypes.get_errno',
                return_value=errno.EACCES,
            ), patch(
                'graphium.infrastructure.guarded_file_writer.os.link',
                side_effect=AssertionError('link fallback must be unsupported-only'),
            ):
                writer = GuardedFileWriter()
                with self.assertRaises(GuardedWriteError):
                    writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertFalse(target.exists())
    def test_absent_target_has_no_replacing_rename_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            def renameat2(*_args):
                return -1
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.ctypes.get_errno',
                return_value=errno.ENOSYS,
            ), patch(
                'graphium.infrastructure.guarded_file_writer.os.link',
                side_effect=OSError(errno.EPERM, 'hard links unsupported'),
            ), patch(
                'graphium.infrastructure.guarded_file_writer.os.replace',
                side_effect=AssertionError('replacing rename must not be used for absent target'),
            ):
                writer = GuardedFileWriter()
                with self.assertRaises(GuardedWriteError):
                    writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertFalse(target.exists())
    def test_link_fallback_unlink_failure_is_postcommit_warning_not_retry_failure(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            real_unlink = os.unlink
            def renameat2(*_args):
                return -1
            def unlink(path, *, dir_fd=None):
                if dir_fd is not None and isinstance(path, str) and path.startswith('.graphium-save-'):
                    raise OSError(errno.EIO, 'injected post-link cleanup failure')
                if dir_fd is None:
                    return real_unlink(path)
                return real_unlink(path, dir_fd=dir_fd)
            with patch.object(guarded_writer_module, '_RENAMEAT2', renameat2), patch(
                'graphium.infrastructure.guarded_file_writer.ctypes.get_errno',
                return_value=errno.ENOSYS,
            ), patch(
                'graphium.infrastructure.guarded_file_writer.os.unlink',
                side_effect=unlink,
            ):
                writer = GuardedFileWriter()
                result = writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertEqual(target.read_bytes(), b'Body\n')
            self.assertTrue(any(('post-commit stage cleanup failed' in w for w in result.warnings)))
            self.assertTrue(result.disposition.value.startswith('committed-'))
            self.assertEqual(len(list(Path(td).glob('.graphium-save-*.tmp'))), 1)
    def test_competing_creation_before_late_revalidation_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            def hook(phase, _ctx):
                if phase == 'before_late_revalidation':
                    target.write_bytes(b'attacker')
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target))
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'Graphium')
            self.assertEqual(target.read_bytes(), b'attacker')
    def test_competing_creation_at_namespace_commit_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            def hook(phase, _ctx):
                if phase == 'before_namespace_commit':
                    target.write_bytes(b'attacker')
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target))
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'Graphium')
            self.assertEqual(target.read_bytes(), b'attacker')
    def test_write_failure_leaves_existing_target_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'original\n')
            accepted = load_document(str(target)).file_state
            writer = GuardedFileWriter()
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            with patch('graphium.infrastructure.guarded_file_writer.os.write', side_effect=OSError(errno.ENOSPC, 'no space')):
                with self.assertRaises(Exception):
                    writer.commit(obs, b'replacement\n')
            self.assertEqual(target.read_bytes(), b'original\n')
    def test_stage_fsync_failure_leaves_existing_target_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'original\n')
            accepted = load_document(str(target)).file_state
            writer = GuardedFileWriter()
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            with patch('graphium.infrastructure.guarded_file_writer.os.fsync', side_effect=OSError(errno.EIO, 'sync fail')):
                with self.assertRaises(Exception):
                    writer.commit(obs, b'replacement\n')
            self.assertEqual(target.read_bytes(), b'original\n')
    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks required')
    def test_stage_path_substitution_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            attacker = Path(td) / 'attacker.txt'
            self._write(target, b'old\n')
            self._write(attacker, b'attacker')
            accepted = load_document(str(target)).file_state
            def hook(phase, ctx):
                if phase == 'after_stage_fsync':
                    stage = Path(ctx['stage_path'])
                    stage.unlink()
                    stage.symlink_to(attacker.name)
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'new\n')
            self.assertEqual(target.read_bytes(), b'old\n')
            self.assertEqual(attacker.read_bytes(), b'attacker')
    def test_existing_target_change_during_stage_is_late_guard_failure(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n')
            accepted = load_document(str(target)).file_state
            def hook(phase, _ctx):
                if phase == 'before_late_revalidation':
                    target.write_bytes(b'other\n')
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'new\n')
            self.assertEqual(target.read_bytes(), b'other\n')
    def test_existing_target_deleted_during_stage_is_late_guard_failure(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n')
            accepted = load_document(str(target)).file_state
            def hook(phase, _ctx):
                if phase == 'before_late_revalidation':
                    target.unlink()
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'new\n')
            self.assertFalse(target.exists())
    def test_parent_directory_replacement_after_observation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td) / 'folder'
            retired = Path(td) / 'retired'
            parent.mkdir()
            target = parent / 'new.txt'
            def hook(phase, _ctx):
                if phase == 'before_late_revalidation':
                    parent.rename(retired)
                    parent.mkdir()
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target))
            with self.assertRaises(StaleSaveTargetError):
                writer.commit(obs, b'Graphium\n')
            self.assertFalse(target.exists())
            self.assertFalse((retired / 'new.txt').exists())
    @unittest.skipUnless(hasattr(os, 'setxattr') and hasattr(os, 'getxattr'), 'xattrs required')
    def test_accessible_extended_attributes_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n')
            try:
                os.setxattr(target, 'user.graphium-test', b'kept')
            except OSError as exc:
                self.skipTest(f'filesystem does not support user xattrs: {exc}')
            accepted = load_document(str(target)).file_state
            writer = GuardedFileWriter()
            result = writer.commit(writer.observe_target(str(target), expected_file_state=accepted), b'new\n')
            self.assertIsNotNone(result.file_state)
            self.assertEqual(os.getxattr(target, 'user.graphium-test'), b'kept')
    def test_parent_directory_fsync_failure_is_committed_uncertainty_not_exception(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n')
            accepted = load_document(str(target)).file_state
            real_fsync = os.fsync
            calls = 0
            def fsync(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError(errno.EIO, 'dir sync fail')
                return real_fsync(fd)
            writer = GuardedFileWriter()
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            with patch('graphium.infrastructure.guarded_file_writer.os.fsync', side_effect=fsync):
                result = writer.commit(obs, b'new\n')
            self.assertEqual(target.read_bytes(), b'new\n')
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_DURABILITY_UNCERTAIN)
            self.assertTrue(any(('durability sync failed' in w for w in result.warnings)))
    def test_postcommit_baseline_failure_is_committed_baseline_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n')
            accepted = load_document(str(target)).file_state
            def hook(phase, _ctx):
                if phase == 'before_postcommit_load':
                    raise RuntimeError('injected postcommit observation failure')
            writer = GuardedFileWriter(test_hook=hook)
            obs = writer.observe_target(str(target), expected_file_state=accepted)
            result = writer.commit(obs, b'new\n')
            self.assertEqual(target.read_bytes(), b'new\n')
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_BASELINE_UNAVAILABLE)
            self.assertIsNone(result.file_state)
    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks required')
    def test_dangling_symlink_save_as_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            link = Path(td) / 'dangling.txt'
            link.symlink_to('missing.txt')
            with self.assertRaises(UnsafeSaveTargetError):
                GuardedFileWriter().observe_target(str(link))
    def test_directory_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td) / 'folder'
            folder.mkdir()
            with self.assertRaises(UnsafeSaveTargetError):
                GuardedFileWriter().observe_target(str(folder))
    def test_absent_target_uses_frozen_new_file_mode(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new.txt'
            writer = GuardedFileWriter(new_file_mode=416)
            result = writer.commit(writer.observe_target(str(target)), b'Body\n')
            self.assertEqual(result.disposition, SaveDisposition.COMMITTED_CONFIRMED)
            self.assertEqual(target.stat().st_mode & 511, 416)
    def test_mode_change_after_accepted_load_is_stale(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n', 420)
            accepted = load_document(str(target)).file_state
            target.chmod(384)
            with self.assertRaises(StaleSaveTargetError):
                GuardedFileWriter().observe_target(str(target), expected_file_state=accepted)
    def test_success_and_failure_leave_no_graphium_stage_files(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'doc.txt'
            self._write(target, b'old\n')
            accepted = load_document(str(target)).file_state
            writer = GuardedFileWriter()
            writer.commit(writer.observe_target(str(target), expected_file_state=accepted), b'new\n')
            self.assertEqual(list(Path(td).glob('.graphium-save-*.tmp')), [])
            accepted2 = load_document(str(target)).file_state
            obs2 = writer.observe_target(str(target), expected_file_state=accepted2)
            with patch('graphium.infrastructure.guarded_file_writer.os.write', side_effect=OSError(errno.ENOSPC, 'no space')):
                with self.assertRaises(Exception):
                    writer.commit(obs2, b'other\n')
            self.assertEqual(list(Path(td).glob('.graphium-save-*.tmp')), [])
if __name__ == '__main__':
    unittest.main()
