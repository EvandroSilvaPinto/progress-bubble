import sys,time,unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))

class UsageTests(unittest.TestCase):
    def sample(self,percent=42,reset=8200):
        from usage_model import normalize
        return normalize('codex',{'rateLimits':{'primary':{'usedPercent':percent,'windowDurationMins':300,'resetsAt':reset},'secondary':{'usedPercent':68,'windowDurationMins':10080,'resetsAt':9000}},'secret':'never'},now=1000)
    def test_real_windows_normalize_and_private_fields_are_dropped(self):
        from usage_model import view
        data=self.sample(0);self.assertNotIn('secret',json.dumps(data))
        self.assertEqual(view(data,now=1001)['used'],0)
        self.assertEqual(view(data,'secondary',1001)['used'],68)
    def test_colors_and_countdown_only_at_full_usage(self):
        from usage_model import view
        for percent,color in [(0,'#58d9b0'),(60,'#f1cc62'),(80,'#ffad66'),(95,'#ff7185')]:
            self.assertEqual(view(self.sample(percent),now=1000)['color'],color)
        state=view(self.sample(100),now=1000)
        self.assertEqual(state['detail'],'Renova em 2h')
        self.assertNotIn('Renova',view(self.sample(99),now=1000)['detail'])
        self.assertEqual(view(self.sample(100),'primary',1000,'en')['detail'],'Renews in 2h')
    def test_reset_and_stale_data_never_fabricate_zero(self):
        from usage_model import view
        self.assertIsNone(view(self.sample(100,999),now=1000)['used'])
        self.assertIsNone(view(self.sample(),now=1301)['used'])
        self.assertIsNone(view(None,now=1000)['used'])
    def test_malformed_fields_are_unavailable_and_zero_is_valid(self):
        from usage_model import normalize,view
        for value in [True,-1,float('nan'),'42',None,101]:
            raw={'rateLimits':{'primary':{'usedPercent':value,'windowDurationMins':300}}}
            self.assertIsNone(view(normalize('codex',raw,now=1000),now=1000)['used'])
    def test_claude_supported_windows(self):
        from usage_model import normalize,view
        data=normalize('claude',{'rate_limits':{'five_hour':{'used_percentage':25,'resets_at':4000},'seven_day':{'used_percentage':90,'resets_at':8000}}},now=1000)
        self.assertEqual(view(data,now=1000)['used'],25)
        self.assertEqual(view(data,'secondary',1000)['used'],90)
    def test_mobile_allowlist_never_uploads_account_quota(self):
        import web_client
        self.assertNotIn('usage',web_client.FIELDS);self.assertNotIn('usage_provider',web_client.FIELDS)

class UsageCacheTests(unittest.TestCase):
    def test_local_cache_reuses_result_and_background_failure_preserves_snapshot(self):
        from usage_source import poll,cache_path
        with tempfile.TemporaryDirectory() as directory,patch('usage_source.cache_path',return_value=Path(directory)/'usage.json'),patch('usage_source.read_codex',return_value={'rateLimits':{'primary':{'usedPercent':25,'windowDurationMins':300}}}) as read:
            first=poll('codex');second=poll('codex')
            self.assertEqual(first,second);self.assertEqual(read.call_count,1)
    def test_cache_only_keeps_normalized_numeric_usage(self):
        from usage_source import accept_feed,load_cache
        with tempfile.TemporaryDirectory() as directory,patch('usage_source.cache_path',return_value=Path(directory)/'usage.json'):
            accept_feed('claude',{'auth':'secret','rate_limits':{'five_hour':{'used_percentage':100,'resets_at':time.time()+100}}})
            self.assertNotIn('secret',json.dumps(load_cache('claude')))

