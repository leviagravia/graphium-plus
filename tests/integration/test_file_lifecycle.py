from __future__ import annotations
import tempfile
from pathlib import Path
import unittest
from graphium.application.document_save_service import DocumentSaveService
from graphium.application.document_session import DocumentSession
from graphium.application.file_lifecycle import FileLifecycleController, ReloadDecision, UnsavedDecision
from graphium.application.native_editor import NativeEditorController
from graphium.domain.edit_history import DeltaHistory
from graphium.infrastructure.document_loader import load_document
from graphium.infrastructure.guarded_file_writer import GuardedFileWriter
from tests.behavioral._native_test_support import NativeTestBuffer
FakeBuffer = NativeTestBuffer
class RecoverySpy:
    def __init__(self): self.changed=0; self.invalidated=0
    def document_state_changed(self): self.changed+=1
    def invalidate(self): self.invalidated+=1
class FakeUI:
    def __init__(self):
        self.open_path=None; self.save_path=None; self.unsaved=UnsavedDecision.CANCEL; self.reload_decision=ReloadDecision.CANCEL; self.overwrite=False; self.mixed=False
        self.errors=[]; self.warnings=[]; self.unsaved_prompts=[]; self.reload_prompts=0; self.overwrite_prompts=[]
    def choose_open_path(self): return self.open_path
    def choose_save_path(self,_current): return self.save_path
    def confirm_unsaved_changes(self,action_label): self.unsaved_prompts.append(action_label); return self.unsaved
    def confirm_modified_reload(self): self.reload_prompts+=1; return self.reload_decision
    def confirm_overwrite(self,path): self.overwrite_prompts.append(path); return self.overwrite
    def confirm_mixed_eol_normalization(self): return self.mixed
    def show_error(self,title,message): self.errors.append((title,message))
    def show_warning(self,title,message): self.warnings.append((title,message))
class FileLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.buffer = NativeTestBuffer()
        self.session = DocumentSession()
        self.history = DeltaHistory()
        self.editor = NativeEditorController(session=self.session, history=self.history, buffer=self.buffer)
        self.editor.initialize_new_text('', clean=True)
        self.writer = GuardedFileWriter()
        self.save_service = DocumentSaveService(session=self.session, writer=self.writer)
        self.ui = FakeUI()
        self.lifecycle = FileLifecycleController(session=self.session, editor=self.editor, save_service=self.save_service, loader=load_document, ui=self.ui)
    def tearDown(self) -> None:
        self.temp.cleanup()
    def edit(self, text: str) -> None:
        old = self.buffer.text
        self.assertTrue(text.startswith(old), 'test helper supports append edits')
        self.buffer.user_insert(self.editor, len(old), text[len(old):])
    def file_bytes(self,name,raw):
        path=self.root/name; path.write_bytes(raw); return path
    def open_bytes(self,name,raw):
        path=self.file_bytes(name,raw); self.assertTrue(self.lifecycle.open_document(str(path)).completed); return path
    def state_triplet(self): return self.session.snapshot(),self.history.checkpoint(),self.buffer.text
    def assert_state_triplet(self,before): self.assertEqual((self.session.snapshot(),self.history.checkpoint(),self.buffer.text),before)
    def bind_recovery_spy(self):
        r=RecoverySpy(); self.lifecycle.recovery=r; self.editor.set_document_state_listener(r.document_state_changed); return r
    def test_prepared_replacement_discard_authorizes_canonical_open_without_second_prompt(self):
        self.edit('draft')
        target = self.file_bytes('created.md', b'')
        self.ui.unsaved = UnsavedDecision.DISCARD
        permit = self.lifecycle.prepare_document_replacement('open a new Workspace text file')
        self.assertIsNotNone(permit)
        self.assertEqual(self.ui.unsaved_prompts, ['open a new Workspace text file'])
        result = self.lifecycle.open_document(str(target), replacement_permit=permit)
        self.assertTrue(result.completed)
        self.assertEqual(self.ui.unsaved_prompts, ['open a new Workspace text file'])
        self.assertEqual(self.session.logical_path, str(target))
        self.assertFalse(self.session.modified)

    def test_prepared_replacement_fails_closed_if_document_changes_before_open(self):
        self.edit('draft')
        target = self.file_bytes('created.md', b'')
        self.ui.unsaved = UnsavedDecision.DISCARD
        permit = self.lifecycle.prepare_document_replacement('open a new Workspace text file')
        self.assertIsNotNone(permit)
        self.edit('draft changed')
        before = self.state_triplet()
        result = self.lifecycle.open_document(str(target), replacement_permit=permit)
        self.assertFalse(result.completed)
        self.assert_state_triplet(before)
        self.assertTrue(self.ui.errors)
        self.assertIn('changed after replacement was authorized', self.ui.errors[-1][1])

    def test_recovery_failed_open_after_discard_preserves_generation(self):
        self.edit('draft'); r=self.bind_recovery_spy(); self.ui.unsaved=UnsavedDecision.DISCARD
        self.assertFalse(self.lifecycle.open_document(str(self.root/'missing.txt')).completed); self.assertEqual((r.changed,r.invalidated),(0,0))
    def test_recovery_successful_replace_notifies_only_after_install(self):
        self.edit('draft'); r=self.bind_recovery_spy(); self.ui.unsaved=UnsavedDecision.DISCARD
        self.assertTrue(self.lifecycle.new_document().completed); self.assertEqual((r.changed,r.invalidated),(1,0))
    def test_recovery_close_cancel_preserves_but_discard_invalidates(self):
        self.edit('draft'); r=self.bind_recovery_spy(); self.ui.unsaved=UnsavedDecision.CANCEL
        self.assertFalse(self.lifecycle.request_close().completed); self.assertEqual(r.invalidated,0)
        self.ui.unsaved=UnsavedDecision.DISCARD; self.assertTrue(self.lifecycle.request_close().completed); self.assertEqual(r.invalidated,1)
    def test_unsaved_prompt_does_not_copy_full_buffer(self):
        self.edit('draft')
        self.buffer.full_captures = 0
        self.ui.unsaved = UnsavedDecision.CANCEL
        result = self.lifecycle.new_document()
        self.assertFalse(result.completed)
        self.assertEqual(self.buffer.full_captures, 0)
    def test_new_document_cancel_preserves_modified_document(self):
        self.edit('draft')
        before = self.session.snapshot()
        self.ui.unsaved = UnsavedDecision.CANCEL
        result = self.lifecycle.new_document()
        self.assertFalse(result.completed)
        self.assertTrue(result.cancelled)
        self.assertEqual(self.session.snapshot(), before)
        self.assertEqual(self.buffer.text, 'draft')
    def test_new_document_discard_replaces_and_is_clean(self):
        self.edit('draft')
        self.ui.unsaved = UnsavedDecision.DISCARD
        result = self.lifecycle.new_document()
        self.assertTrue(result.completed)
        self.assertEqual(self.buffer.text, '')
        self.assertIsNone(self.session.logical_path)
        self.assertFalse(self.session.modified)
        self.assertFalse(self.editor.can_undo)
    def test_failed_open_preserves_current_document(self):
        self.edit('keep me')
        self.ui.unsaved = UnsavedDecision.DISCARD
        before = self.session.snapshot()
        result = self.lifecycle.open_document(str(self.root / 'missing.txt'))
        self.assertFalse(result.completed)
        self.assertEqual(self.session.snapshot(), before)
        self.assertEqual(self.buffer.text, 'keep me')
        self.assertTrue(self.ui.errors)
    def test_open_loads_before_replacing_and_is_clean(self):
        source = self.file_bytes('source.txt',b'hello\r\nworld\r\n')
        result = self.lifecycle.open_document(str(source))
        self.assertTrue(result.completed)
        self.assertEqual(self.buffer.text, 'hello\nworld\n')
        self.assertEqual(self.session.logical_path, str(source))
        self.assertFalse(self.session.modified)
        self.assertFalse(self.editor.can_undo)
    def test_pathological_huge_line_open_is_rejected_before_buffer_install(self):
        from graphium.application.renderability import MAX_INTERACTIVE_LINE_CHARS
        self.edit('keep current')
        self.ui.unsaved = UnsavedDecision.DISCARD
        before_session = self.session.snapshot()
        before_history = self.history.checkpoint()
        source = self.root / 'huge-line.txt'
        source.write_text('x' * (MAX_INTERACTIVE_LINE_CHARS + 1), encoding='utf-8')
        result = self.lifecycle.open_document(str(source))
        self.assertFalse(result.completed)
        self.assertEqual(self.buffer.text, 'keep current')
        self.assertEqual(self.session.snapshot(), before_session)
        after_history = self.history.checkpoint()
        self.assertEqual(after_history, before_history)
        self.assertTrue(self.ui.errors)
        self.assertIn('line too long', self.ui.errors[-1][0].lower())
    def test_huge_line_open_does_not_truncate_or_mutate_source_bytes(self):
        from graphium.application.renderability import MAX_INTERACTIVE_LINE_CHARS
        source = self.root / 'huge-line.txt'
        raw = ('x' * (MAX_INTERACTIVE_LINE_CHARS + 1)).encode('utf-8')
        source.write_bytes(raw)
        result = self.lifecycle.open_document(str(source))
        self.assertFalse(result.completed)
        self.assertEqual(source.read_bytes(), raw)
    def test_save_untitled_syncs_once_then_save_as_rebinds_after_commit(self):
        self.edit('hello')
        target = self.root / 'new.txt'
        self.ui.save_path = str(target)
        self.buffer.full_captures = 0
        result = self.lifecycle.save()
        self.assertTrue(result.completed)
        self.assertEqual(self.buffer.full_captures, 1)
        self.assertEqual(target.read_bytes(), b'hello')
        self.assertEqual(self.session.logical_path, str(target))
        self.assertFalse(self.session.modified)
    def test_save_as_existing_requires_explicit_overwrite_consent(self):
        self.edit('new bytes')
        target = self.root / 'existing.txt'
        target.write_bytes(b'old bytes')
        self.ui.save_path = str(target)
        result = self.lifecycle.save_as()
        self.assertFalse(result.completed)
        self.assertTrue(result.cancelled)
        self.assertEqual(target.read_bytes(), b'old bytes')
        self.assertIsNone(self.session.logical_path)
    def test_save_as_existing_rebinds_only_after_successful_commit(self):
        self.edit('new bytes')
        target = self.root / 'existing.txt'
        target.write_bytes(b'old bytes')
        self.ui.save_path = str(target)
        self.ui.overwrite = True
        result = self.lifecycle.save_as()
        self.assertTrue(result.completed)
        self.assertEqual(target.read_bytes(), b'new bytes')
        self.assertEqual(self.session.logical_path, str(target))
        self.assertFalse(self.session.modified)
    def test_mixed_eol_save_requires_explicit_normalization_consent(self):
        source = self.open_bytes('mixed.txt',b'a\r\nb\nc\r')
        self.buffer.user_insert(self.editor, len(self.buffer.text), 'd')
        self.ui.mixed = False
        denied = self.lifecycle.save()
        self.assertFalse(denied.completed)
        self.assertTrue(denied.cancelled)
        self.assertTrue(self.session.modified)
        self.ui.mixed = True
        accepted = self.lifecycle.save()
        self.assertTrue(accepted.completed)
        self.assertFalse(self.session.modified)
    def test_stale_external_mutation_blocks_ordinary_save(self):
        source = self.open_bytes('doc.txt',b'one')
        self.buffer.user_insert(self.editor, len(self.buffer.text), ' mine')
        source.write_bytes(b'theirs')
        result = self.lifecycle.save()
        self.assertFalse(result.completed)
        self.assertEqual(source.read_bytes(), b'theirs')
        self.assertTrue(self.session.modified)
        self.assertTrue(self.ui.errors)
    def test_reload_clean_accepts_fresh_disk_bytes_without_touching_recent(self):
        source = self.open_bytes('reload.txt',b'first')
        class RecentSpy:
            def __init__(self): self.touches=[]
            def touch(self, path): self.touches.append(path)
        recent=RecentSpy(); self.lifecycle.recent_files=recent
        source.write_bytes(b'second')
        result = self.lifecycle.reload_document()
        self.assertTrue(result.completed)
        self.assertTrue(result.changed_document)
        self.assertEqual(self.buffer.text, 'second')
        self.assertEqual(self.session.logical_path, str(source))
        self.assertFalse(self.session.modified)
        self.assertFalse(self.editor.can_undo)
        self.assertEqual(recent.touches, [])
    def test_reload_modified_cancel_preserves_buffer_session_and_history(self):
        source = self.open_bytes('reload-cancel.txt',b'disk')
        self.buffer.user_insert(self.editor, len(self.buffer.text), ' mine')
        source.write_bytes(b'external')
        before=self.state_triplet()
        self.ui.reload_decision = ReloadDecision.CANCEL
        result = self.lifecycle.reload_document()
        self.assertFalse(result.completed); self.assertTrue(result.cancelled)
        self.assert_state_triplet(before)
        self.assertEqual(source.read_bytes(),b'external')
        self.assertEqual(self.ui.reload_prompts, 1)
        self.assertEqual(self.ui.unsaved_prompts, [])
    def test_reload_modified_discard_accepts_current_disk_object(self):
        source = self.open_bytes('reload-discard.txt',b'alpha')
        self.buffer.user_insert(self.editor, len(self.buffer.text), ' mine')
        replacement = self.root / 'replacement.tmp'
        replacement.write_bytes(b'beta')
        old_object=self.session.file_state.binding.object_id
        replacement.replace(source)
        class NeverReloadWriter(GuardedFileWriter):
            def observe_target(self, *args, **kwargs):
                raise AssertionError('Reload must never invoke writer observation')
            def commit(self, *args, **kwargs):
                raise AssertionError('Reload must never invoke writer commit')
        self.lifecycle.save_service = DocumentSaveService(
            session=self.session, writer=NeverReloadWriter()
        )
        self.ui.reload_decision = ReloadDecision.DISCARD_AND_RELOAD
        result=self.lifecycle.reload_document()
        self.assertTrue(result.completed)
        self.assertEqual(self.buffer.text,'beta')
        self.assertNotEqual(self.session.file_state.binding.object_id,old_object)
        self.assertFalse(self.session.modified)
        self.assertEqual(self.ui.reload_prompts, 1)
        self.assertEqual(self.ui.unsaved_prompts, [])
    def test_reload_modified_uses_dedicated_decision_and_never_generic_save_prompt(self):
        source = self.open_bytes('reload-dedicated.txt',b'alpha')
        self.buffer.user_insert(self.editor, len(self.buffer.text), ' mine')
        source.write_bytes(b'external')
        self.ui.unsaved = UnsavedDecision.SAVE  # tripwire: generic path must never be consulted
        self.ui.reload_decision = ReloadDecision.CANCEL
        before_text = self.buffer.text
        result = self.lifecycle.reload_document()
        self.assertFalse(result.completed)
        self.assertTrue(result.cancelled)
        self.assertEqual(self.ui.reload_prompts, 1)
        self.assertEqual(self.ui.unsaved_prompts, [])
        self.assertEqual(self.buffer.text, before_text)
        self.assertEqual(source.read_bytes(), b'external')
        self.assertTrue(self.session.modified)
    def test_reload_failure_preserves_current_document(self):
        source = self.open_bytes('reload-missing.txt',b'keep')
        before=self.state_triplet()
        source.unlink()
        result=self.lifecycle.reload_document()
        self.assertFalse(result.completed)
        self.assert_state_triplet(before)
        self.assertTrue(self.ui.errors)
    def test_reload_pathological_line_is_rejected_before_buffer_install(self):
        from graphium.application.renderability import MAX_INTERACTIVE_LINE_CHARS
        source = self.open_bytes('reload-huge.txt',b'safe')
        before=self.state_triplet()
        source.write_text('x' * (MAX_INTERACTIVE_LINE_CHARS + 1), encoding='utf-8')
        result=self.lifecycle.reload_document()
        self.assertFalse(result.completed)
        self.assert_state_triplet(before)
        self.assertTrue(self.ui.errors)
        self.assertIn('line too long', self.ui.errors[-1][0].lower())
    def test_reload_untitled_is_inert(self):
        before=self.session.snapshot(); before_history=self.history.checkpoint()
        result=self.lifecycle.reload_document()
        self.assertFalse(result.completed)
        self.assertEqual(self.session.snapshot(),before)
        self.assertEqual(self.history.checkpoint(),before_history)
    def test_close_save_cancelled_keeps_window_open_semantics(self):
        self.edit('draft')
        self.ui.unsaved = UnsavedDecision.SAVE
        self.ui.save_path = None
        result = self.lifecycle.request_close()
        self.assertFalse(result.completed)
        self.assertTrue(result.cancelled)
        self.assertTrue(self.session.modified)
    def test_close_discard_completes_without_mutating_document(self):
        self.edit('draft')
        self.ui.unsaved = UnsavedDecision.DISCARD
        result = self.lifecycle.request_close()
        self.assertTrue(result.completed)
        self.assertEqual(self.buffer.text, 'draft')
if __name__ == '__main__':
    unittest.main()
