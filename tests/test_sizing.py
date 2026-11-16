from pathlib import Path
import sys
import tempfile
import unittest
import struct
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from sizing import DEFAULTS, FACTORS, geometry, load_sizes, save_size, show_size_menu
from ring import ring_png


class SizingTests(unittest.TestCase):
    def test_menu_retains_callbacks_until_deferred_windows_selection_runs(self):
        root_menu, card_menu, bubble_menu = Mock(), Mock(), Mock()
        app=SimpleNamespace(root=Mock(),sizes=dict(DEFAULTS),change_size=Mock())
        with patch('tkinter.Menu',side_effect=[root_menu,card_menu,bubble_menu]), patch('tkinter.StringVar'):
            show_size_menu(app,SimpleNamespace(x_root=10,y_root=20))
        root_menu.destroy.assert_not_called()
        self.assertIs(app.size_menu,root_menu)
        # Invoke after popup returned, as the Windows selection can be delivered.
        card_menu.add_radiobutton.call_args_list[2].kwargs['command']()
        app.change_size.assert_called_once_with('card','Grande')
        app.change_size.reset_mock()
        bubble_menu.add_radiobutton.call_args_list[0].kwargs['command']()
        app.change_size.assert_called_once_with('bubble','Pequeno')

    def test_selections_are_independent_and_persistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sizes.json'
            self.assertEqual(load_sizes(path),DEFAULTS)
            save_size('card','Grande',path)
            save_size('bubble','Pequeno',path)
            self.assertEqual(load_sizes(path),dict(card='Grande',bubble='Pequeno'))
            with self.assertRaises(ValueError):
                save_size('bubble','Huge',path)
            self.assertEqual(load_sizes(path)['bubble'],'Pequeno')

    def test_all_combinations_fit_at_different_dpi_and_palette_states(self):
        for dpi in (1,1.5,2):
            for card in FACTORS:
                for bubble in FACTORS:
                    for palette in (False,True):
                        layout=geometry(dpi,dict(card=card,bubble=bubble),palette)
                        self.assertGreaterEqual(layout['card_x'],-1)
                        self.assertGreaterEqual(layout['bubble_y'],0)
                        self.assertLessEqual(layout['bubble_x']+84*layout['bubble'],layout['width'])
                        card_bottom=(270+layout['offset'])*layout['card']
                        self.assertGreaterEqual(layout['bubble_y'],card_bottom-1)
                        self.assertGreaterEqual(layout['bubble_y']-19*layout['bubble'],0)

    def test_smaller_ring_uses_requested_native_resolution(self):
        for factor in FACTORS.values():
            png=ring_png(65,'#8b9dff',factor)
            self.assertEqual(struct.unpack('!II',png[16:24]),(round(84*factor),)*2)

    def test_corrupt_settings_fall_back_to_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sizes.json'
            path.write_text('[]')
            self.assertEqual(load_sizes(path),DEFAULTS)


class SolidBubbleTests(unittest.TestCase):
    def test_disk_is_opaque_through_gap_below_outer_usage_ring(self):
        import math,zlib
        for scale in (.85,1,1.2,1.5,2):
            png=ring_png(65,'#8b9dff',scale)
            size=struct.unpack('!I',png[16:20])[0]
            chunks=[];offset=8
            while offset<len(png):
                length=int.from_bytes(png[offset:offset+4],'big')
                if png[offset+4:offset+8]==b'IDAT':chunks.append(png[offset+8:offset+8+length])
                offset+=length+12
            raw=zlib.decompress(b''.join(chunks));factor=size/84
            for y in range(size):
                for x in range(size):
                    if math.hypot((x+.5)/factor-42,(y+.5)/factor-42)<40:
                        self.assertEqual(raw[y*(size*4+1)+1+x*4+3],255,(scale,x,y))
            self.assertEqual(raw[4],0,'Exterior corners must remain transparent')
