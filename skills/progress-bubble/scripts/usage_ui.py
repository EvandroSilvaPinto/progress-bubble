"""Subscription presentation: card text and image-only bubble quota ring."""
from functools import lru_cache
import math
import struct
import zlib
import tkinter as tk
from tkinter import font as tkfont
from i18n import system_language
from usage_model import view
from usage_source import provider_for


def current_usage(app):
    provider=provider_for(app.data.get('usage_provider'),app.data.get('conversation_url'))
    if provider=='off':return None
    snapshot=getattr(app,'usage_snapshot',None) or app.data.get('usage')
    if not isinstance(snapshot,dict) or snapshot.get('provider')!=provider:snapshot=None
    return view(snapshot,getattr(app,'usage_window','primary'),lang=system_language())


def toggle_usage(app):
    state=current_usage(app)
    if state:app.usage_window='secondary' if state['key']=='primary' else 'primary'
    app.draw()


def draw_usage(app,state):
    app.text(23,177,state['label'],7.5,app.theme.get('links'),tags='usage',translate=False)
    app.text(329,177,state['detail'],7.5,app.theme.get('muted'),anchor='ne',translate=False)
    app.rounded(23,192,329,196,2,app.theme['track'],'progress')
    if state['used']:
        app.rounded(23,192,23+306*state['used']/100,196,2,state['color'],'progress')


@lru_cache(maxsize=16)
def quota_ring_png(percent,color,scale,track):
    size=max(32,round(84*scale));factor=size/84;pixels=bytearray()
    color=color or track
    accent,empty=[tuple(int(value[i:i+2],16) for i in (1,3,5)) for value in (color,track)]
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            dx,dy=(x+.5)/factor-42,(y+.5)/factor-42
            alpha=max(0,min(1,(1.15-abs(math.hypot(dx,dy)-39))*factor+.5))
            angle=math.atan2(dx,-dy)%math.tau
            rgb=accent if percent is not None and percent>0 and angle<=math.tau*percent/100 else empty
            pixels.extend((*rgb,round(alpha*255)))
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')


def draw_usage_ring(app,state):
    app.quota_image=tk.PhotoImage(data=quota_ring_png(state['used'],state['color'],app.layout['bubble'],app.theme['track']))
    app.canvas.create_image(app.layout['bubble_x'],app.layout['bubble_y'],image=app.quota_image,anchor='nw',tags='bubble')


def compact_message(text,measure,width):
    text=' '.join(str(text).split())
    if measure(text)<=width:return text
    low,high=0,len(text)
    while low<high:
        middle=(low+high+1)//2
        if measure(text[:middle]+'…')<=width:low=middle
        else:high=middle-1
    return text[:low].rstrip()+'…'


def draw_usage_message(app,text):
    scale=app.layout['card']
    font=tkfont.Font(root=app.root,font=('Segoe UI',-max(1,round(8*scale*96/72))))
    fitted=compact_message(text,font.measure,302*scale)
    app.text(23,205,fitted,8,app.theme['message'],width=302,translate=False)
