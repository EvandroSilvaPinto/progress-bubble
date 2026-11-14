import sys,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))

class SettingsTests(unittest.TestCase):
    def test_visibility_preference_is_saved_and_corruption_falls_back_safely(self):
        from settings_menu import load_preferences,save_preferences
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json'
            self.assertFalse(load_preferences(path)['show_usage'])
            save_preferences(True,path)
            self.assertTrue(load_preferences(path)['show_usage'])
            save_preferences(False,path)
            self.assertFalse(load_preferences(path)['show_usage'])
            path.write_text('[]');self.assertFalse(load_preferences(path)['show_usage'])
    def test_hidden_usage_removes_both_card_bar_and_ring_state(self):
        from usage_ui import current_usage
        app=SimpleNamespace(settings={'show_usage':False},data={'usage_provider':'codex'})
        self.assertIsNone(current_usage(app))
    def test_settings_menu_unifies_actions_and_retains_size_callbacks(self):
        from settings_menu import show_settings_menu
        menus=[Mock() for _ in range(4)]
        app=SimpleNamespace(root=Mock(),tooltip=Mock(),sizes={'card':'Médio','bubble':'Médio'},settings={'show_usage':True},colors_open=False,edit_colors=Mock(),reset_theme=Mock(),change_size=Mock(),draw=Mock())
        with patch('tkinter.Menu',side_effect=menus),patch('tkinter.StringVar'),patch('tkinter.BooleanVar'),patch('i18n.system_language',return_value='pt'):
            show_settings_menu(app,SimpleNamespace(x_root=10,y_root=20))
        labels=[call.kwargs['label'] for call in menus[0].add_command.call_args_list]
        self.assertIn('Cores',labels)
        self.assertEqual(menus[0].add_cascade.call_args.kwargs['label'],'Tamanhos')
        self.assertEqual(menus[0].add_checkbutton.call_args.kwargs['label'],'Mostrar uso da assinatura')
        self.assertIs(app.settings_menu,menus[0]);menus[0].destroy.assert_not_called()
        menus[2].add_radiobutton.call_args_list[2].kwargs['command']()
        app.change_size.assert_called_once_with('card','Grande')

    def test_hidden_tracker_does_not_schedule_provider_reads(self):
        from bubble import Bubble
        from colors import DEFAULTS as COLORS
        from sizing import DEFAULTS as SIZES
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)/'state.json';data={'title':'Task','message':'Working','status':'Em andamento','percent':10,'usage_provider':'codex'}
            state.write_text(json.dumps(data))
            app=Bubble.__new__(Bubble);app.state=state;app.data=data;app.sizes=dict(SIZES);app.theme=dict(COLORS)
            app.root=Mock();app.usage_reader=Mock();app.usage_reader.read.return_value=None;app.draw=Mock()
            with patch('bubble.load_preferences',return_value={'show_usage':False}),patch('bubble.load_sizes',return_value=dict(SIZES)),patch('bubble.load_colors',return_value=dict(COLORS)):
                app.refresh()
            app.usage_reader.read.assert_called_once_with('off')
