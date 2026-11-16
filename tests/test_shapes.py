from pathlib import Path
import struct
import sys
import unittest
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from shapes import rounded_png


def pixels(png):
    width,height = struct.unpack('!II',png[16:24])
    offset,data = 8,b''
    while offset<len(png):
        length = struct.unpack('!I',png[offset:offset+4])[0]
        if png[offset+4:offset+8]==b'IDAT':
            data += png[offset+8:offset+8+length]
        offset += length+12
    raw = zlib.decompress(data)
    rows = [raw[y*(width*4+1)+1:(y+1)*(width*4+1)] for y in range(height)]
    return width,height,[tuple(row[x:x+4]) for row in rows for x in range(0,len(row),4)]


class ShapeTests(unittest.TestCase):
    def test_circle_has_smooth_edges_and_preserves_selected_color(self):
        width,height,rgba = pixels(rounded_png(32,32,16,'#ff77aa','#ffffff','#101827'))
        self.assertEqual((width,height),(32,32))
        self.assertEqual(rgba[16*32+16],(255,119,170,255))
        self.assertEqual(rgba[0],(16,24,39,255))
        self.assertGreater(len(set(rgba)),10)

    def test_panels_have_transparent_corners_and_native_dimensions(self):
        for scale in (.85,1,1.2,1.5,2):
            width,height,rgba = pixels(rounded_png(40*scale,30*scale,8*scale,'#101827'))
            self.assertEqual((width,height),(round(40*scale),round(30*scale)))
            self.assertEqual(rgba[0][3],0)
            self.assertTrue(any(0<p[3]<255 for p in rgba))


"""Pixel equivalence for accelerated rounded shapes, including DPI and thin bars."""
import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from shapes import rounded_png

CASES = [
    ((350, 262, 24, '#080d17', '', '', 1), '7c44888acb43901ebddae7c6e21444ff2066b20766aee00c6d2cb8fa4dfc7fa3'),
    ((700, 520, 44, '#101827', '#29364c', '', 2), '3d3dbdbba2b37ef0506a7e0058a4ae255040320ac35f68c70b09b412edb202b9'),
    ((306, 7, 3, '#27334a', '', '#101827', 1), 'f52c64b968a7bb62d92b668b69948691784205e8d3edc7eedf6451a8c6b4f9bc'),
    ((6.12, 7, 3, '#8b9dff', '', '#101827', 1), 'a58c984aaf5e80af991f363a57daee28f893f462f1ebcb8acc1d975c6ff22b2b'),
    ((32, 32, 16, '#f3a9ce', '#ffffff', '#101827', 1), '2486a4c366bf5a88c46d8685377e664076043ad6ec0fa38b86ea8951c75c0f9f'),
    ((1, 7, 3, '#ffffff', '', '', 1), '3605fcc5a3335ea7fff0b9c3443c5697a2e8a123e27b1c0e41369015647622b1'),
    ((35, 21, 10.5, '#abcdef', '#123456', '', 1.5), '9ff0e18d80175efbaa26739c96778dcce03a850ea1f9cb3141c7823559c953ba'),
    ((23.8, 23.8, 11.9, '#abcdef', '#123456', '#101827', 0.85), 'f430874a76a4955a69bf506b56d18d5d4c49adeebde984677df033e9a60762a7'),
 ]

class ShapePixelsTests(unittest.TestCase):
    def test_accelerated_shapes_preserve_original_pixels(self):
        for arguments,expected in CASES:
            with self.subTest(arguments=arguments):
                self.assertEqual(hashlib.sha256(rounded_png(*arguments)).hexdigest(),expected)

    def test_large_background_only_calculates_corner_distances(self):
        import math
        from unittest.mock import patch
        rounded_png.cache_clear()
        with patch('shapes.math.hypot',wraps=math.hypot) as distance:
            rounded_png(700,520,44,'#101827','#29364c')
        self.assertLess(distance.call_count,2500)
