"""Reproducible illustrative feature tour for README; no live task or private QR."""
import io
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont
from render_demo import ROOT, frame, BG, CARD, FG, MUTED, TRACK, ACCENT, GREEN, FONT, BOLD

sys.path.insert(0, str(ROOT/'skills/progress-bubble/scripts'))
from native_qr import qr_png


def scene(kind):
    im = frame(100 if kind == 'parallel' else 65, palette=kind == 'colors', expanded=kind != 'parallel',
               complete=kind == 'parallel').resize((1920, 1080))
    d = ImageDraw.Draw(im)

    def box(bounds, color=CARD, radius=12):
        d.rounded_rectangle(tuple(int(v*2) for v in bounds), radius*2, fill=color)

    def text(x, y, value, size=15, color=FG, bold=False):
        d.text((x*2, y*2), value, fill=color,
               font=ImageFont.truetype(str(Path('C:/Windows/Fonts/seguisym.ttf') if '⚙' in value else BOLD if bold else FONT), size*2))

    titles = {
        'progress': ('01 / PROGRESS', 'Click, drag and return to your chat.'),
        'settings': ('02 / SETTINGS', 'Colors, sizes and optional quota in one menu.'),
        'colors': ('03 / PERSONALIZE', 'Five editable colors. Saved across trackers.'),
        'usage': ('04 / OPTIONAL QUOTA', 'Real limits, separate from task progress.'),
        'qr': ('05 / SHARE ONE TASK', 'Mobile opens the QR inside the same card.'),
        'phone': ('06 / PHONE VIEW', 'Read-only progress. No account required.'),
        'parallel': ('07 / PARALLEL TASKS', 'Separate bubbles. Independent progress.'),
    }
    box((55, 318, 510, 420), BG)
    text(58, 326, titles[kind][0], 13, GREEN, True)
    # Wrap captions explicitly to retain comfortable margins at README width.
    words = titles[kind][1].split()
    lines, line = [], ''
    for word in words:
        if len(line+' '+word) > 42:
            lines.append(line); line = word
        else: line = (line+' '+word).strip()
    lines.append(line)
    for index, line in enumerate(lines): text(58, 358+index*24, line, 17)
    box((55, 482, 670, 515), BG)
    text(58, 489, 'Illustrative tour · sample data · QR is not a live session', 12, MUTED)

    if kind == 'settings':
        box((652, 155, 895, 350), '#263149')
        for y, value in zip((171, 206, 241, 276, 311),
                            ('Colors', 'Sizes  >', 'Card: Small / Medium / Large',
                             'Bubble: Small / Medium / Large', '[ ] Show subscription usage')):
            text(665, y, value, 12)
    elif kind == 'colors':
        text(550, 20, 'Hover for tooltips · choose any shade', 13, MUTED)
        box((538, 369, 895, 400))
        text(542, 376, 'Settings → Reset colors (palette open)', 12, ACCENT)
    elif kind == 'usage':
        box((538, 324, 888, 397))
        text(542, 326, 'Subscription · 5h                       100%', 13, '#ff889e')
        box((542, 352, 877, 358), '#ff889e', 3)
        text(542, 371, 'Renews in 2h 15min', 12, MUTED)
        d.arc((1610, 810, 1818, 1018), -90, 270, fill='#ff889e', width=6)
        text(58, 420, 'Off by default · enable in Settings', 13, MUTED)
    elif kind == 'qr':
        box((519, 124, 900, 402), CARD, 20)
        text(542, 142, 'PROGRESS', 11, MUTED)
        text(766, 142, 'Back    ⚙    ×', 14, ACCENT)
        # Public example URL only; no temporary capability or writer key.
        qr = Image.open(io.BytesIO(qr_png('https://example.org/progress-bubble-demo', 360))).convert('RGB')
        im.paste(qr, ((2840-qr.width)//2, 360))
        text(677, 374, 'Copy link', 12, ACCENT)
    elif kind == 'phone':
        box((510, 35, 920, 520), BG)
        box((610, 40, 865, 516), '#263149', 30)
        box((618, 49, 857, 507), CARD, 25)
        text(645, 93, 'PROGRESS BUBBLE', 13, GREEN, True)
        text(639, 153, 'Preparing report', 21, bold=True)
        text(639, 198, 'In progress', 13, ACCENT)
        text(639, 239, '65%', 42, bold=True)
        box((639, 312, 835, 321), TRACK, 4)
        box((639, 312, 766, 321), ACCENT, 4)
        text(639, 346, 'Reviewing the content.', 13)
        text(639, 392, 'About 3 min left', 13, MUTED)
        text(639, 457, 'Private temporary link', 12, GREEN)
    return im.resize((960, 540), Image.Resampling.LANCZOS)


def main():
    kinds = ('progress', 'settings', 'colors', 'usage', 'qr', 'phone', 'parallel')
    frames = [scene(kind) for kind in kinds]
    # One common palette avoids changing colors between scenes.
    sheet = Image.new('RGB', (1920, 2160), BG)
    for index, image in enumerate(frames):
        sheet.paste(image, ((index % 2)*960, (index//2)*540))
    sheet.save(ROOT/'assets/feature-tour.png', optimize=True)
    palette = sheet.quantize(colors=192)
    animation = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in frames]
    animation[0].save(ROOT/'assets/feature-tour.gif', save_all=True,
                      append_images=animation[1:], duration=2800, loop=0, disposal=2)
    print('Rendered seven feature scenes, GIF and PNG overview.')


if __name__ == '__main__':
    main()
