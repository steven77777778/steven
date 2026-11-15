#!/usr/bin/env python3
"""火星人原生像素圖產生器。

每一張圖都是用數學算出來的：身體各部位是橢圓、圓角方塊和膠囊線段，
姿勢用關節角度與仿射矩陣（旋轉、縮放、位移）描述，最後在「一格 = 一個像素」
的畫布上逐像素判斷是否落在形狀內。沒有任何放大或縮圖的步驟，所以輸出的
PNG 就是原生像素圖；做動畫時只要改姿勢參數就會得到新的一格。

用法：python3 pixel/generate.py   →  輸出到 pixel/out/
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
FRAMES = 8                      # 每個動畫的格數
PREVIEW_SCALE = 8               # 預覽圖放大倍率（只用於預覽，原生圖不放大）
BG = (138, 170, 170)            # 預覽圖底色


# ---------------------------------------------------------------- 仿射矩陣
def T(tx, ty):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1.0]])


def R(deg, cx, cy):
    """繞 (cx, cy) 旋轉；螢幕座標 y 向下，正角度 = 上半身往畫面右邊倒。"""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return T(cx, cy) @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]]) @ T(-cx, -cy)


def S(sx, sy, cx, cy):
    return T(cx, cy) @ np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1.0]]) @ T(-cx, -cy)


def pt(M, x, y):
    v = M @ np.array([x, y, 1.0])
    return float(v[0]), float(v[1])


# ---------------------------------------------------------------- 畫布
class Canvas:
    """col = 每個像素的顏色名稱編號（0 = 透明），part = 屬於哪個部位。"""

    def __init__(self, w, h, names):
        self.w, self.h = w, h
        self.idx = {n: i + 1 for i, n in enumerate(names)}
        self.names = [None] + list(names)
        self.col = np.zeros((h, w), int)
        self.part = np.zeros((h, w), int)
        ys, xs = np.mgrid[0:h, 0:w]
        self.px, self.py = xs + 0.5, ys + 0.5      # 像素中心

    # --- 形狀：回傳布林遮罩 ---
    def _local(self, M):
        Mi = np.linalg.inv(M)
        return (Mi[0, 0] * self.px + Mi[0, 1] * self.py + Mi[0, 2],
                Mi[1, 0] * self.px + Mi[1, 1] * self.py + Mi[1, 2])

    def ellipse(self, M, cx, cy, rx, ry):
        x, y = self._local(M)
        return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0

    def box(self, M, cx, cy, hw, hh, r=0.0):
        x, y = self._local(M)
        qx, qy = np.abs(x - cx) - (hw - r), np.abs(y - cy) - (hh - r)
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
        return d <= 0

    def capsule(self, p0, p1, r):
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = np.zeros_like(self.px) if L2 == 0 else np.clip(((self.px - x0) * dx + (self.py - y0) * dy) / L2, 0, 1)
        return np.hypot(self.px - (x0 + t * dx), self.py - (y0 + t * dy)) <= r

    # --- 上色 ---
    def paint(self, mask, color, part, sep=None):
        """sep：這個部位蓋在別的部位上時，沿邊緣畫一圈分隔線的顏色。"""
        if sep is not None:
            ring = dilate(mask) & ~mask & (self.col > 0)
            self.col[ring] = self.idx[sep]
        self.col[mask] = self.idx[color]
        self.part[mask] = part

    def stamp(self, rows, cx, cy, legend, part):
        """把固定的小圖案（例如眼睛）貼在最接近 (cx, cy) 的整數像素上。"""
        h, w = len(rows), len(rows[0])
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in legend and 0 <= y0 + j < self.h and 0 <= x0 + i < self.w:
                    self.col[y0 + j, x0 + i] = self.idx[legend[ch]]
                    self.part[y0 + j, x0 + i] = part


def dilate(m):
    out = m.copy()
    out[1:, :] |= m[:-1, :]
    out[:-1, :] |= m[1:, :]
    out[:, 1:] |= m[:, :-1]
    out[:, :-1] |= m[:, 1:]
    return out


# ---------------------------------------------------------------- 三組造型
RED, RED_HI, RED_SH = (216, 67, 74), (236, 110, 112), (176, 48, 60)
CREAM, CREAM_SH = (244, 232, 214), (214, 196, 170)
SKIN, SKIN_SH = (246, 201, 176), (222, 164, 140)
JEANS, JEANS_SH = (44, 108, 140), (30, 80, 110)
SHOE, WHITE, INK, LINE = (44, 44, 52), (255, 255, 255), (30, 28, 40), (25, 26, 38)

PALETTE = {
    "line": LINE, "head": RED, "head_hi": RED_HI, "head_sh": RED_SH,
    "white": WHITE, "ink": INK, "sweater": CREAM, "sweater_sh": CREAM_SH,
    "skin": SKIN, "skin_sh": SKIN_SH, "jeans": JEANS, "jeans_sh": JEANS_SH, "shoe": SHOE,
    # 帶色外框（方案 B 用）
    "ol_head": (120, 28, 44), "ol_sweater": (150, 128, 104), "ol_skin": (160, 104, 88),
    "ol_jeans": (18, 48, 72), "ol_shoe": (16, 16, 22),
}
SHADE = {"head": "head_sh", "sweater": "sweater_sh", "skin": "skin_sh", "jeans": "jeans_sh"}
TINT = {"head": "ol_head", "head_hi": "ol_head", "head_sh": "ol_head", "sweater": "ol_sweater",
        "sweater_sh": "ol_sweater", "skin": "ol_skin", "skin_sh": "ol_skin", "jeans": "ol_jeans",
        "jeans_sh": "ol_jeans", "shoe": "ol_shoe", "white": "ol_head", "ink": "ol_head"}

EYES_S = {"open": [".ww.", "wkkw", ".ww."], "closed": ["....", "kkkk", "...."],
          "happy": [".kk.", "k..k", "...."], "wide": [".ww.", "wkkw", "wkkw", ".ww."]}
EYES_L = {"open": [".wwww.", "wwwwww", "wwkkww", ".wwww."], "closed": ["......", "......", "kkkkkk", "......"],
          "happy": ["..kk..", ".k..k.", "k....k", "......"],
          "wide": [".wwww.", "wwwwww", "wwkkww", "wwkkww", ".wwww."]}


def humanoid(scale, **extra):
    """方案 A、B 共用的身體比例（單位：像素），scale 是整體倍率。"""
    k = scale
    d = dict(
        W=round(44 * k), H=round(54 * k), cx=22 * k, ground=51.5 * k, u=k,
        head=(17 * k, 7.2 * k, 6.8 * k),            # 頭：中心 y、半寬、半高
        face=(20.5 * k, 6.0 * k, 4.6 * k),          # 下半臉（較窄的橢圓）
        hi=(-3.0 * k, 12.6 * k, 2.3 * k, 1.3 * k),  # 頭頂亮面
        neck=24 * k, eye=(3.2 * k, 17.3 * k), tent_y=22.3 * k, tent_r=1.05 * k,
        torso=(30.2 * k, 5.0 * k, 6.7 * k, 1.6 * k),  # 毛衣：中心 y、半寬、半高、圓角
        hem=36.4 * k,
        shoulder=(6.0 * k, 25.6 * k), arm=(5.6 * k, 5.4 * k, 1.05 * k), hand=1.25 * k,
        hips=(38.3 * k, 5.0 * k, 2.3 * k), hip=(2.5 * k, 38.5 * k), leg_r=2.5 * k,
        ankle=48.4 * k, shoe=(2.5 * k, 1.5 * k),
        # 觸手：(根部 x、往外的角度、長度、末端再彎的角度)
        tentacles=[(-5.6, 62, 5.2, 14), (-3.4, 10, 6.6, -6), (0, 0, 8.4, 0), (3.4, -10, 6.6, 6), (5.6, -62, 5.2, -14)],
        eyes=EYES_S, outline="line", sep="line", shade=False,
    )
    d["tentacles"] = [(x * k, a, L * k, c) for x, a, L, c in d["tentacles"]]
    d.update(extra)
    return d


DESIGNS = {
    "A": humanoid(1.0, title="A 簡潔版", note="44×54 像素 · 純色 · 深色外框"),
    "B": humanoid(1.5, title="B 細緻版", note="66×81 像素 · 有明暗 · 帶色外框 · 7 條觸手",
                  eyes=EYES_L, outline="tint", sep="shade", shade=True,
                  tentacles=[(x * 1.5, a, L * 1.5, c) for x, a, L, c in
                             [(-5.8, 64, 5.4, 16), (-4.2, 24, 6.2, -8), (-2.2, 6, 7.4, -3), (0, 0, 8.8, 0),
                              (2.2, -6, 7.4, 3), (4.2, -24, 6.2, 8), (5.8, -64, 5.4, -16)]],
                  tent_r=1.7),
    "C": dict(  # Q 版：頭大身體小
        title="C Q版", note="44×44 像素 · 大頭小身體",
        W=44, H=44, cx=22, ground=41.5, u=0.8,
        head=(17.5, 10.6, 9.4), face=(22.0, 9.0, 6.4), hi=(-4.6, 11.4, 3.2, 1.7),
        neck=27.5, eye=(4.6, 18.4), tent_y=25.4, tent_r=1.1,
        torso=(31.4, 4.5, 4.0, 1.5), hem=34.6,
        shoulder=(5.5, 28.6), arm=(3.3, 3.1, 1.05), hand=1.3,
        hips=(36.0, 4.5, 1.4), hip=(2.25, 36.2), leg_r=2.25, ankle=39.0, shoe=(2.25, 1.25),
        tentacles=[(-8.4, 66, 4.4, 16), (-5.4, 18, 4.6, -8), (-2.4, 4, 5.4, -3), (2.4, -4, 5.4, 3),
                   (5.4, -18, 4.6, 8), (8.4, -66, 4.4, -16)],
        eyes=EYES_L, outline="line", sep="line", shade=False,
    ),
}


# ---------------------------------------------------------------- 方案 A 的十組微調
T5 = [(-5.6, 62, 5.2, 14), (-3.4, 10, 6.6, -6), (0, 0, 8.4, 0), (3.4, -10, 6.6, 6), (5.6, -62, 5.2, -14)]
T7 = [(-5.8, 64, 5.0, 16), (-4.2, 24, 5.4, -8), (-2.2, 6, 6.4, -3), (0, 0, 7.4, 0),
      (2.2, -6, 6.4, 3), (4.2, -24, 5.4, 8), (5.8, -64, 5.0, -16)]


def tent(base, sx=1.0, sl=1.0):
    return [(x * sx, a, L * sl, c) for x, a, L, c in base]


BIG_HEAD = dict(head=(16.4, 8.6, 8.0), face=(21.0, 7.2, 5.0), hi=(-3.8, 11.0, 2.8, 1.5),
                eye=(3.9, 17.2), tent_y=23.0, tentacles=tent(T5, 1.22, 1.0))
VARIANTS = {
    "A1": humanoid(1.0, note="原版"),
    "A2": humanoid(1.0, note="頭放大", **BIG_HEAD),
    "A3": humanoid(1.0, note="觸手加粗、末端不加深", tent_r=1.55, tips=False, tentacles=tent(T5, 1.0, 0.95)),
    "A4": humanoid(1.0, note="7 條細觸手、較短", tentacles=T7, tent_r=0.8),
    "A5": humanoid(1.0, note="身體內部不用黑線，改用陰影色分隔", sep="shade"),
    "A6": humanoid(1.0, note="外框改成各部位的深色", outline="tint", sep="shade"),
    "A7": humanoid(1.0, note="身形修長：窄肩、長腿", torso=(29.6, 4.5, 6.0, 1.6), hem=35.2, shoulder=(5.5, 25.6),
                   hips=(37.0, 4.5, 2.2), hip=(2.25, 37.2), leg_r=2.25, shoe=(2.25, 1.5)),
    "A8": humanoid(1.0, note="寬鬆毛衣：身體較寬、手臂微張", torso=(30.6, 5.8, 7.1, 2.2), hem=37.2,
                   shoulder=(6.8, 25.8), rest_arm=9, arm=(5.8, 5.6, 1.3), hand=1.4),
    "A9": humanoid(1.0, note="大眼睛、位置略低", eyes=EYES_L, eye=(3.6, 18.2)),
    "A10": humanoid(1.0, note="綜合：大頭 + 粗觸手 + 柔和線條 + 明暗", tent_r=1.5, tips=False, sep="shade",
                    outline="tint", shade=True, **dict(BIG_HEAD, tentacles=tent(T5, 1.22, 0.95))),
}


# ---------------------------------------------------------------- 姿勢 → 像素
REST = dict(dy=0, lean=0, tilt=0, bob=0, squash=1.0, sway=0.0, sway_amp=5.0, flare=0.0, eyes="open",
            armL=(4, 0, False), armR=(4, 0, False), legL=(0, 0), legR=(0, 0))


def render(d, pose):
    """依姿勢參數畫出一格。回傳 Canvas。"""
    ra = d.get("rest_arm", 4)
    p = dict(REST, armL=(ra, 0, False), armR=(ra, 0, False))
    p.update(pose)
    c = Canvas(d["W"], d["H"], list(PALETTE))
    cx, ground, u = d["cx"], d["ground"], d["u"]
    dy = round(p["dy"] * u)                      # 位移一律取整數像素，形狀才不會抖動
    body = T(0, dy) @ R(p["lean"], cx, ground) @ S(1, p["squash"], cx, ground)
    head = body @ R(p["tilt"], cx, d["neck"]) @ T(0, round(p["bob"]))
    sep = d["sep"]
    sep_of = lambda color: "line" if sep == "line" else SHADE.get(color, color)

    # 1. 腿與鞋：腳踩在地上，髖部跟著身體走
    hx, hy = d["hip"]
    for part, side, (ldx, lift) in ((1, -1, p["legL"]), (2, 1, p["legR"])):
        hipp = pt(body, cx + side * hx, hy)
        fx, fy = cx + side * hx + round(ldx * u), d["ankle"] - round(lift * u) + dy
        c.paint(c.capsule(hipp, (fx, fy), d["leg_r"]), "jeans", part, sep_of("jeans") if part == 2 else None)
        sw, sh = d["shoe"]
        c.paint(c.box(T(0, 0), fx, fy + sh, sw, sh, 0.6 * u), "shoe", 10 + part)
    # 2. 臀部
    hcy, hhw, hhh = d["hips"]
    c.paint(c.box(body, cx, hcy, hhw, hhh, 0.8 * u), "jeans", 3)
    # 3. 毛衣
    tcy, thw, thh, tr = d["torso"]
    torso = c.box(body, cx, tcy, thw, thh, tr)
    c.paint(torso, "sweater", 4)
    c.paint(torso & c.box(body, cx, d["hem"], thw, 0.5 * u), "sweater_sh", 4)   # 下襬

    # 手臂：a1 = 上臂角度（0 垂下、90 平舉、180 高舉），a2 = 手肘再彎的角度
    def arm(part, side, spec):
        a1, a2, _ = spec
        sx, sy = d["shoulder"]
        L1, L2, r = d["arm"]
        s0 = (cx + side * sx, sy)
        e = (s0[0] + side * L1 * math.sin(math.radians(a1)), s0[1] + L1 * math.cos(math.radians(a1)))
        a = math.radians(a1 + a2)
        w = (e[0] + side * L2 * math.sin(a), e[1] + L2 * math.cos(a))
        hnd = (e[0] + side * (L2 + 0.9 * u) * math.sin(a), e[1] + (L2 + 0.9 * u) * math.cos(a))
        s0, e, w, hnd = (pt(body, *q) for q in (s0, e, w, hnd))
        c.paint(c.capsule(hnd, hnd, d["hand"]), "skin", part + 20, sep_of("skin"))
        c.paint(c.capsule(s0, e, r) | c.capsule(e, w, r), "sweater", part, sep_of("sweater"))

    for part, side, spec in ((5, -1, p["armL"]), (6, 1, p["armR"])):
        if not spec[2]:
            arm(part, side, spec)                 # 垂著的手在觸手後面
    # 4. 觸手：兩節線段，角度隨 sway 擺動
    n = len(d["tentacles"])
    for i, (bx, ang, L, curl) in enumerate(d["tentacles"]):
        side = -1 if bx < 0 else 1
        wob = p["sway_amp"] * math.sin(p["sway"] + i * 0.9)
        a = math.radians(-ang + wob + p["flare"] * side * 55 * (1 if abs(ang) > 30 else 0.45))
        b = a + math.radians(-curl + 1.6 * p["sway_amp"] * math.sin(p["sway"] + i * 0.9 - 0.8))
        p0 = (cx + bx, d["tent_y"])
        p1 = (p0[0] + 0.55 * L * math.sin(a), p0[1] + 0.55 * L * math.cos(a))
        p2 = (p1[0] + 0.45 * L * math.sin(b), p1[1] + 0.45 * L * math.cos(b))
        p0, p1, p2 = (pt(head, *q) for q in (p0, p1, p2))
        c.paint(c.capsule(p0, p1, d["tent_r"]) | c.capsule(p1, p2, d["tent_r"]), "head", 30 + i)
        if d.get("tips", True):
            c.paint(c.capsule(p2, p2, d["tent_r"]), "head_sh", 30 + i)         # 末端較深
    # 5. 頭
    hcy2, hrx, hry = d["head"]
    fcy, frx, fry = d["face"]
    c.paint(c.ellipse(head, cx, hcy2, hrx, hry) | c.ellipse(head, cx, fcy, frx, fry), "head", 50)
    hix, hiy, hirx, hiry = d["hi"]
    c.paint(c.ellipse(head, cx + hix, hiy, hirx, hiry), "head_hi", 50)
    # 6. 眼睛：位置跟著頭轉，圖案本身不旋轉以保持清楚
    ex, ey = d["eye"]
    for side in (-1, 1):
        c.stamp(d["eyes"][p["eyes"]], *pt(head, cx + side * ex, ey), {"w": "white", "k": "ink"}, 50)
    # 7. 舉起來的手在最前面
    for part, side, spec in ((5, -1, p["armL"]), (6, 1, p["armR"])):
        if spec[2]:
            arm(part, side, spec)

    # 8. 明暗：光從左上來，每個部位的右緣與下緣用暗色
    if d["shade"]:
        col, part = c.col, c.part
        edge = np.zeros_like(col, bool)
        edge[:, :-1] |= part[:, :-1] != part[:, 1:]
        edge[:-1, :] |= part[:-1, :] != part[1:, :]
        edge[:, -1] = edge[-1, :] = True
        for base, dark in SHADE.items():
            col[edge & (col == c.idx[base])] = c.idx[dark]
    # 9. 外框：輪廓外側一圈
    filled = c.col > 0
    ring = dilate(filled) & ~filled
    if d["outline"] == "line":
        c.col[ring] = c.idx["line"]
    else:                                         # 帶色外框：取相鄰像素顏色的深色版
        src = c.col.copy()
        for dy_, dx_ in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = np.roll(src, (dy_, dx_), (0, 1))
            take = ring & (c.col == 0) & (nb > 0)
            for name, dark in TINT.items():
                c.col[take & (nb == c.idx[name])] = c.idx[dark]
        c.col[ring & (c.col == 0)] = c.idx["line"]
    return c


def to_image(c):
    rgba = np.zeros((c.h, c.w, 4), np.uint8)
    for name, i in c.idx.items():
        rgba[c.col == i] = (*PALETTE[name], 255)
    return Image.fromarray(rgba, "RGBA")


# ---------------------------------------------------------------- 五組動畫
def lerp(a, b, w):
    return a + (b - a) * w


def anim_idle(t):
    """1 待機：呼吸、觸手輕擺、眨眼"""
    return dict(bob=-1 if 0.5 <= t < 1 else 0, sway=2 * math.pi * t, sway_amp=6,
                eyes="closed" if abs(t - 0.75) < 0.01 else "open")


def anim_wave(t):
    """2 招手：右手高舉左右揮，頭微微歪"""
    return dict(armR=(152, -18 + 30 * math.sin(4 * math.pi * t), True), tilt=4, eyes="happy",
                bob=-1 if 0.5 <= t < 1 else 0, sway=4 * math.pi * t, sway_amp=7)


def anim_dance(t):
    """3 火星人舞：身體左右傾，一手高舉一手彎在胸前，頭跟著歪"""
    s = math.sin(2 * math.pi * t)
    w = (s + 1) / 2                                # 0 = 向左傾到底，1 = 向右傾到底
    return dict(lean=8 * s, tilt=7 * s, dy=1 if abs(s) < 0.35 else 0,
                armR=(lerp(148, 22, w), lerp(12, -128, w), True),
                armL=(lerp(22, 148, w), lerp(-128, 12, w), True),
                sway=2 * math.pi * t + 1.2, sway_amp=11, eyes="open")


def anim_walk(t):
    """4 走路：原地踏步，手腳交替擺動"""
    s, co = math.sin(2 * math.pi * t), math.cos(2 * math.pi * t)
    return dict(legL=(2.2 * s, 2.2 * max(0, co)), legR=(-2.2 * s, 2.2 * max(0, -co)),
                armL=(-24 * s, 12, False), armR=(24 * s, 12, False),
                dy=-1 if abs(s) < 0.5 else 0, sway=2 * math.pi * t, sway_amp=10, lean=1.5 * s)


def anim_jump(t):
    """5 跳躍：蹲下、跳起、觸手飛起來、落地"""
    keys = [  # dy, squash, 手臂角度, 觸手飛起程度, 眼睛
        (0, 1.00, 4, 0.0, "open"), (0, 0.88, -14, 0.0, "closed"), (-3, 1.06, 120, 0.3, "open"),
        (-5, 1.00, 160, 0.8, "wide"), (-6, 1.00, 164, 1.0, "wide"), (-3, 1.03, 140, 1.0, "wide"),
        (0, 0.86, 62, 0.4, "closed"), (0, 0.96, 20, 0.1, "open"),
    ]
    dy, sq, a, fl, eyes = keys[int(round(t * FRAMES)) % FRAMES]
    front = a > 90
    return dict(dy=dy, squash=sq, armL=(a, 0, front), armR=(a, 0, front), flare=fl, eyes=eyes, sway_amp=3)


ANIMS = [("idle", "1 待機", anim_idle, 140), ("wave", "2 招手", anim_wave, 110),
         ("dance", "3 火星人舞", anim_dance, 130), ("walk", "4 走路", anim_walk, 100),
         ("jump", "5 跳躍", anim_jump, 100)]


# ---------------------------------------------------------------- 輸出
def font(size):
    for path in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def on_bg(img, scale):
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    out = Image.new("RGB", big.size, BG)
    out.paste(big, (0, 0), big)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {"frames": FRAMES, "designs": {}}
    frames = {}                                   # frames[設計][動畫] = [Image…]
    for key, d in DESIGNS.items():
        ddir = os.path.join(OUT, key)
        os.makedirs(ddir, exist_ok=True)
        to_image(render(d, {})).save(os.path.join(ddir, "sprite.png"))
        frames[key] = {}
        for name, _, fn, ms in ANIMS:
            fr = [to_image(render(d, fn(i / FRAMES))) for i in range(FRAMES)]
            frames[key][name] = fr
            sheet = Image.new("RGBA", (d["W"] * FRAMES, d["H"]))
            for i, im in enumerate(fr):
                sheet.paste(im, (i * d["W"], 0))
            sheet.save(os.path.join(ddir, f"{name}.png"))          # 原生像素的動畫條
        meta["designs"][key] = {"frame_width": d["W"], "frame_height": d["H"], "note": d["note"],
                                "animations": {n: {"file": f"{key}/{n}.png", "frame_ms": ms} for n, _, _, ms in ANIMS}}
    json.dump(meta, open(os.path.join(OUT, "sprites.json"), "w"), ensure_ascii=False, indent=2)

    # 三組造型對照圖（同一個放大倍率，可以直接比較實際像素數）
    f1, f2 = font(30), font(18)
    cell_w = max(d["W"] for d in DESIGNS.values()) * PREVIEW_SCALE + 40
    cell_h = max(d["H"] for d in DESIGNS.values()) * PREVIEW_SCALE
    sheet = Image.new("RGB", (cell_w * 3, cell_h + 96), BG)
    dr = ImageDraw.Draw(sheet)
    for i, (key, d) in enumerate(DESIGNS.items()):
        im = on_bg(to_image(render(d, {})), PREVIEW_SCALE)
        sheet.paste(im, (i * cell_w + (cell_w - im.width) // 2, 86 + cell_h - im.height))
        dr.text((i * cell_w + 20, 14), d["title"], font=f1, fill=(20, 30, 40))
        dr.text((i * cell_w + 20, 54), d["note"], font=f2, fill=(40, 60, 70))
    sheet.save(os.path.join(OUT, "designs.png"))

    # 每組造型一張動畫預覽：五個動畫並排
    for key, d in DESIGNS.items():
        sc = PREVIEW_SCALE if key != "B" else 5
        w, h = d["W"] * sc, d["H"] * sc
        gif = []
        for i in range(FRAMES):
            fr = Image.new("RGB", (w * len(ANIMS), h + 44), BG)
            dr = ImageDraw.Draw(fr)
            for j, (name, label, _, _) in enumerate(ANIMS):
                fr.paste(on_bg(frames[key][name][i], sc), (j * w, 44))
                dr.text((j * w + 10, 8), label, font=font(24), fill=(20, 30, 40))
            gif.append(fr)
        gif[0].save(os.path.join(OUT, f"animations-{key}.gif"), save_all=True, append_images=gif[1:],
                    duration=120, loop=0, disposal=1)
        # 靜態版：每個動畫的 8 格排成一列，方便逐格檢查
        strip = Image.new("RGB", (w * FRAMES + 150, (h + 6) * len(ANIMS)), BG)
        dr = ImageDraw.Draw(strip)
        for j, (name, label, _, _) in enumerate(ANIMS):
            dr.text((8, j * (h + 6) + h // 2 - 12), label, font=font(22), fill=(20, 30, 40))
            for i in range(FRAMES):
                strip.paste(on_bg(frames[key][name][i], sc), (150 + i * w, j * (h + 6)))
        strip.save(os.path.join(OUT, f"frames-{key}.png"))
    variants_sheet()
    print("done →", OUT)


def variants_sheet():
    """方案 A 的十組微調：靜態對照圖、招手動畫對照，以及每組的原生像素圖。"""
    vdir = os.path.join(OUT, "variants")
    os.makedirs(vdir, exist_ok=True)
    sc, cols = 7, 5
    f1, f2 = font(26), font(15)
    first = next(iter(VARIANTS.values()))
    w, h = first["W"] * sc, first["H"] * sc
    cw, ch = w + 24, h + 70

    def sheet(pose):
        out = Image.new("RGB", (cw * cols, ch * 2), BG)
        dr = ImageDraw.Draw(out)
        for i, (key, d) in enumerate(VARIANTS.items()):
            x, y = (i % cols) * cw, (i // cols) * ch
            out.paste(on_bg(to_image(render(d, pose)), sc), (x + 12, y + 64))
            dr.text((x + 12, y + 8), key, font=f1, fill=(20, 30, 40))
            dr.text((x + 12, y + 40), d["note"], font=f2, fill=(40, 60, 70))
        return out

    for key, d in VARIANTS.items():
        to_image(render(d, {})).save(os.path.join(vdir, f"{key}.png"))
    sheet({}).save(os.path.join(OUT, "variants-A.png"))
    frames = [sheet(anim_wave(i / FRAMES)) for i in range(FRAMES)]
    frames += [sheet(anim_dance(i / FRAMES)) for i in range(FRAMES)]
    frames[0].save(os.path.join(OUT, "variants-A-motion.gif"), save_all=True, append_images=frames[1:],
                   duration=130, loop=0, disposal=1)


if __name__ == "__main__":
    main()
