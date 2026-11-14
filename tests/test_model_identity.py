import sys,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
THREAD='11111111-2222-3333-4444-555555555555'
ORIGIN='codex://threads/'+THREAD

class ModelIdentityTests(unittest.TestCase):
    def test_reads_only_latest_current_thread_model_metadata(self):
        from model_identity import codex_model
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            rows=[{'type':'turn_context','payload':{'model':'older-model'}},{'type':'event_msg','payload':{'model':'ignore-message-model'}},{'type':'turn_context','payload':{'model':'gpt-6.1-sol'}}]
            (root/('rollout-'+THREAD+'.jsonl')).write_text('\n'.join(json.dumps(r) for r in rows))
            (root/'other-thread.jsonl').write_text(json.dumps({'type':'turn_context','payload':{'model':'wrong-chat'}}))
            self.assertEqual(codex_model(ORIGIN,root),'gpt-6.1-sol')
    def test_first_line_metadata_and_missing_data_are_handled(self):
        from model_identity import codex_model
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertIsNone(codex_model(ORIGIN,root))
            (root/('rollout-'+THREAD+'.jsonl')).write_text(json.dumps({'type':'turn_context','payload':{'model':'known-model'}}))
            self.assertEqual(codex_model(ORIGIN,root),'known-model')
            self.assertIsNone(codex_model('https://example.com/chat',root))
    def test_invalid_names_are_rejected_instead_of_guessed(self):
        from model_identity import clean_model
        for value in (None,True,{},'','x'*97,'model\nsecret'):
            self.assertIsNone(clean_model(value))
        self.assertEqual(clean_model('Claude Opus 4.7'),'Claude Opus 4.7')
    def test_explicit_model_and_changed_origin_do_not_mix_chats(self):
        from model_identity import resolve_model
        previous={'conversation_url':'https://example.com/chat-a','model_name':'old-model'}
        self.assertEqual(resolve_model('known-model',None,previous),'known-model')
        self.assertIsNone(resolve_model(None,'https://example.com/chat-b',previous))
        with patch('model_identity.codex_model',return_value=None):self.assertIsNone(resolve_model(None,ORIGIN,previous))
    def test_model_name_stays_out_of_mobile_payload(self):
        from web_client import FIELDS
        self.assertNotIn('model_name',FIELDS)

    def test_corrupt_deep_metadata_does_not_break_progress_delivery(self):
        from model_identity import codex_model
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/('rollout-'+THREAD+'.jsonl')).write_text('{"type":"turn_context","payload":'+'['*20000+'0'+']'*20000+'}')
            self.assertIsNone(codex_model(ORIGIN,root))
