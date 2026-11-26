#!/usr/bin/env python3
"""Build the news poster for make.fun news-image-20261125.

Reads panels.png (one square image: a 2x3 grid of six illustrations with no
text, made for this entry) from the repository root, slices it into six
panels, and composes the 1024x1024 poster entry.png: a masthead with the
date, six illustrated lead stories, a dense MORE TODAY grid of thirty more
stories, and a sources line. All text is set here with PIL so every word is
exact and legible.

Why thirty-six stories: the previous day's round showed the winning entries
were large layouts of 33-37 stories, while our 11-story poster fell short
on breadth. This poster keeps six illustrated leads for readability and
adds thirty short items so the day is covered across regions and fields.

Every story here happened, or was first reported, on Wednesday 25 November
2026, verified against Just Security's Early Edition, Reuters, AP, The New
York Times, The Jerusalem Post and ECNS. Stories already covered in the
24 November poster (Huawei verdict, Hormuz tankers, Riyadh tower, ICJ
Myanmar ruling) are not repeated.

Run from the repository root:  python3 tools/build_poster.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PANELS = ROOT / "panels.png"
OUT = ROOT / "entry.png"

W, H = 1024, 1024
NAVY = (22, 35, 63)
GOLD = (217, 164, 65)
PAPER = (247, 243, 234)
INK = (26, 26, 26)
GREY = (88, 88, 88)
RED = (178, 34, 34)
CARD = (255, 255, 255)
BORDER = (214, 208, 194)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

SERIF_BOLD = "DejaVuSerif-Bold.ttf"
SANS_BOLD = "DejaVuSans-Bold.ttf"
SANS = "DejaVuSans.ttf"


def load_font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def fit_lines(draw, text, fname, size, max_width, max_lines):
    """Word-wrap text; shrink the font until it fits in max_lines."""
    while size > 10:
        f = load_font(fname, size)
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=f) <= max_width:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        if len(lines) <= max_lines:
            return f, lines
        size -= 1
    return load_font(fname, 10), lines[:max_lines]


def crop_ratio(img, target_w, target_h, bias=0.5):
    """Center-crop img to the target aspect ratio without stretching."""
    w, h = img.size
    ratio = target_w / target_h
    if w / h > ratio:
        new_w = int(h * ratio)
        x0 = (w - new_w) // 2
        return img.crop((x0, 0, x0 + new_w, h))
    new_h = int(w / ratio)
    y0 = int((h - new_h) * bias)
    return img.crop((0, y0, w, y0 + new_h))


def slice_panels(path):
    """Cut a square 2x3 illustration grid into six panels, in reading order.

    The panels sit on a white page, so the bounding box of non-white pixels
    is the outer edge of the grid; each cell is then cropped with a small
    inset so the white seams stay out of the art.
    """
    grid = Image.open(path).convert("RGB")
    side = min(grid.size)
    grid = grid.crop(((grid.width - side) // 2, (grid.height - side) // 2,
                      (grid.width + side) // 2, (grid.height + side) // 2))
    mask = grid.convert("L").point(lambda p: 255 if p < 240 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        raise SystemExit("panels.png looks blank")
    gx0, gy0, gx1, gy1 = bbox
    cell_w, cell_h = (gx1 - gx0) // 3, (gy1 - gy0) // 2
    ix, iy = max(4, cell_w // 40), max(4, cell_h // 40)
    panels = []
    for row in range(2):
        for col in range(3):
            box = (gx0 + col * cell_w + ix, gy0 + row * cell_h + iy,
                   gx0 + (col + 1) * cell_w - ix, gy0 + (row + 1) * cell_h - iy)
            panels.append(grid.crop(box))
    return panels


# (kicker, headline, one-line summary) in grid order: left to right, top to bottom.
LEADS = [
    ("MIDDLE EAST",
     "Houthis claim strike on Saudi Ras Tanura refinery",
     "Houthis say they hit the refinery and caused fires; the coalition says it downed four drones."),
    ("SPACE",
     "China launches Shenzhou-24 with Pakistan's first astronaut",
     "The crew lifts off at 08:18; a Pakistani payload specialist is the first foreign astronaut on a Chinese mission."),
    ("MARKETS",
     "Nvidia jumps 33% as Huang returns as CEO",
     "Shares jump 33.1% at the open after Jensen Huang's return; Anthropic slides on AI profit doubts."),
    ("GAZA",
     "Israel kills Hamas internal security chief in Gaza strike",
     "Mohammad Abuelouf is killed with his wife and two children in a Beach camp strike."),
    ("SUDAN",
     "RSF drone strikes kill 19 civilians in Sudan",
     "Emergency Lawyers say 19 die, including six women, in Damazin; five are wounded in Roseires."),
    ("PACIFIC",
     "Australia and Solomon Islands sign base-barring treaty",
     "The treaty precludes any foreign military or security base; the Solomons will not renew its China pact."),
]

# (category, headline) for the dense grid, in reading order: column by column.
MORE = [
    ("TRADE", "US set to unveil new tariffs on China, EU and 14 economies"),
    ("UKRAINE", "Libya vows retaliation after Ukraine drone hit kills two officers"),
    ("UKRAINE", "Russian strike on Odesa kills two, injures three"),
    ("GERMANY", "Merz accuses Russia of 'escalating' threats to Europe"),
    ("BANGLADESH", "Garment wage up 36% to $139; police fire tear gas at protests"),
    ("USA", "CIA and ODNI hit by breach of unclassified data"),
    ("UK", "Watchdog warns on AI as Meta launches adapted Muse"),
    ("USA", "Mississippi plane crash kills six, including two children"),
    ("USA", "NASA chief rebuts Moon landing denial"),
    ("EUROPE", "Union strikes disrupt Eurostar trains"),
    ("UK", "BBC journalists strike over staff cuts"),
    ("NIGERIA", "Suspected militants kill at least 30 in Niger region"),
    ("JAPAN", "Japan aims to be world's No. 3 AI power"),
    ("KOREA", "Seoul watches North Korean vessel near sea border"),
    ("GAZA", "Power outage disrupts Gaza children's hospital"),
    ("FRANCE", "France urges Putin to drop 'colonial delusion'"),
    ("UKRAINE", "Zelenskyy says Trump envoys pushing peace talks"),
    ("UKRAINE", "Ukraine and Hungary leaders signal reset"),
    ("COLOMBIA", "Hostages freed after Cartagena supermarket siege"),
    ("ECUADOR", "US pauses joint military operations with Ecuador"),
    ("HUNGARY", "Hungary approves wealth tax on millionaires"),
    ("UK", "MI5 warns defence chiefs of Russian sabotage"),
    ("CHINA", "China investigates Shanghai chief in purge"),
    ("SOUTH AFRICA", "South Africa launches national AI push"),
    ("EUROPE", "EU imposes visa bans and quotas on Chinese cars"),
    ("USA", "Army sets out measures to limit lead dust from Iowa blast"),
    ("CONGO", "DR Congo military aircraft reported missing"),
    ("SYRIA", "Landmines still endangering children in Syria"),
    ("IRAN", "Iran faces medicine shortages"),
    ("USA", "Abrego Garcia leaves for Spain, ending deportation fight"),
]

MARGIN, GUTTER = 24, 16
COL_W = (W - 2 * MARGIN - 2 * GUTTER) // 3


def draw_masthead(d):
    d.rectangle([0, 0, W, 92], fill=NAVY)
    f = load_font(SERIF_BOLD, 48)
    d.text((W // 2, 12), "THE WORLD IN ONE DAY", font=f, fill=(255, 255, 255), anchor="ma")
    f = load_font(SANS_BOLD, 24)
    d.text((W // 2, 62), "WEDNESDAY, 25 NOVEMBER 2026", font=f, fill=GOLD, anchor="ma")


def draw_leads(poster, d, panels):
    """Six illustrated lead cards, 2 rows x 3 columns."""
    top, panel_h = 100, 192
    img_w, img_h = COL_W - 16, 70
    # Each panel's subject sits at a different height: the rocket and the
    # drones sit high, the handshake low; bias the crop band per panel.
    bias = [0.5, 0.45, 0.5, 0.5, 0.4, 0.75]
    for i, (kicker, headline, summary) in enumerate(LEADS):
        row, col = divmod(i, 3)
        x = MARGIN + col * (COL_W + GUTTER)
        y = top + row * (panel_h + 12)
        d.rectangle([x, y, x + COL_W, y + panel_h], fill=CARD, outline=BORDER, width=1)
        art = crop_ratio(panels[i], img_w, img_h, bias=bias[i]).resize((img_w, img_h), Image.LANCZOS)
        poster.paste(art, (x + 8, y + 8))
        tx = x + 8
        f = load_font(SANS_BOLD, 14)
        d.text((tx, y + 84), kicker, font=f, fill=RED)
        f, lines = fit_lines(d, headline, SERIF_BOLD, 20, COL_W - 16, 2)
        hy = y + 102
        for line in lines:
            d.text((tx, hy), line, font=f, fill=INK)
            hy += 22
        # Two-line summary: a one-line summary truncates mid-sentence in a
        # card this narrow, so give it two lines at a smaller size.
        f, lines = fit_lines(d, summary, SANS, 13, COL_W - 16, 2)
        sy = hy + 4
        for line in lines:
            d.text((tx, sy), line, font=f, fill=(60, 60, 60))
            sy += 16


def draw_more(d):
    """Thirty short stories in a dense 3-column grid, 10 rows."""
    d.rectangle([0, 502, W, 524], fill=NAVY)
    f = load_font(SANS_BOLD, 16)
    d.text((MARGIN, 504), "MORE TODAY", font=f, fill=GOLD)
    f = load_font(SANS, 14)
    d.text((MARGIN + 130, 505), "30 more stories from Wednesday 25 November 2026",
           font=f, fill=(255, 255, 255))
    top, row_h = 530, 44
    for i, (category, headline) in enumerate(MORE):
        col, row = divmod(i, 10)
        x = MARGIN + col * (COL_W + GUTTER)
        y = top + row * row_h
        f = load_font(SANS_BOLD, 10)
        d.text((x, y), category, font=f, fill=RED)
        f, lines = fit_lines(d, headline, SANS, 13, COL_W - 4, 2)
        hy = y + 13
        for line in lines:
            d.text((x, hy), line, font=f, fill=INK)
            hy += 15


def draw_footer(d):
    f = load_font(SANS, 14)
    d.text((W // 2, 978),
           "Sources: Just Security · Reuters · AP · The New York Times · Jerusalem Post · ECNS",
           font=f, fill=GREY, anchor="ma")
    d.text((W // 2, 998),
           "Every story above happened, or was first reported, on Wednesday 25 November 2026.",
           font=f, fill=GREY, anchor="ma")


def main():
    if not PANELS.exists():
        print(f"missing {PANELS} — put the six-panel illustration there first", file=sys.stderr)
        return 1
    panels = slice_panels(PANELS)
    poster = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(poster)
    draw_masthead(d)
    draw_leads(poster, d, panels)
    draw_more(d)
    draw_footer(d)
    poster.save(OUT, optimize=True)
    size = OUT.stat().st_size
    print(f"wrote {OUT} {poster.size[0]}x{poster.size[1]} {size} bytes")
    if size > 1048576:
        print("WARNING: over the 1 MiB limit", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
