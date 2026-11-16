#!/usr/bin/env python3
"""第二隻桌寵：白色長耳玩偶的原生像素圖產生器（96×108，和火星人同一套畫法）。

身體是一個直筒：上面兩隻長耳、圓圈眼睛加睫毛、梯形嘴巴、臉下方一道縫線、兩條短腿。
身體用圓角方塊和仿射矩陣在「一格 = 一個像素」的畫布上算出來，眼睛是固定的像素小圖案。
嘴巴要的是平滑的斜線，像素格子畫不出來，所以成品圖放大 4 倍輸出：
身體仍是一格一格的像素（每格變成 4×4），只有嘴巴的梯形用平滑的線畫在上面。

用法：python3 pixel/generate_rabbit.py   →  輸出到 pixel/out/rabbit/
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

import generate as g
from generate import T, R, S, pt, dilate

g.PALETTE.update({
    "fur": (255, 255, 255),         # 白色絨毛
    "fur_sh": (212, 219, 230),      # 右側與下緣的淡淡陰影
})

OUT = os.path.join(g.OUT, "rabbit")
W, H, CX, GROUND = 96, 108, 48.0, 102.0
FRAMES = g.FRAMES

# 造型尺寸（像素）。整體約 28 寬、86 高：耳朵和腿各佔約兩成，耳朵、身體、腿的外緣連成一直線。
# （比玩偶略寬一點，臉上的圓眼睛和嘴巴才畫得清楚。）
BODY = (60.0, 14.0, 25.0, 3.0)      # 身體直筒：中心 y、半寬、半高、圓角 → y 35 ~ 85
EAR = (7.3, 30.0, 6.4, 15.0, 6.0)   # 耳朵：離中線的距離、中心 y、半寬、半高、圓角 → y 15 ~ 45（下半段藏在身體裡）
EAR_PIVOT = 38.0                    # 耳朵繞著這個高度擺動
LEG = (7.3, 90.0, 6.4, 12.0, 4.0)   # 腿：離中線的距離、中心 y、半寬、半高、圓角 → y 78 ~ 102
EYE = (7.0, 43.5)                   # 眼睛：離中線的距離、y（靠近臉的上方）
MOUTH_Y = 57.5                      # 嘴巴中心的高度（y 50 ~ 65），和眼睛隔開一段
STITCH_Y = 68.5                     # 臉下方的縫線

# 左眼的圖案（右眼是鏡像）。k = 黑線，w = 白色
EYE_STAMPS = {
    "open": [
        "...kkkkk..",
        "..kwwwwwk.",
        ".kwwwwwwwk",
        ".kwwwwwwwk",
        ".kwwwwwwwk",
        ".kwwwwwwwk",
        "kkwwwwwwwk",
        "..kwwwwwk.",
        "k..kkkkk..",
    ],
    "closed": [
        "..........",
        "..........",
        "..........",
        "..........",
        "..........",
        ".kkkkkkkkk",
        "..........",
        "..........",
        "..........",
    ],
    "happy": [
        "..........",
        "..........",
        "...kkkkk..",
        "..k.....k.",
        ".k.......k",
        "..........",
        "..........",
        "..........",
        "..........",
    ],
}


MOUTH = (8.0, 12.0, 15.0)           # 嘴巴：瘦高的梯形（上底、下底、高），單位是像素格
HI = 4                              # 成品圖的放大倍率

REST = dict(dy=0, lean=0, squash=1.0, earL=0.0, earR=0.0, eyes="open", look=0, legL=0, legR=0, blush=False)


def render_pixels(pose=None):
    """畫出像素的部分（原生 96×108）：身體、耳朵、腿、眼睛、縫線、外框。嘴巴另外畫。"""
    p = dict(REST)
    if pose:
        p.update(pose)
    c = g.Canvas(W, H, list(g.PALETTE))
    dy = round(p["dy"])
    sq = p["squash"]
    body = T(0, dy) @ R(p["lean"], CX, GROUND) @ S(1.0 + (1.0 - sq) * 0.5, sq, CX, GROUND)

    # 1. 腿（抬腳時整條腿往上縮）
    off, lcy, lhw, lhh, lr = LEG
    for part, side, lift in ((1, -1, p["legL"]), (2, 1, p["legR"])):
        c.paint(c.box(body, CX + side * off, lcy - lift / 2, lhw, lhh - lift / 2, lr), "fur", part)
    # 2. 耳朵（各自繞著根部擺動）
    off, ecy, ehw, ehh, er = EAR
    for part, side, ang in ((3, -1, p["earL"]), (4, 1, p["earR"])):
        ear = body @ R(ang, CX + side * off, EAR_PIVOT)
        c.paint(c.box(ear, CX + side * off, ecy, ehw, ehh, er), "fur", part)
    # 3. 身體直筒
    bcy, bhw, bhh, br = BODY
    c.paint(c.box(body, CX, bcy, bhw, bhh, br), "fur", 5)

    # 4. 陰影：右緣兩格、下緣一格
    fur = c.col == c.idx["fur"]
    empty = c.col == 0
    right = np.zeros_like(fur)
    right[:, :-1] |= empty[:, 1:]
    right[:, :-2] |= empty[:, 2:]
    below = np.zeros_like(fur)
    below[:-1, :] |= empty[1:, :]
    c.col[fur & (right | below)] = c.idx["fur_sh"]

    # 5. 臉：眼睛和嘴巴都是固定的小圖案，位置跟著身體移動，圖案本身不旋轉
    legend = {"k": "ink", "w": "fur"}
    ex, ey = EYE
    for side in (-1, 1):
        rows = EYE_STAMPS[p["eyes"]]
        if side == 1:
            rows = [r[::-1] for r in rows]                     # 右眼左右對稱
        c.stamp(rows, *pt(body, CX + side * ex + p["look"], ey), legend, 6)
    # 臉下方的縫線：微微下彎的虛線
    for i, x in enumerate(np.arange(-10.5, 11.0, 1.0)):
        if i % 3 == 2:
            continue
        q = pt(body, CX + x, STITCH_Y + 1.6 * (1 - (x / 10.5) ** 2))
        c.paint(c.capsule(q, q, 0.55), "ink", 6)
    # 腰側與腳背的小縫線
    for side in (-1, 1):
        hx_, hy_ = pt(body, CX + side * 12.0, 83.0)
        c.paint(c.capsule((hx_, hy_), (hx_ - side * 1.6, hy_ + 1.2), 0.5), "ink", 6)
        fx_, fy_ = pt(body, CX + side * 7.3, 97.0)
        c.paint(c.capsule((fx_ - 0.5, fy_), (fx_ + 0.5, fy_), 0.5), "ink", 6)
    if p["blush"]:
        for side in (-1, 1):
            bx_, by_ = pt(body, CX + side * 10.4, 50.5)
            c.paint(c.ellipse(T(0, 0), bx_, by_, 1.7, 1.0), "skin", 6)

    # 6. 外框
    filled = c.col > 0
    c.col[dilate(filled) & ~filled] = c.idx["line"]
    return c, body, p


def render(pose=None):
    """畫出一格成品圖（放大 HI 倍的 RGBA 圖）：像素身體 + 平滑線條的梯形嘴巴。"""
    c, body, p = render_pixels(pose)
    img = g.to_image(c)
    img = img.resize((W * HI, H * HI), Image.NEAREST)
    # 嘴巴：先畫大 4 倍再縮回來，線條邊緣才平滑。線寬等於一個像素格。
    top, bottom, height = MOUTH
    y0, y1 = MOUTH_Y - height / 2, MOUTH_Y + height / 2
    corners = [pt(body, CX - top / 2 + p["look"], y0), pt(body, CX + top / 2 + p["look"], y0),
               pt(body, CX + bottom / 2 + p["look"], y1), pt(body, CX - bottom / 2 + p["look"], y1)]
    ss = 4
    k = HI * ss
    layer = Image.new("RGBA", (W * k, H * k))
    d = ImageDraw.Draw(layer)
    pts = [(x * k, y * k) for x, y in corners]
    d.polygon(pts, fill=(*g.PALETTE["fur"], 255))
    d.line(pts + [pts[0]], fill=(*g.PALETTE["ink"], 255), width=k, joint="curve")
    for x, y in pts:                                           # 轉角補成圓的，才不會缺角
        d.ellipse([x - k / 2, y - k / 2, x + k / 2, y + k / 2], fill=(*g.PALETTE["ink"], 255))
    img.alpha_composite(layer.resize((W * HI, H * HI), Image.LANCZOS))
    return img


# ---------------------------------------------------------------- 動畫（每組 8 格）
def anim_idle(t):
    """待機：輕輕呼吸、耳朵微微晃、眨一次眼。"""
    i = int(round(t * FRAMES)) % FRAMES
    sq = [1.0, 1.0, 0.985, 0.985, 1.0, 1.0, 1.0, 1.0][i]
    ear = [0, 1.5, 2.5, 1.5, 0, -1.5, -2.5, -1.5][i]
    return dict(squash=sq, earL=ear, earR=ear * 0.7, eyes="closed" if i == 5 else "open")


def anim_ears(t):
    """抖耳朵：兩隻耳朵輪流往外彎。"""
    i = int(round(t * FRAMES)) % FRAMES
    left = [0, -22, -30, -12, 0, 0, 0, 0][i]
    right = [0, 0, 0, 0, 0, 22, 30, 12][i]
    return dict(earL=left, earR=right, eyes="open", look=[0, -1, -1, 0, 0, 1, 1, 0][i])


def anim_hop(t):
    """跳一下：蹲、跳起、落地。"""
    i = int(round(t * FRAMES)) % FRAMES
    # 每格：高度、壓扁比例、耳朵往外張開的角度（蹲下和落地時張開，騰空時併攏）
    table = [(0, 1.0, 0), (0, 0.9, 10), (-6, 1.05, 3), (-11, 1.0, 0), (-11, 1.0, 4), (-5, 1.03, 9), (0, 0.9, 18), (0, 0.97, 6)]
    dy, sq, spread = table[i]
    return dict(dy=dy, squash=sq, earL=-spread, earR=spread, eyes="happy" if 2 <= i <= 5 else "open")


def anim_sway(t):
    """開心搖擺：身體左右搖，耳朵跟著甩，眼睛彎成弧形。"""
    i = int(round(t * FRAMES)) % FRAMES
    s = math.sin(2 * math.pi * t)
    lag = math.sin(2 * math.pi * t - 0.9)
    return dict(lean=7 * s, earL=-10 * lag, earR=-10 * lag, eyes="happy", blush=True,
                legL=2 if i in (1, 2) else 0, legR=2 if i in (5, 6) else 0)


ANIMS = [
    ("idle", "01 待機", anim_idle, 165),
    ("ears", "02 抖耳朵", anim_ears, 120),
    ("hop", "03 跳一下", anim_hop, 100),
    ("sway", "04 開心搖擺", anim_sway, 120),
]


def on_bg(img, scale=1):
    """成品圖（已放大 HI 倍）貼到預覽底色上；scale 是再放大的整數倍。"""
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    out = Image.new("RGB", img.size, g.BG)
    out.paste(img, (0, 0), img)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    render().save(os.path.join(OUT, "sprite.png"))
    # 造型大圖：平常與開心的表情，再加一張臉部特寫
    crop = tuple(v * HI for v in (24, 8, 72, 106))
    normal = on_bg(render().crop(crop), 2)
    happy = on_bg(render(dict(eyes="happy", blush=True)).crop(crop), 2)
    face = on_bg(render().crop(tuple(v * HI for v in (30, 34, 66, 74))), 4)
    design = Image.new("RGB", (normal.width * 2 + face.width, normal.height), g.BG)
    design.paste(normal, (0, 0))
    design.paste(happy, (normal.width, 0))
    design.paste(face, (normal.width * 2, (normal.height - face.height) // 2))
    design.save(os.path.join(OUT, "design.png"))
    # 動畫總覽
    lw = 150
    fw, fh = W * HI // 2, H * HI // 2
    sheet = Image.new("RGB", (lw + fw * FRAMES, (fh + 6) * len(ANIMS)), (20, 23, 32))
    dr = ImageDraw.Draw(sheet)
    for j, (name, label, fn, ms) in enumerate(ANIMS):
        frames = [render(fn(i / FRAMES)) for i in range(FRAMES)]
        strip = Image.new("RGBA", (W * HI * FRAMES, H * HI))
        for i, im in enumerate(frames):
            strip.paste(im, (i * W * HI, 0))
            sheet.paste(on_bg(im).resize((fw, fh), Image.LANCZOS), (lw + i * fw, j * (fh + 6)))
        strip.save(os.path.join(OUT, f"{name}.png"))
        gif = [on_bg(im) for im in frames]
        gif[0].save(os.path.join(OUT, f"{name}-preview.gif"), save_all=True, append_images=gif[1:], duration=ms, loop=0)
        dr.text((10, j * (fh + 6) + fh // 2 - 12), label, font=g.font(22), fill=(240, 240, 245))
    sheet.save(os.path.join(OUT, "all-frames.png"))
    print("saved →", OUT)


if __name__ == "__main__":
    main()