class UsagePresentationTests(unittest.TestCase):
    def test_card_countdown_and_bubble_only_image(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from usage_model import normalize,view
        from usage_ui import draw_usage,draw_usage_ring
        data=normalize('codex',{'rateLimits':{'primary':{'usedPercent':100,'windowDurationMins':300,'resetsAt':8200}}},now=1000)
        app=SimpleNamespace(text=Mock(),rounded=Mock(),canvas=Mock(),theme={'track':'#27334a'},layout={'bubble':1,'bubble_x':0,'bubble_y':0})
        state=view(data,now=1000)
        draw_usage(app,state)
        self.assertTrue(any('Renova em' in str(call) for call in app.text.call_args_list))
        app.text.reset_mock()
        with patch('usage_ui.tk.PhotoImage'):
            draw_usage_ring(app,state)
        app.text.assert_not_called();app.canvas.create_text.assert_not_called()
    def test_outer_ring_preserves_native_dimensions_and_is_transparent_in_center(self):
        from usage_ui import quota_ring_png
        import struct,zlib
        for scale in (.85,1,1.2,1.5,2):
            png=quota_ring_png(100,'#ff7185',scale,'#27334a')
            width=struct.unpack('!I',png[16:20])[0];self.assertEqual(width,max(32,round(84*scale)))
            offset=8;chunks=[]
            while offset<len(png):
                length=int.from_bytes(png[offset:offset+4],'big');kind=png[offset+4:offset+8]
                if kind==b'IDAT':chunks.append(png[offset+8:offset+8+length])
                offset+=12+length
            raw=zlib.decompress(b''.join(chunks));center=(width//2)*(width*4+1)+1+(width//2)*4+3
            self.assertEqual(raw[center],0)

    def test_existing_claude_statusline_is_never_overwritten(self):
        from usage_bridge import install_claude
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json';original={'statusLine':{'type':'command','command':'existing-custom-command'},'other':123}
            path.write_text(json.dumps(original))
            with self.assertRaises(ValueError):install_claude(path)
            self.assertEqual(json.loads(path.read_text()),original)
    def test_cache_is_revalidated_before_entering_task_deliverables(self):
        from usage_source import load_cache
        with tempfile.TemporaryDirectory() as directory,patch('usage_source.cache_path',return_value=Path(directory)/'usage.json'):
            path=Path(directory)/'usage.json'
            path.write_text(json.dumps({'provider':'codex','observed_at':time.time(),'secret':'private','windows':{'primary':{'used_percent':25,'window_minutes':300}}}))
            self.assertNotIn('secret',json.dumps(load_cache('codex')))

    def test_invalid_task_snapshot_cannot_crash_the_card(self):
        from types import SimpleNamespace
        from usage_ui import current_usage
        app=SimpleNamespace(data={'usage_provider':'codex','usage':['bad']},usage_snapshot=None)
        self.assertIsNone(current_usage(app)['used'])

class ReviewRegressionTests(unittest.TestCase):
    def test_distinct_profiles_do_not_share_account_quota(self):
        import os
        from usage_source import cache_path
        for provider,key in [('codex','CODEX_HOME'),('claude','CLAUDE_CONFIG_DIR')]:
            with patch.dict(os.environ,{key:'profile-one'}):first=cache_path(provider)
            with patch.dict(os.environ,{key:'profile-two'}):second=cache_path(provider)
            self.assertNotEqual(first,second)
    def test_confirmed_absent_quota_clears_previous_full_snapshot(self):
        from usage_source import accept_feed,load_cache
        with tempfile.TemporaryDirectory() as directory,patch('usage_source.cache_path',return_value=Path(directory)/'usage.json'):
            accept_feed('claude',{'rate_limits':{'five_hour':{'used_percentage':100,'resets_at':time.time()+100}}})
            accept_feed('claude',{})
            self.assertEqual(load_cache('claude')['windows'],{})
    def test_extreme_numbers_cannot_break_normalization_or_card_refresh(self):
        from usage_model import normalize,view
        for value in (10**400,1e307):
            data=normalize('codex',{'rateLimits':{'primary':{'usedPercent':value,'windowDurationMins':300}}})
            self.assertIsNone(view(data)['used'])
            data={'provider':'codex','observed_at':time.time(),'windows':{'primary':{'used_percent':10,'window_minutes':value}}}
            self.assertIsNone(view(data)['used'])
    def test_renewal_text_is_not_printed_into_claude_statusline(self):
        import usage_bridge,io,contextlib
        from usage_model import normalize
        data=normalize('claude',{'rate_limits':{'five_hour':{'used_percentage':100,'resets_at':time.time()+100}}})
        with patch.object(sys,'argv',['usage_bridge.py']),patch.object(sys,'stdin',io.StringIO('{}')),patch.object(usage_bridge,'accept_feed',return_value=data),contextlib.redirect_stdout(io.StringIO()) as output:
            usage_bridge.main()
        self.assertNotIn('Renova',output.getvalue());self.assertNotIn('Renews',output.getvalue())
    def test_claude_setup_respects_its_config_directory(self):
        import usage_bridge,os
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.dict(os.environ,CLAUDE_CONFIG_DIR=str(root/'custom')),patch.object(usage_bridge.Path,'home',return_value=root/'home'),patch.object(usage_bridge,'save_secret') as save:
                usage_bridge.install_claude()
            self.assertEqual(save.call_args.args[0],root/'custom/settings.json')
    def test_multiline_messages_fit_a_single_measured_card_line(self):
        from usage_ui import compact_message
        for text in ['Schema validated.\nProvider connected.\nWaiting for response.','W'*100,'界'*100]:
            result=compact_message(text,lambda s:len(s)*10,302)
            self.assertNotIn('\n',result);self.assertLessEqual(len(result)*10,302)
