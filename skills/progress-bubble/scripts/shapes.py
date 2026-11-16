"""Native-resolution antialiased UI shapes without external dependencies."""
from functools import lru_cache
import math
import struct
import zlib


def rgb(color):
    return tuple(int(color[i:i+2],16) for i in (1,3,5))


@lru_cache(maxsize=96)
def rounded_png(width, height, radius, fill, border='', backing='', stroke=1):
    width, height = max(1,round(width)), max(1,round(height))
    radius = max(0,min(radius,width/2,height/2))
    inside, edge = rgb(fill), rgb(border or fill)
    background = rgb(backing) if backing else (0,0,0)
    # Only corners vary in both axes. Build their top-left pixels once,
    # mirror them, and repeat the solid spans instead of visiting every pixel.
    corner = min(math.ceil(radius), width//2)

    def row(y):
        def pixel(x):
            dx = abs(x+.5-width/2)-(width/2-radius)
            dy = abs(y+.5-height/2)-(height/2-radius)
            distance = math.hypot(max(dx,0),max(dy,0))+min(max(dx,dy),0)-radius
            coverage = max(0,min(1,.5-distance))
            inner = max(0,min(1,.5-distance-stroke)) if border else 1
            color = tuple(round(a+(b-a)*inner) for a,b in zip(edge,inside))
            if backing:
                color = tuple(round(a+(b-a)*coverage) for a,b in zip(background,color))
                alpha = 255
            else:
                alpha = round(coverage*255)
            return bytes((*color,alpha))
        left = [pixel(x) for x in range(corner)]
        middle = pixel(corner)*(width-2*corner) if width>2*corner else b''
        return b'\0'+b''.join(left)+middle+b''.join(reversed(left))

    top_count = min(math.ceil(radius),height//2)
    top = [row(y) for y in range(top_count)]
    middle = row(top_count)*(height-2*top_count) if height>2*top_count else b''
    pixels = b''.join(top)+middle+b''.join(reversed(top))

    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(bytes(pixels)))+chunk(b'IEND',b''))
