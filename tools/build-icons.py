#!/usr/bin/env python3
"""
Build the full ENYT square icon set from the brand wordmark typeface.

Design: "EN" in off-white over "YT" in amber, on the dark brand field with the
same 12.5% corner radius as the existing favicon. Chosen because it stays legible
at 32px (browser tab) while still reading as ENYT at 512px, which is the size
Google News shows a publisher logo at.

Outputs into the repo root:
  favicon.svg            vector, glyphs converted to paths (no font dependency)
  favicon.png            512x512  - also serves as the Google News publisher logo
  favicon.ico            16/32/48 multi-resolution
  apple-touch-icon.png   180x180
  enyt-square-512.png    512x512 copy for LION / Project Oasis uploads
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

# Clash Display Bold, the same face as the ENYT wordmark. Download once with:
#   curl -sL -o /tmp/clash700.ttf "$(curl -s 'https://api.fontshare.com/v2/css?f[]=clash-display@700' \
#     | grep -o 'https\?://[^)]*\.ttf' | head -1)"
FONT_PATH = os.environ.get("CLASH_TTF", "/tmp/clash700.ttf")
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DARK = (13, 17, 23, 255)
AMBER = (232, 149, 42, 255)
OFFWHITE = (230, 237, 243, 255)
DARK_HEX, AMBER_HEX, OFFWHITE_HEX = "#0d1117", "#e8952a", "#e6edf3"

S = 1024
RADIUS_PCT = 0.125


# ───────────────────────── raster ─────────────────────────
def fit(text, target_w, start=560):
    size = start
    while size > 10:
        f = ImageFont.truetype(FONT_PATH, size)
        b = f.getbbox(text)
        if b[2] - b[0] <= target_w:
            return f
        size -= 4
    return ImageFont.truetype(FONT_PATH, 10)


def centered(d, text, font, y_center, fill):
    b = d.textbbox((0, 0), text, font=font)
    w, h = b[2] - b[0], b[3] - b[1]
    d.text((S / 2 - w / 2 - b[0], y_center - h / 2 - b[1]), text, font=font, fill=fill)


def render(size=S):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * RADIUS_PCT), fill=DARK)
    f = fit("EN", int(S * 0.60), 560)
    centered(d, "EN", f, S * 0.34, OFFWHITE)
    centered(d, "YT", f, S * 0.68, AMBER)
    if size != S:
        img = img.resize((size, size), Image.LANCZOS)
    return img


# ───────────────────────── vector ─────────────────────────
def svg_paths():
    """Convert EN / YT to SVG path data so the icon needs no webfont."""
    tt = TTFont(FONT_PATH)
    gs = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    hmtx = tt["hmtx"]
    glyf = tt["glyf"]

    def line_path(text):
        """Return per-glyph paths, total advance, and the real ink bounding box
        in font units, so placement uses measured metrics rather than a guess."""
        pen_paths, advance = [], 0
        ymin, ymax, xmin, xmax = None, None, None, None
        for ch in text:
            gname = cmap[ord(ch)]
            pen = SVGPathPen(gs)
            gs[gname].draw(pen)
            pen_paths.append((pen.getCommands(), advance))
            g = glyf[gname]
            if g.numberOfContours:
                gx0, gy0, gx1, gy1 = g.xMin, g.yMin, g.xMax, g.yMax
                lo, hi = advance + gx0, advance + gx1
                xmin = lo if xmin is None else min(xmin, lo)
                xmax = hi if xmax is None else max(xmax, hi)
                ymin = gy0 if ymin is None else min(ymin, gy0)
                ymax = gy1 if ymax is None else max(ymax, gy1)
            advance += hmtx[gname][0]
        return pen_paths, advance, (xmin, ymin, xmax, ymax)

    return line_path


def build_svg(path):
    line_path = svg_paths()
    VB = 512
    r = VB * RADIUS_PCT

    def line_group(text, colour, target_w, cy):
        paths, _adv, (xmin, ymin, xmax, ymax) = line_path(text)
        ink_w = xmax - xmin
        ink_h = ymax - ymin
        scale = target_w / ink_w
        # place using the measured ink box so the visual centre lands on cy
        x0 = VB / 2 - (ink_w * scale) / 2 - xmin * scale
        y0 = cy + (ink_h * scale) / 2 + ymin * scale
        out = [f'  <g fill="{colour}" transform="translate({x0:.3f} {y0:.3f}) '
               f'scale({scale:.6f} {-scale:.6f})">']
        for cmds, off in paths:
            out.append(f'    <path transform="translate({off} 0)" d="{cmds}"/>')
        out.append("  </g>")
        return "\n".join(out)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" role="img" aria-label="East New York Times">
  <rect width="{VB}" height="{VB}" rx="{r:.1f}" fill="{DARK_HEX}"/>
{line_group("EN", OFFWHITE_HEX, VB * 0.60, VB * 0.34)}
{line_group("YT", AMBER_HEX, VB * 0.60, VB * 0.68)}
</svg>
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)


# ───────────────────────── main ─────────────────────────
def main():
    master = render()

    png512 = master.resize((512, 512), Image.LANCZOS)
    png512.save(os.path.join(REPO, "favicon.png"))
    png512.save(os.path.join(REPO, "enyt-square-512.png"))

    master.resize((180, 180), Image.LANCZOS).save(
        os.path.join(REPO, "apple-touch-icon.png"))

    # multi-resolution .ico built from individually downsampled frames
    frames = [master.resize((n, n), Image.LANCZOS) for n in (48, 32, 16)]
    frames[0].save(os.path.join(REPO, "favicon.ico"),
                   sizes=[(48, 48), (32, 32), (16, 16)])

    build_svg(os.path.join(REPO, "favicon.svg"))

    for f in ("favicon.png", "favicon.ico", "favicon.svg",
              "apple-touch-icon.png", "enyt-square-512.png"):
        p = os.path.join(REPO, f)
        print(f"  {f:24} {os.path.getsize(p)/1024:6.1f} KB")

    # QA sheet: every size that will actually be seen
    sizes = [512, 180, 96, 64, 48, 32, 16]
    pad = 24
    w = pad + sum(s + pad for s in sizes)
    sheet = Image.new("RGB", (w, 512 + pad * 2 + 34), (24, 26, 30))
    d = ImageDraw.Draw(sheet)
    lf = ImageFont.truetype(FONT_PATH, 22)
    x = pad
    for s in sizes:
        im = master.resize((s, s), Image.LANCZOS)
        sheet.paste(im, (x, pad + (512 - s)), im)
        d.text((x, pad + 512 + 8), f"{s}px", font=lf, fill=(190, 196, 204))
        x += s + pad
    out = os.path.join(REPO, "tools", "_icon-qa-preview.png")
    sheet.save(out)
    print(f"  QA sheet -> {out}")


if __name__ == "__main__":
    main()
