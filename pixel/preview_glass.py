#!/usr/bin/env python3
"""預覽「球棒敲碎玻璃」：把 app 裡 ShatteredLiquidGlassOverlay 的畫法照搬到 Python，
疊在小工具（桌布底圖 + 火星人）上，輸出球棒 8 格的模擬圖。

用法：python3 pixel/preview_glass.py <空白主畫面截圖.png>  →  pixel/out/bat-glass-preview.png
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

import generate as g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLOT = (620, 1447, 483)                 # 右下那一格在截圖上的位置與邊長（像素）
CROP = (11, 14, 89, 105)                # 圖片裁掉四周空白後的範圍（和輸出到 app 的一致）
IMPACT = (0.22, 0.65)                   # 球棒落點在小工具上的相對位置
PX = SLOT[2] / 164.0                    # 截圖上每 1 pt 是幾個像素
SS = 3                                  # 先畫大再縮小，線條才平滑

PRIMARY = [
    (-2.94, [(0.06, 0.08), (0.14, -0.14), (0.29, 0.11), (0.52, -0.07), (0.86, 0.05)]),
    (-2.38, [(0.05, -0.11), (0.13, 0.16), (0.26, -0.09), (0.48, 0.14), (0.78, -0.06)]),
    (-1.86, [(0.07, 0.12), (0.17, -0.08), (0.35, 0.15), (0.64, -0.10)]),
    (-1.32, [(0.05, -0.09), (0.15, 0.13), (0.31, -0.16), (0.55, 0.08)]),
    (-0.62, [(0.06, 0.14), (0.16, -0.11), (0.34, 0.09), (0.68, -0.12)]),
    (0.08, [(0.05, -0.12), (0.14, 0.09), (0.30, -0.14), (0.58, 0.07)]),
    (0.72, [(0.06, 0.09), (0.18, -0.15), (0.38, 0.12), (0.74, -0.08)]),
    (1.38, [(0.05, -0.13), (0.14, 0.11), (0.28, -0.08), (0.56, 0.13)]),
    (2.04, [(0.07, 0.10), (0.19, -0.14), (0.41, 0.09), (0.84, -0.11)]),
    (2.58, [(0.06, -0.08), (0.16, 0.15), (0.36, -0.12), (0.76, 0.09), (1.02, -0.05)]),
]


def glass(size, flash):
    """回傳一張透明底的碎玻璃圖層（size×size 像素）。"""
    S = size * SS
    k = PX * SS                                        # 1 pt 對應的繪圖像素
    cx, cy = S * IMPACT[0], S * IMPACT[1]
    reach = math.hypot(S, S)
    out = Image.new("RGBA", (S, S))

    def radial(r, stops):
        layer = Image.new("RGBA", (S, S))
        d = ImageDraw.Draw(layer)
        steps = 40
        for i in range(steps, 0, -1):
            t = i / steps
            # 線性內插顏色
            for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
                if t0 <= t <= t1:
                    u = (t - t0) / (t1 - t0)
                    col = tuple(round(c0[j] + (c1[j] - c0[j]) * u) for j in range(4))
                    break
            d.ellipse([cx - r * t, cy - r * t, cx + r * t, cy + r * t], fill=col)
        return layer

    if flash:
        out.alpha_composite(radial(reach * 0.42, [(0, (255, 255, 255, 133)), (0.5, (209, 242, 255, 46)), (1, (255, 255, 255, 0))]))

    segs, chains = [], []
    for idx, (ang, steps) in enumerate(PRIMARY):
        prev, nodes, cur = (cx, cy), [(cx, cy)], ang
        for si, (frac, bend) in enumerate(steps):
            cur += bend
            nxt = (cx + math.cos(cur) * reach * frac, cy + math.sin(cur) * reach * frac)
            prog = si / max(1, len(steps))
            w, al = 2.15 * (1 - prog * 0.72), 0.96 - prog * 0.34
            segs.append((prev, nxt, w, al))
            nodes.append(nxt)
            if si in (1, 2) or (si == 3 and idx % 2 == 0):
                sign = 1.0 if (idx + si) % 2 == 0 else -1.0
                fa = cur + sign * (0.34 + si * 0.06)
                mid = (nxt[0] + math.cos(fa) * reach * 0.09, nxt[1] + math.sin(fa) * reach * 0.09)
                tip = (mid[0] + math.cos(fa - sign * 0.14) * reach * 0.10, mid[1] + math.sin(fa - sign * 0.14) * reach * 0.10)
                segs.append((nxt, mid, w * 0.56, al * 0.78))
                segs.append((mid, tip, 0.42, al * 0.52))
            prev = nxt
        chains.append(nodes)

    d = ImageDraw.Draw(out, "RGBA")
    shards = Image.new("RGBA", (S, S))
    sd = ImageDraw.Draw(shards)
    for i in range(len(chains)):
        j = (i + 1) % len(chains)
        if len(chains[i]) > 3 and len(chains[j]) > 3:
            a1, a2, b1, b2 = chains[i][1], chains[i][2], chains[j][1], chains[j][2]
            if i % 3 != 1:
                segs.append((a1, b2 if i % 2 == 0 else b1, 0.85, 0.68))
            if i % 3 == 0:
                sd.polygon([a1, a2, b2, b1], fill=(235, 248, 255, 32))
            elif i % 3 == 1:
                sd.polygon([a1, a2, b2, b1], fill=(0, 0, 0, 23))
    out.alpha_composite(shards)

    for layer_no in range(3):                          # 陰影 → 冷白切面 → 白色裂線
        layer = Image.new("RGBA", (S, S))
        ld = ImageDraw.Draw(layer)
        for p0, p1, w, al in segs:
            if layer_no == 0:
                off, col, lw = (0.8 * k, 1.3 * k), (0, 0, 0, round(255 * al * 0.42)), (w + 0.6) * k
            elif layer_no == 1:
                if w <= 0.9:
                    continue
                off, col, lw = (-1.1 * k, -0.8 * k), (184, 240, 255, round(255 * al * 0.55)), w * 1.35 * k
            else:
                off, col, lw = (0, 0), (255, 255, 255, round(255 * al)), w * k
            ld.line([(p0[0] + off[0], p0[1] + off[1]), (p1[0] + off[0], p1[1] + off[1])], fill=col, width=max(1, round(lw)))
        out.alpha_composite(layer)

    crater = max(7.0 * k, reach * 0.048)
    out.alpha_composite(radial(crater * 1.5, [(0, (255, 255, 255, 199)), (0.5, (219, 242, 255, 82)), (1, (255, 255, 255, 0))]))
    web = Image.new("RGBA", (S, S))
    wd = ImageDraw.Draw(web)
    for n in range(7):
        a = n * 0.92 + 0.2
        r1 = crater * (0.45 + (n % 3) * 0.28)
        pa = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        pb = (cx + math.cos(a + 1.1) * r1 * 0.85, cy + math.sin(a + 1.1) * r1 * 0.85)
        wd.polygon([(cx, cy), pa, pb], fill=(255, 255, 255, 115 if n % 2 == 0 else 56))
        wd.line([(cx, cy), pa, pb, (cx, cy)], fill=(255, 255, 255, 235), width=max(1, round(0.75 * k)))
    out.alpha_composite(web)
    return out.resize((size, size), Image.LANCZOS)


def main():
    shot = Image.open(sys.argv[1]).convert("RGBA")
    x0, y0, S = SLOT
    bg = shot.crop((x0, y0, x0 + S, y0 + S))
    scale = (S - 12) / (CROP[3] - CROP[1])
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=round(24 * PX), fill=255)
    sheet = Image.new("RGB", ((S + 16) * 4 + 16, (S + 56) * 2 + 16), (20, 23, 32))
    dr = ImageDraw.Draw(sheet)
    notes = ["1 舉棒", "2 往後拉", "3 蓄力", "4 擊中：閃光＋玻璃碎裂", "5 裂痕留著", "6 裂痕留著", "7 收棒", "8 回到預備"]
    for i in range(8):
        tile = bg.copy()
        sp = g.to_image(g.render(g.DESIGN_MV, g.anim_bat(i / 8))).crop(CROP)
        sp = sp.resize((round(sp.width * scale), round(sp.height * scale)), Image.NEAREST)
        tile.alpha_composite(sp, ((S - sp.width) // 2, (S - sp.height) // 2))
        if i >= 3:
            tile.alpha_composite(glass(S, flash=(i == 3)))
        x, y = 16 + (i % 4) * (S + 16), 16 + (i // 4) * (S + 56)
        sheet.paste(tile.convert("RGB"), (x, y + 40), mask)
        dr.text((x + 6, y + 4), notes[i], font=g.font(26), fill=(240, 240, 245))
    path = os.path.join(ROOT, "pixel", "out", "bat-glass-preview.png")
    sheet.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()
