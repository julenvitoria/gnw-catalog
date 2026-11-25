#!/usr/bin/env python3
"""Make the catalog's logo, img/logo.svg: a Game & Watch (The Legend of
Zelda edition: green rim, buttons in a row, GAME/TIME/PAUSE on the right),
drawn like DOS G&W Imager's logos, whose LCD-style screen shows a 2x2 grid of
app tiles.

  python3 tools/make_logo.py

No brand names or logos are drawn: the plate above the D-pad has no lettering.
"""
import os

GOLD_HI, GOLD, GOLD_LO, GOLD_EDGE = "#f6e4a6", "#e7cd78", "#c9a74e", "#a8873a"
GREEN, GREEN_DARK = "#2d9a4a", "#1f7436"
LCD_BG, LCD_FG = "#b9c7a0", "#26301f"
RED_HI, RED_LO = "#ff6a63", "#b4201d"
GREY = "#8e949d"


W, H = 96, 54
# the screen (inside the green bezel)
SX, SY, SW, SH = 33, 12.5, 30, 23
CX, CY = SX + SW / 2, SY + SH / 2


def screen_art(kind):
    # a 2x2 grid of app tiles: the catalog
    w, h, g = 9.4, 7.6, 2.2
    x0, y0 = CX - w - g / 2, CY - h - g / 2
    tiles = []
    for r in range(2):
        for c in range(2):
            x, y = x0 + c * (w + g), y0 + r * (h + g)
            tiles.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" rx="1.6" fill="{LCD_FG}"/>'
                         f'<rect x="{x + 2.2:.2f}" y="{y + 2:.2f}" width="{w - 4.4:.2f}" height="{h - 4:.2f}" rx=".8" fill="{LCD_BG}"/>')
    return "\n  ".join(tiles)


def pill(x, y, w, h):
    return (f'<rect x="{x - .8}" y="{y - .8}" width="{w + 1.6}" height="{h + 1.6}" rx="{(h + 1.6) / 2}" fill="{GREEN}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{GREY}"/>')


def red(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="4.3" fill="{GREEN}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="3.3" fill="url(#btn)"/>')


def logo(kind, label):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="G&amp;W Catalog">
  <defs>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GOLD_HI}"/><stop offset=".55" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD_LO}"/>
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fbedbd"/><stop offset="1" stop-color="#e2c56d"/>
    </linearGradient>
    <radialGradient id="btn" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="{RED_HI}"/><stop offset="1" stop-color="{RED_LO}"/></radialGradient>
  </defs>
  <!-- case: green rim, gold face -->
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{GREEN}" stroke="{GREEN_DARK}" stroke-width=".6"/>
  <rect x="2.4" y="2.4" width="{W - 4.8}" height="{H - 4.8}" rx="4.6" fill="url(#body)" stroke="{GOLD_EDGE}" stroke-width=".5"/>
  <rect x="4" y="3.6" width="{W - 8}" height="2.2" rx="1.1" fill="#fff" opacity=".3"/>
  <!-- the plate above the D-pad (no lettering) -->
  <rect x="7.5" y="8" width="15" height="10" rx="1.6" fill="#e6e8ec" stroke="#9aa0a8" stroke-width=".5"/>
  <rect x="9.3" y="10" width="11.4" height="1.5" rx=".6" fill="#3a3f47"/>
  <rect x="12.5" y="12.3" width="5" height="1.3" rx=".6" fill="#3a3f47"/>
  <rect x="9.3" y="14.4" width="11.4" height="1.5" rx=".6" fill="#3a3f47"/>
  <!-- D-pad in its green frame -->
  <rect x="6.5" y="28.5" width="17" height="17" rx="3.4" fill="{GREEN}"/>
  <rect x="8" y="30" width="14" height="14" rx="2.4" fill="#d9bd66"/>
  <rect x="12.9" y="30.8" width="4.2" height="12.4" rx=".8" fill="#16181d"/>
  <rect x="8.8" y="34.9" width="12.4" height="4.2" rx=".8" fill="#16181d"/>
  <circle cx="15" cy="37" r=".9" fill="#2c3038"/>
  <!-- the screen panel, green bezel, LCD -->
  <rect x="27" y="5.5" width="42" height="43" rx="3" fill="url(#panel)" stroke="{GOLD_EDGE}" stroke-width=".4"/>
  <rect x="35" y="7.6" width="26" height="1.4" rx=".7" fill="{GOLD_EDGE}" opacity=".55"/>
  <rect x="{SX - 2.6}" y="{SY - 2.6}" width="{SW + 5.2}" height="{SH + 5.2}" rx="2.6" fill="{GREEN}"/>
  <rect x="{SX}" y="{SY}" width="{SW}" height="{SH}" rx="1" fill="{LCD_BG}"/>
  {screen_art(kind)}
  <rect x="39.5" y="41.6" width="17" height="4.4" rx="2.2" fill="none" stroke="#3a3f47" stroke-width=".7" opacity=".7"/>
  <!-- GAME, TIME, PAUSE/SET -->
  {pill(78, 7.5, 8, 3)}
  {pill(78, 13.3, 8, 3)}
  {pill(78, 19.1, 8, 3)}
  <!-- SELECT and START on their green bar -->
  <rect x="71.5" y="26.5" width="21" height="6.6" rx="3.3" fill="{GREEN}"/>
  <rect x="73.2" y="28.2" width="7.6" height="3.2" rx="1.6" fill="#c9cdd2"/>
  <rect x="83.2" y="28.2" width="7.6" height="3.2" rx="1.6" fill="#c9cdd2"/>
  <!-- B, A -->
  {red(76.8, 42.3)}
  {red(87.2, 42.3)}
</svg>
"""


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img", "logo.svg")
    with open(out, "w") as fh:
        fh.write(logo("catalog", "Catalog"))
    print("img/logo.svg written")
