#!/usr/bin/env python3
"""ヨルシカ「火星人」MV 高精細純色像素產生器（96×108 高解析度 · 方案 1 乾淨純色像素 · 男版 1:1 直筒比例）。

針對原圖逐張對照修正重點：
1. 畫布升級為 96×108（約 3.5 倍像素密度），維持乾淨純色塊與 1px 銳利外框，手指、五官、道具細節清晰可辨。
2. 嚴格維持 1:1 男版直筒比例（上衣寬 20px == 直筒褲寬 20px），杜絕梯形裙裝感。
3. 特效（彩墨水花、金色星芒、桌球動線、咖啡蒸氣、夜空花火）採獨立無黑框圖層，不再變成生硬黑框色塊。
4. 重點動作徹底重製：
   - 03 吹紅泡泡 (#08-#11)：改為忠於原圖的「朝右側身構圖」，單眼死魚眼、襯衫翻領、手肘自然下垂捧嘴，水平吹出細長紅管與亮面大紅氣球！
   - 04 揮灑彩墨 (#15-#24)：修正手肘扭曲，重現 #16 右上甩薄荷綠水花 → #20 過頭拉出天藍流體水弧 → #24 左手平伸食指噴出兩滴粉紅水珠！
   - 10 打乒乓球 (#51-#52)：深藍撞色袖 T 恤，右手肘自然下垂、前臂斜伸胸前握持清晰圓面桌球拍，橘黃乒乓球上下彈跳並帶白色殘影，雙眼隨球上下移動！
   - 11 土耳其帽喝咖啡 (#54 MARSLI)：統一為完整 8 格高細節 #54 造型（暗紅土耳其毯帽＋黑流蘇、圓框墨鏡、卡其夾克內搭白T、深色長褲），手肘自然下收雙手捧白瓷馬克杯啜飲熱咖啡並飄起柔和白蒸氣！
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
FRAMES = 8
PREVIEW_SCALE = 3
BG = (96, 122, 128)

PALETTE = {
    "line":       (25, 26, 38),     # 乾淨 1px 深色外框
    "head":       (214, 65, 72),    # MV 章魚紅（乾淨統一純色）
    "head_hi":    (250, 224, 226),  # 頭頂亮白粉高光
    "head_sh":    (172, 46, 58),    # 觸手尖端與半垂眼皮暗紅
    "fez":        (142, 28, 42),    # #54 暗紅土耳其毯帽
    "fez_sh":     (104, 18, 30),
    "white":      (255, 255, 255),
    "steam":      (236, 242, 248),  # 柔和蒸氣與動線白
    "ink":        (30, 28, 40),
    # 服裝純色
    "sweater":    (242, 232, 216),  # 米白長袖襯衫 / 毛衣
    "sweater_sh": (212, 196, 174),
    "teal_t":     (42, 128, 126),   # #15-#26 湖水綠寬 T
    "teal_sh":    (28, 96, 96),
    "yellow_t":   (224, 188, 84),   # #42-#46 / #65-#78 芥末黃寬 T
    "yellow_sh":  (188, 150, 58),
    "navy_t":     (28, 76, 114),    # #51-#52 打桌球寶藍身片
    "navy_slv":   (16, 42, 68),     # #51-#52 打桌球深藏青撞色短袖
    "suit":       (36, 40, 54),     # #36-#37 黑色西裝 / #54 深色長褲
    "suit_sh":    (22, 24, 34),
    "tan_j":      (192, 148, 96),   # #54 卡其棕夾克
    "tan_sh":     (156, 116, 68),
    "skin":       (246, 204, 180),
    "skin_sh":    (216, 162, 136),
    "jeans":      (42, 98, 128),    # 1:1 男版直筒褲
    "jeans_sh":   (28, 72, 98),
    "shoe":       (68, 52, 42),
    "olive_shoe": (96, 88, 44),     # #54 橄欖綠休閒鞋
    "shoe_sole":  (240, 234, 224),
    # 道具與無黑框特效色
    "wood":       (178, 128, 80),
    "wood_sh":    (128, 86, 48),
    "paddle_red": (168, 38, 48),    # 桌球拍膠皮暗紅
    "red_ink":    (208, 46, 56),
    "blower_pk":  (238, 108, 128),  # #10 吹管粉紅亮面
    "bubble_hi":  (254, 198, 202),  # #10 紅氣球高光
    "paint_g":    (122, 218, 134),  # #16 薄荷綠水花
    "paint_g2":   (174, 240, 182),
    "paint_b":    (78, 178, 244),   # #20 天藍流體彩墨
    "paint_b2":   (156, 218, 255),
    "paint_p":    (240, 118, 158),  # #24 指尖粉紅水珠
    "paint_p2":   (255, 182, 206),
    "star":       (255, 222, 74),
    "star_hi":    (255, 250, 214),
    "ball":       (248, 188, 42),   # #51-#52 橘黃乒乓球
    "flare_p":    (216, 108, 190),
}

# 96×108 專用高精細眼神點陣（7×5）
EYES = {
    "chill": [
        ".ddddd.",
        "dwwkkwd",
        "dwwkkwd",
        ".wwwww.",
        ".......",
    ],
    "lookL": [
        ".ddddd.",
        "dkkwwwd",
        "dkkwwwd",
        ".wwwww.",
        ".......",
    ],
    "lookR": [
        ".ddddd.",
        "dwwwkkd",
        "dwwwkkd",
        ".wwwww.",
        ".......",
    ],
    "lookD": [
        ".ddddd.",
        ".wwwww.",
        "dwwkkwd",
        ".wkkkw.",
        ".......",
    ],
    "half": [
        ".ddddd.",
        "ddddddd",
        "dwwkkwd",
        ".......",
        ".......",
    ],
    "closed": [
        ".......",
        ".ddddd.",
        "kkkkkkk",
        ".......",
        ".......",
    ],
    "squint": [
        ".ddddd.",
        "ddddddd",
        "dwwkkwd",
        ".ddddd.",
        ".......",
    ],
    "wide": [
        ".wwwww.",
        "wwwwwww",
        "wwkkkww",
        "wwkkkww",
        ".wwwww.",
    ],
    "joy": [                      # 開心時瞇成像括號的弧形 ︵ ︵
        ".......",
        ".kkkkk.",
        "k.....k",
        ".......",
        ".......",
    ],
    "glasses": [
        ".kkkkk.",
        "kkkkkkk",
        "kkkkkkk",
        "kkkkkkk",
        ".kkkkk.",
    ],
}

# 側臉專用單眼點陣（6×5，朝右看 #09-#10）
EYE_PROFILE_R = {
    "chill": [
        "ddddd.",
        "dwwkkw",
        "dwwkkw",
        ".wwww.",
        "......",
    ],
    "wide": [
        ".wwww.",
        "wwkkkw",
        "wwkkkw",
        ".wwww.",
        "......",
    ],
}

# 96×108 高精細畫布。比例取自先前選定的 A7 造型（頭較大、外側觸手往兩旁翹），
# 並把身體（脖子到下襬）和腿（下襬到地面）調成一樣長；上衣和長褲同寬（各 18px）。
DESIGN_MV = dict(
    W=96, H=108, cx=48.0, ground=102.0,
    head=(33.0, 14.4, 13.6),
    face=(40.0, 12.0, 9.2),
    hi=(6.0, 24.6, 4.2, 2.4),
    neck=47.0,
    eye=(6.4, 33.6),
    tent_y=43.6,
    tent_r=2.1,
    tentacles=[
        (-11.2,  62, 10.4,  14),
        ( -6.8,  10, 13.2,  -6),
        (  0.0,   0, 16.8,   0),
        (  6.8, -10, 13.2,   6),
        ( 11.2, -62, 10.4, -14),
    ],
    torso=(60.7, 9.0, 14.5, 3.2),      # 46.2 ~ 75.2
    hem=74.4,
    shoulder=(10.2, 50.2),
    arm=(12.6, 12.0, 2.3),
    hand=2.5,
    hips=(78.0, 9.0, 4.4),
    hip=(4.5, 78.4),
    leg_r=4.5,
    ankle=96.2,
    shoe=(4.6, 2.6),
)

LAYERS = {
    "legs": {1, 2, 3, 11, 12},
    "torso": {4},
    "upperL": {5},
    "foreL": {7, 25},
    "upperR": {6},
    "foreR": {8, 26},
    "head": set(range(30, 40)) | {50},
}


def T(tx, ty):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1.0]])


def R(deg, cx, cy):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return T(cx, cy) @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]]) @ T(-cx, -cy)


def S(sx, sy, cx, cy):
    return T(cx, cy) @ np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1.0]]) @ T(-cx, -cy)


def pt(M, x, y):
    v = M @ np.array([x, y, 1.0])
    return float(v[0]), float(v[1])


def dilate(m):
    out = m.copy()
    out[1:, :] |= m[:-1, :]
    out[:-1, :] |= m[1:, :]
    out[:, 1:] |= m[:, :-1]
    out[:, :-1] |= m[:, 1:]
    return out


class Canvas:
    def __init__(self, w, h, names):
        self.w, self.h = w, h
        self.idx = {n: i + 1 for i, n in enumerate(names)}
        self.allow = None
        self.col = np.zeros((h, w), int)
        self.part = np.zeros((h, w), int)
        self.fx = np.zeros((h, w), int)   # 無黑框乾淨特效層（彩墨、星芒、蒸氣、花火）
        ys, xs = np.mgrid[0:h, 0:w]
        self.px, self.py = xs + 0.5, ys + 0.5

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

    def poly(self, pts):
        # 向量化多邊形遮罩
        n = len(pts)
        inside = np.zeros((self.h, self.w), dtype=bool)
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            cond = ((yi > self.py) != (yj > self.py)) & (
                self.px < (xj - xi) * (self.py - yi) / ((yj - yi) + 1e-9) + xi
            )
            inside ^= cond
            j = i
        return inside

    def paint(self, mask, color, part, sep=None):
        if self.allow is not None and part not in self.allow:
            return
        if sep is not None:
            ring = dilate(mask) & ~mask & (self.col > 0)
            self.col[ring] = self.idx[sep]
        self.col[mask] = self.idx[color]
        self.part[mask] = part

    def paint_fx(self, mask, color):
        if self.allow is not None:
            return
        self.fx[mask] = self.idx[color]

    def stamp(self, rows, cx, cy, legend, part):
        if self.allow is not None and part not in self.allow:
            return
        h, w = len(rows), len(rows[0])
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in legend and 0 <= y0 + j < self.h and 0 <= x0 + i < self.w:
                    self.col[y0 + j, x0 + i] = self.idx[legend[ch]]
                    self.part[y0 + j, x0 + i] = part


REST = dict(
    dy=0, lean=0, tilt=0, bob=0, squash=1.0,
    profile_r=False,                # True: #08-#11 朝右側身構圖！
    sway=0.0, sway_amp=3.0, flare=0.0, tent_lag=0.0, tent_wind=0.0,
    hi_side=1,
    eyes="chill",
    shirt="sweater",
    fez=False,
    armL=(4, 0, False), armR=(4, 0, False),   # 垂著時整隻手是一直線，不彎手肘
    legL=(0, 0), legR=(0, 0),
    peaceR=False, threeFingerR=False, openPalmR=False, pointAtYou=False, pointLeft=False, sparkle=0,
    bubble=0.0,                     # #08-#11 側身吹紅氣球進度
    cup_mouth=False,                # #08 側身雙手捧嘴
    bat=None,
    ball=None,                      # 紅球：(x, y, 拖尾方向, 是否正被擊中)；x 為 None 時握在左手掌心
    two_hands=False,                # 雙手握棒：前臂橫過身體時要描邊，兩隻手掌畫在球棒上
    paint_arc=None,
    red_bar=None,
    piano=None,
    book=None,
    pingpong=None,
    coffee_sip=None,                # #54 0.0~1.0 雙手端白瓷咖啡杯啜飲高度
    flare_gun=None,
)

SHIRT_SHADE = {
    "sweater": "sweater_sh",
    "teal_t": "teal_sh",
    "yellow_t": "yellow_sh",
    "navy_t": "navy_slv",
    "suit": "suit_sh",
    "tan_j": "tan_sh",
}


def render_profile_right(c, d, p):
    """#08-#11 忠於原始 MV 截圖的「朝右側身吹紅泡泡」專屬高精細渲染！"""
    cx = d["cx"] - 6.0  # 角色站左側，留右側空間給長吹管與大紅氣球
    ground = d["ground"]
    body = R(p["lean"], cx, ground)
    head = body @ R(p["tilt"], cx, d["neck"])

    # 1. 側身深藍灰直筒寬褲（#08-#10）與休閒鞋
    c.paint(c.box(body, cx + 1.2, 99.0, 6.2, 2.5, 1.0), "shoe", 11)
    c.paint(c.box(body, cx + 1.2, 100.8, 6.2, 1.0, 0.4), "shoe_sole", 11)
    pants_m = c.box(body, cx, 83.0, 6.8, 15.0, 2.0)
    c.paint(pants_m, "jeans_sh", 1)
    # 褲摺線（#09 側面褲線）
    p_top = pt(body, cx + 1.2, 72.0)
    p_bot = pt(body, cx + 1.8, 96.0)
    c.col[c.capsule(p_top, p_bot, 0.7) & (c.col == c.idx["jeans_sh"])] = c.idx["line"]

    # 2. 後側左手微垂在褲頭前方（如 #09 截圖）
    if not p["cup_mouth"]:
        la_s = pt(body, cx + 3.5, 62.0)
        la_w = pt(body, cx + 8.5, 70.5)
        la_h = pt(body, cx + 10.2, 73.2)
        c.paint(c.capsule(la_s, la_w, 2.5), "sweater_sh", 5)
        c.paint(c.ellipse(T(0, 0), la_h[0], la_h[1], 2.4, 2.2), "skin", 25, sep="line")

    # 3. 米白長袖襯衫側身軀幹 + 翻領（#09 頸後白翻領與膚色後頸！）
    neck_skin = c.box(head, cx + 0.5, 44.5, 3.8, 3.2, 0.8)
    c.paint(neck_skin, "skin", 4)
    torso_m = c.box(body, cx - 0.4, 59.5, 7.6, 12.8, 3.6)
    c.paint(torso_m, "sweater", 4)
    c.paint(torso_m & c.box(body, cx - 0.4, 70.8, 7.6, 1.4), "sweater_sh", 4)
    # 襯衫翻領 (#09)
    col_pts = [pt(body, cx - 5.2, 45.2), pt(body, cx + 3.0, 48.0),
               pt(body, cx + 1.5, 51.2), pt(body, cx - 6.0, 47.8)]
    c.paint(c.poly(col_pts), "sweater", 4, sep="line")

    # 4. 側身章魚圓頭（後腦勺飽滿向左延伸、臉部朝右、頭頂高光如 #10）
    head_back = c.ellipse(head, cx - 2.6, 32.0, 12.4, 11.8)
    head_front = c.ellipse(head, cx + 2.8, 34.8, 8.8, 9.8)
    c.paint(head_back | head_front, "head", 50)
    # 頭頂白色弧形反光 (#09-#10)
    c.paint(c.ellipse(head, cx - 2.5, 22.8, 4.8, 1.5), "head_hi", 50)

    # 側臉右向半垂死魚眼（單眼！）
    eye_mode = "wide" if p["eyes"] == "wide" else "chill"
    c.stamp(EYE_PROFILE_R[eye_mode], *pt(head, cx + 5.8, 31.4),
            {"w": "white", "k": "ink", "d": "head_sh"}, 50)

    # 側面順胸前垂下的 4 根長觸手（#09-#10 垂在右胸與衣領前）
    for idx_t, (ox, ln, curl_x) in enumerate([(1.2, 16.5, -0.5), (3.8, 18.2, 1.2), (6.2, 16.8, 2.4), (8.2, 13.5, 3.0)]):
        wob = 1.2 * math.sin(p["sway"] + idx_t * 0.9)
        t0 = pt(head, cx + ox, 39.5)
        t1 = pt(head, cx + ox + 0.6 + wob * 0.5, 39.5 + ln * 0.55)
        t2 = pt(head, cx + ox + curl_x + wob, 39.5 + ln)
        c.paint(c.capsule(t0, t1, 1.9) | c.capsule(t1, t2, 1.7), "head", 30 + idx_t)
        c.paint(c.capsule(t2, t2, 1.6), "head_sh", 30 + idx_t)

    # 5. #09-#11 細長水平紅吹管 + 亮面大紅氣球（先畫吹管再畫握嘴的右手，手部遮擋更自然！）
    bp = p["bubble"]
    mouth_pt = pt(head, cx + 10.6, 36.8)
    if bp > 0:
        if bp < 0.88:
            tube_len = 5.0 + bp * 15.5
            rad = 2.6 + bp * 8.6
            bx_c = mouth_pt[0] + tube_len + rad * 0.82
            by_c = mouth_pt[1] - 0.5 - bp * 1.4
            # 水平雙色細長吹管 (#10)
            c.paint(c.capsule(mouth_pt, (bx_c - rad * 0.5, by_c), 1.35), "red_ink", 65, sep="line")
            c.paint(c.capsule((mouth_pt[0] + 1.5, mouth_pt[1] - 0.4),
                              (bx_c - rad * 0.7, by_c - 0.4), 0.55), "blower_pk", 65)
            # 渾圓大紅氣球 + 右上亮白粉反光 (#10-#11)
            c.paint(c.ellipse(T(0, 0), bx_c, by_c, rad, rad), "red_ink", 65, sep="line")
            if rad >= 4.2:
                c.paint(c.ellipse(R(-25, bx_c + rad * 0.34, by_c - rad * 0.34),
                                  bx_c + rad * 0.34, by_c - rad * 0.34,
                                  rad * 0.28, rad * 0.16), "bubble_hi", 65)
        else:
            # 啵一聲破掉飛散的小紅水滴（無黑框特效層更輕盈）
            bx_c = mouth_pt[0] + 24.0
            by_c = mouth_pt[1] - 2.0
            for ang_d, dist in ((18, 9.5), (75, 8.5), (145, 8.0), (215, 8.5), (295, 9.0), (-35, 10.5)):
                ar = math.radians(ang_d)
                px_d, py_d = bx_c + math.cos(ar) * dist, by_c + math.sin(ar) * dist
                c.paint_fx(c.capsule((px_d, py_d), (px_d + math.cos(ar) * 1.6, py_d + math.sin(ar) * 1.6), 1.4), "red_ink")

    # 6. 右手自然在胸前彎曲（手肘朝右下收在胸肋前、前臂垂直往上捧在嘴邊，忠於 #09-#10！）
    sh_pt = pt(body, cx - 1.2, 52.5)
    if bp >= 0.88:
        # 氣球破掉時手微放低
        el_pt = pt(body, cx + 4.5, 61.5)
        wr_pt = pt(body, cx + 13.5, 56.0)
        hd_pt = pt(body, cx + 15.8, 55.2)
    else:
        el_pt = pt(body, cx + 7.2, 60.8)
        wr_pt = pt(head, cx + 9.4, 43.8)
        hd_pt = pt(head, cx + 9.6, 39.2)

    if p["cup_mouth"]:
        # #08 第二隻手在旁微微合捧
        hd2 = pt(head, cx + 12.4, 39.8)
        c.paint(c.ellipse(T(0, 0), hd2[0], hd2[1], 2.6, 3.0), "skin_sh", 26, sep="line")

    c.paint(c.ellipse(T(0, 0), hd_pt[0], hd_pt[1], 2.7, 3.4), "skin", 26, sep="line")
    arm_m = c.capsule(sh_pt, el_pt, 3.1) | c.capsule(el_pt, wr_pt, 2.8)
    c.paint(arm_m, "sweater", 6, sep="line")

    # 乾淨 1px 深色外框 + 疊加無黑框特效層
    filled = c.col > 0
    c.col[dilate(filled) & ~filled] = c.idx["line"]
    fx_mask = c.fx > 0
    c.col[fx_mask] = c.fx[fx_mask]
    return c


def render(d=DESIGN_MV, pose=None, only=None):
    p = dict(REST)
    if pose:
        p.update(pose)
    c = Canvas(d["W"], d["H"], list(PALETTE))
    c.allow = LAYERS[only] if only else None

    if p["profile_r"] and c.allow is None:
        return render_profile_right(c, d, p)

    cx, ground = d["cx"], d["ground"]
    dy = round(p["dy"])
    sq = p["squash"]
    sx = 1.0 + (1.0 - sq) * 0.40
    body = T(0, dy) @ R(p["lean"], cx, ground) @ S(sx, sq, cx, ground)
    head = body @ R(p["tilt"], cx, d["neck"]) @ T(0, round(p["bob"]))

    shirt_col = p["shirt"]
    shirt_sh = SHIRT_SHADE.get(shirt_col, "sweater_sh")
    short_sleeve = shirt_col in ("teal_t", "yellow_t", "navy_t")
    upper_sleeve_col = "navy_slv" if shirt_col == "navy_t" else shirt_col
    pants_col = "suit" if shirt_col in ("suit", "tan_j") else "jeans"
    pants_sh = "suit_sh" if shirt_col in ("suit", "tan_j") else "jeans_sh"
    shoe_col = "olive_shoe" if shirt_col == "tan_j" else "shoe"

    # 1. 嚴格 1:1 男版直筒褲與球鞋
    hx, hy = d["hip"]
    jump_dy = dy if dy < 0 else 0
    for part, side, (ldx, lift) in ((1, -1, p["legL"]), (2, 1, p["legR"])):
        hipp = pt(body, cx + side * hx, hy)
        fx = cx + side * hx + round(ldx)
        fy = d["ankle"] - round(lift) + jump_dy
        sw, sh = d["shoe"]
        c.paint(c.box(T(0, 0), fx + side * 0.4, fy + sh, sw, sh, 1.4), shoe_col, 10 + part)
        c.paint(c.box(T(0, 0), fx + side * 0.4, fy + sh * 1.68, sw, sh * 0.42, 0.5), "shoe_sole", 10 + part)
        c.paint(c.capsule(hipp, (fx, fy - 0.5), d["leg_r"]), pants_col, part)

    hcy, hhw, hhh = d["hips"]
    c.paint(c.box(body, cx, hcy, hhw, hhh, 1.8), pants_col, 3)
    if c.allow is None or 3 in c.allow:
        seam_top = pt(body, cx, hcy + 2.0)
        min_lift = max(p["legL"][1], p["legR"][1])
        seam_bot = (cx, d["ankle"] - 1.8 - min_lift * 0.5 + jump_dy)
        c.col[c.capsule(seam_top, seam_bot, 0.9) & (c.col == c.idx[pants_col])] = c.idx["line"]
        for side, (ldx, lift) in ((-1, p["legL"]), (1, p["legR"])):
            fx = cx + side * hx + round(ldx)
            fy = d["ankle"] - round(lift) + jump_dy
            c.col[c.box(T(0, 0), fx, fy - 2.0, 4.0, 1.0) & (c.col == c.idx[pants_col])] = c.idx[pants_sh]

    # 2. 直筒上衣軀幹（+ 西裝白襯衫領帶 / #54 卡其夾克內搭白圓領T）
    tcy, thw, thh, tr = d["torso"]
    torso_mask = c.box(body, cx, tcy, thw, thh, tr)
    c.paint(torso_mask, shirt_col, 4)
    c.paint(torso_mask & c.box(body, cx, d["hem"], thw, 1.2), shirt_sh, 4)
    if shirt_col == "suit" and c.allow is None:
        c.paint(c.box(body, cx, 50.2, 3.2, 4.2, 0.8), "white", 4)
        c.paint(c.capsule(pt(body, cx, 49.5), pt(body, cx, 55.0), 0.9), "ink", 4)
    elif shirt_col == "tan_j" and c.allow is None:
        # #54 卡其夾克領口露出的白色內搭 T 與前襟縫線
        c.paint(c.ellipse(body, cx, 48.2, 3.8, 2.4), "white", 4)
        c.col[c.capsule(pt(body, cx, 51.0), pt(body, cx, 69.5), 0.55) & torso_mask] = c.idx["tan_sh"]

    # 3. 零斷手連貫雙段手臂
    wrist_pts = {}

    def draw_arm(part, side, spec):
        a1, a2, in_front = spec
        sx_off, sy_off = d["shoulder"]
        L1, L2, r = d["arm"]
        s_chest = pt(body, cx + side * (sx_off - 2.8), sy_off + 1.0)
        s0 = pt(body, cx + side * sx_off, sy_off)
        rad1 = math.radians(a1)
        rad2 = math.radians(a1 + a2)
        e_loc = (cx + side * sx_off + side * L1 * math.sin(rad1), sy_off + L1 * math.cos(rad1))
        w_loc = (e_loc[0] + side * L2 * math.sin(rad2), e_loc[1] + L2 * math.cos(rad2))
        h_loc = (e_loc[0] + side * (L2 + 2.0) * math.sin(rad2), e_loc[1] + (L2 + 2.0) * math.cos(rad2))
        e, w, hnd = pt(body, *e_loc), pt(body, *w_loc), pt(body, *h_loc)
        wrist_pts[side] = hnd

        sleeve_r = r * 1.15 if short_sleeve else r
        upper = c.capsule(s_chest, s0, sleeve_r * 1.05) | c.capsule(s0, e, sleeve_r)
        fore_col = "skin" if short_sleeve else shirt_col
        fore_r = r * 0.80 if short_sleeve else r * 0.95
        fore = c.capsule(e, w, fore_r)
        full_arm = upper | fore

        if c.allow is None:
            if in_front:
                ring = dilate(full_arm) & ~full_arm & (c.col > 0) & (c.part != 4)
                c.col[ring] = c.idx["line"]
                inner_sh = dilate(upper) & ~upper & (c.part == 4) & (c.py > s0[1] + 3.0)
                c.col[inner_sh] = c.idx[shirt_sh]
                if p["two_hands"]:      # 前臂橫在同色的上衣前面時，描一圈邊才看得出手臂
                    c.col[dilate(fore) & ~full_arm & (c.part == 4)] = c.idx["line"]
            else:
                crease = dilate(full_arm) & ~full_arm & (c.part == 4) & (c.py > s0[1] + 4.0)
                c.col[crease] = c.idx["line"]
            c.paint(upper, upper_sleeve_col, part)
            c.paint(fore, fore_col, part)
        else:
            c.paint(upper, upper_sleeve_col, part)
            c.paint(fore, fore_col, part + 2)

        c.paint(c.capsule(hnd, hnd, d["hand"]), "skin", part + 20)

    for part, side, spec in ((5, -1, p["armL"]), (6, 1, p["armR"])):
        if not spec[2]:
            draw_arm(part, side, spec)
    for part, side, spec in ((5, -1, p["armL"]), (6, 1, p["armR"])):
        if spec[2]:
            draw_arm(part, side, spec)

    # 4. 胸前 5 根柔順長觸手（#54 喝咖啡時中間觸手微向兩側分開露出馬克杯！）
    r_arm_up = p["armR"][2] and p["armR"][0] > 90
    l_arm_up = p["armL"][2] and p["armL"][0] > 90
    part_moustache = 1.0 if p["coffee_sip"] is not None else 0.0
    for i, (bx, ang, L, curl) in enumerate(d["tentacles"]):
        side = -1 if bx < 0 else (1 if bx > 0 else -1)
        arm_lift = 14 if (i == 4 and r_arm_up) else (-14 if (i == 0 and l_arm_up) else 0)
        wob = p["sway_amp"] * math.sin(p["sway"] + i * 0.85)
        wind = p["tent_wind"]
        if p["flare"] > 1.05 and i in (1, 2, 3):
            up_ang = 155 if i == 2 else (132 * (-1 if i == 1 else 1))
            a = math.radians(up_ang + wob)
            b = a + math.radians(15)
        else:
            mug_spread = part_moustache * (22 * (-1 if i <= 1 else (1 if i >= 3 else 0.4)))
            ln_scale = 0.72 if (part_moustache > 0 and i == 2) else 1.0
            L = L * ln_scale
            a = math.radians(-ang - arm_lift + wind + wob + mug_spread + p["flare"] * side * 52 * (1 if abs(bx) > 5 else 0.5))
            b = a + math.radians(-curl + wind * 0.45 + 1.4 * p["sway_amp"] * math.sin(p["sway"] + i * 0.85 - 0.9))
        p0 = pt(head, cx + bx, d["tent_y"])
        p1_r = pt(head, cx + bx + 0.55 * L * math.sin(a), d["tent_y"] + 0.55 * L * math.cos(a))
        p2_r = pt(head, cx + bx + 0.55 * L * math.sin(a) + 0.45 * L * math.sin(b),
                  d["tent_y"] + 0.55 * L * math.cos(a) + 0.45 * L * math.cos(b))
        p1 = (p1_r[0], p1_r[1] + p["tent_lag"] * 0.5)
        p2 = (p2_r[0], p2_r[1] + p["tent_lag"])
        c.paint(c.capsule(p0, p1, d["tent_r"]) | c.capsule(p1, p2, d["tent_r"] * 0.92), "head", 30 + i)
        c.paint(c.capsule(p2, p2, d["tent_r"] * 0.88), "head_sh", 30 + i)

    # 5. 章魚圓頂頭 + 高光 + #54 土耳其紅毯帽（梯形帽身＋側面黑流蘇！）
    hcy2, hrx, hry = d["head"]
    fcy, frx, fry = d["face"]
    c.paint(c.ellipse(head, cx, hcy2, hrx, hry) | c.ellipse(head, cx, fcy, frx, fry), "head", 50)
    hix, hiy, hirx, hiry = d["hi"]
    if not p["fez"]:
        if p["hi_side"] == 0:
            c.paint(c.ellipse(head, cx, hiy - 1.4, 5.6, 1.7), "head_hi", 50)
        else:
            c.paint(c.ellipse(head, cx + p["hi_side"] * hix, hiy, hirx, hiry), "head_hi", 50)
    else:
        # #54 梯形暗紅土耳其帽 (Fez) + 黑色垂墜流蘇
        fez_pts = [
            pt(head, cx - 7.4, 16.2), pt(head, cx + 7.4, 16.2),
            pt(head, cx + 9.2, 25.4), pt(head, cx - 9.2, 25.4),
        ]
        fez_m = c.poly(fez_pts)
        c.paint(fez_m, "fez", 50, sep="line")
        c.paint(fez_m & c.box(head, cx + 5.5, 20.8, 3.8, 5.0), "fez_sh", 50)
        # 黑色流蘇 (#54 帽右側黑穗)
        c.paint(c.capsule(pt(head, cx + 6.4, 17.5), pt(head, cx + 7.8, 24.2), 1.05), "ink", 50)

    # 6. 半垂死魚眼 / #54 圓墨鏡（含鏡框橫樑與耳側鏡腳）
    ex, ey = d["eye"]
    for side in (-1, 1):
        c.stamp(EYES[p["eyes"]], *pt(head, cx + side * ex, ey),
                {"w": "white", "k": "ink", "d": "head_sh"}, 50)
    if p["eyes"] == "glasses" and c.allow is None:
        pL = pt(head, cx - ex, ey)
        pR = pt(head, cx + ex, ey)
        c.paint(c.capsule(pL, pR, 0.85), "ink", 50)
        c.paint(c.capsule(pt(head, cx - 10.2, ey - 0.5), pL, 0.75), "ink", 50)
        c.paint(c.capsule(pR, pt(head, cx + 10.2, ey - 0.5), 0.75), "ink", 50)

    # 7. 前景手勢與道具繪製
    for part, side, spec in ((5, -1, p["armL"]), (6, 1, p["armR"])):
        if spec[2] and (abs(spec[1]) > 75 or p["pointAtYou"] or p["pointLeft"]
                        or p["peaceR"] or p["threeFingerR"] or p["openPalmR"]):
            draw_arm(part, side, spec)

    if c.allow is None:
        hR = wrist_pts.get(1, (cx + 14, 56))
        hL = wrist_pts.get(-1, (cx - 14, 56))

        # (A) #64 比 V 手勢
        if p["peaceR"]:
            hx_i, hy_i = hR
            c.paint(c.capsule((hx_i - 1.6, hy_i - 0.8), (hx_i - 2.8, hy_i - 6.2), 1.15), "skin", 60)
            c.paint(c.capsule((hx_i + 1.6, hy_i - 0.8), (hx_i + 2.8, hy_i - 6.2), 1.15), "skin", 60)

        # (B1) #25 三指搖滾準備手勢
        if p["threeFingerR"]:
            hx_i, hy_i = hR
            c.paint(c.capsule((hx_i, hy_i), (hx_i, hy_i - 2.4), 3.4), "skin", 60)
            for fx_o, fh in ((-2.8, 6.8), (0.9, 6.4), (3.0, 5.6)):
                c.paint(c.capsule((hx_i + fx_o, hy_i - 2.2), (hx_i + fx_o * 1.1, hy_i - fh), 0.98), "skin", 60)

        # (B2) #26 張開五指手掌 + 無黑框金色四角星芒
        if p["openPalmR"]:
            hx_i, hy_i = hR
            c.paint(c.capsule((hx_i, hy_i), (hx_i, hy_i - 2.8), 3.7), "skin", 60)
            for fx_o, fh in ((-3.2, 6.4), (-1.2, 7.2), (0.9, 7.0), (2.9, 6.0)):
                c.paint(c.capsule((hx_i + fx_o, hy_i - 2.4), (hx_i + fx_o * 1.15, hy_i - fh), 0.95), "skin", 60)
            c.paint(c.capsule((hx_i - 2.6, hy_i - 0.6), (hx_i - 5.2, hy_i - 2.6), 0.95), "skin", 60)
            if p["sparkle"] > 0:
                sp_x, sp_y = round(hx_i - 0.5), round(hy_i - 0.5)
                arm_l = 3.2 + p["sparkle"] * 2.4
                star_m = (c.capsule((sp_x - arm_l, sp_y), (sp_x + arm_l, sp_y), 1.15) |
                          c.capsule((sp_x, sp_y - arm_l), (sp_x, sp_y + arm_l), 1.15) |
                          c.capsule((sp_x - arm_l * 0.45, sp_y - arm_l * 0.45),
                                    (sp_x + arm_l * 0.45, sp_y + arm_l * 0.45), 0.85) |
                          c.capsule((sp_x - arm_l * 0.45, sp_y + arm_l * 0.45),
                                    (sp_x + arm_l * 0.45, sp_y - arm_l * 0.45), 0.85))
                c.paint_fx(star_m, "star")
                c.paint_fx(c.ellipse(T(0, 0), sp_x, sp_y, 2.0, 2.0), "star_hi")
                if p["sparkle"] >= 2:
                    for ox, oy in ((-8, -8), (9, -7), (8, 7)):
                        c.paint_fx(c.capsule((sp_x + ox, sp_y + oy), (sp_x + ox, sp_y + oy), 1.0), "star_hi")

        # (C) #46 正面指著鏡頭的立體食指特寫
        if p["pointAtYou"]:
            hx_i, hy_i = hR
            c.paint(c.ellipse(T(0, 0), hx_i, hy_i, 4.2, 3.6), "skin", 60, sep="line")
            c.paint(c.ellipse(T(0, 0), hx_i, hy_i - 1.0, 2.0, 2.4), "skin_sh", 60)
            c.paint(c.capsule((hx_i, hy_i - 1.4), (hx_i, hy_i - 2.4), 1.35), "skin", 60)

        # (C2) #24 向左水平伸直的修長食指特寫
        if p["pointLeft"]:
            hx_i, hy_i = hL
            c.paint(c.capsule((hx_i, hy_i - 0.6), (hx_i - 5.6, hy_i - 0.8), 1.05), "skin", 60)
            c.paint(c.ellipse(T(0, 0), hx_i - 0.6, hy_i + 1.0, 2.1, 1.7), "skin_sh", 60)

        # (D) #01-#04 棒球木棒揮擊 + 無黑框書法紅墨爆裂
        if p["bat"] is not None:
            bat_ang, splash = p["bat"]
            ar = math.radians(bat_ang)
            tip = (hR[0] + math.cos(ar) * 19.0, hR[1] + math.sin(ar) * 19.0)
            mid = (hR[0] + math.cos(ar) * 8.5, hR[1] + math.sin(ar) * 8.5)
            knob = (hR[0] - math.cos(ar) * 6.0, hR[1] - math.sin(ar) * 6.0)     # 握把留給下面那隻手
            c.paint(c.capsule(knob, knob, 1.7), "wood_sh", 66)
            c.paint(c.capsule(knob, mid, 1.35), "wood_sh", 66)
            c.paint(c.capsule(mid, tip, 2.35), "wood", 66)
            if p["two_hands"]:          # 兩隻手掌握在握把上
                for hand_pt in (hL, hR):
                    c.paint(c.capsule(hand_pt, hand_pt, d["hand"]), "skin", 67, sep="line")
            if splash > 0:
                sx_c, sy_c = cx - 22.0, 75.0      # 紅墨在球棒砸到的左下方爆開
                if splash == 1:
                    c.paint_fx(c.ellipse(T(0, 0), sx_c, sy_c, 5.2, 5.2), "red_ink")
                for ang_d, dist, rr in ((-42, 9.0 * splash * 0.68, 1.9), (12, 10.5 * splash * 0.68, 2.1),
                                        (62, 8.4 * splash * 0.68, 1.7), (-112, 7.2 * splash * 0.68, 1.5),
                                        (142, 6.8 * splash * 0.68, 1.5), (-15, 13.0 * splash * 0.65, 1.2)):
                    rad_s = math.radians(ang_d)
                    px_s, py_s = sx_c + math.cos(rad_s) * dist, sy_c + math.sin(rad_s) * dist
                    c.paint_fx(c.capsule((px_s, py_s), (px_s + math.cos(rad_s) * 2.2, py_s + math.sin(rad_s) * 2.2), rr), "red_ink")

        # (D2) 紅球：握在左手、拋起、被球棒擊中、帶著拖尾飛出去
        if p["ball"] is not None:
            bx_b, by_b, trail, hit = p["ball"]
            if bx_b is None:
                bx_b, by_b = hL[0] - 0.5, hL[1] - 4.4
            if trail:
                tx_b, ty_b = trail
                c.paint_fx(c.capsule((bx_b + tx_b * 0.45, by_b + ty_b * 0.45), (bx_b + tx_b, by_b + ty_b), 1.2), "steam")
                c.paint_fx(c.capsule((bx_b + tx_b * 0.5 + 2.2, by_b + ty_b * 0.5 - 2.2),
                                     (bx_b + tx_b * 0.9 + 2.2, by_b + ty_b * 0.9 - 2.2), 0.7), "steam")
            if hit:
                for ang_h in (20, 95, 160, 235, 300):
                    rad_h = math.radians(ang_h)
                    c.paint_fx(c.capsule((bx_b + math.cos(rad_h) * 5.0, by_b + math.sin(rad_h) * 5.0),
                                         (bx_b + math.cos(rad_h) * 8.2, by_b + math.sin(rad_h) * 8.2), 0.9), "star")
            c.paint(c.ellipse(T(0, 0), bx_b, by_b, 3.3, 3.3), "red_ink", 72, sep="line")
            c.paint(c.ellipse(T(0, 0), bx_b - 1.0, by_b - 1.2, 1.0, 1.0), "head_hi", 72)

        # (E) #16 / #20 / #24 MARSILAINEN 流體彩墨水花（無黑框，乾淨柔順水弧與粉紅水珠！）
        if p["paint_arc"] is not None:
            pcol_key, prog = p["paint_arc"]
            if pcol_key == "g":
                # #16 右上方飛起的一抹薄荷綠柳葉形水彩（無生硬黑框！）
                gx, gy = cx + 21.0 + prog * 3.5, 22.0 - prog * 3.0
                blade = c.ellipse(R(62, gx, gy), gx, gy, 8.8, 2.6)
                c.paint_fx(blade, "paint_g")
                c.paint_fx(c.ellipse(R(62, gx - 0.6, gy - 0.5), gx - 0.6, gy - 0.5, 5.5, 1.1), "paint_g2")
                c.paint_fx(c.ellipse(T(0, 0), gx - 5.5, gy - 8.0, 1.5, 1.5), "paint_g")
            elif pcol_key == "b":
                # #20 越過頭頂向左垂落的流暢貝茲曲線天藍水彩緞帶（消除折角感！）
                p0 = (hL[0] + 1.0, hL[1] - 1.5)
                p1 = (cx - 18.0, 14.0 + prog * 1.5)
                p2 = (cx - 32.0, 28.0 + prog * 3.5)
                p3 = (cx - 26.0, 46.0 + prog * 3.5)
                rib = np.zeros((c.h, c.w), dtype=bool)
                prev = p0
                for step in range(1, 19):
                    u = step / 18.0
                    bx = ((1 - u)**3 * p0[0] + 3 * (1 - u)**2 * u * p1[0] +
                          3 * (1 - u) * u**2 * p2[0] + u**3 * p3[0])
                    by = ((1 - u)**3 * p0[1] + 3 * (1 - u)**2 * u * p1[1] +
                          3 * (1 - u) * u**2 * p2[1] + u**3 * p3[1])
                    rad_b = 1.6 + 2.1 * math.sin(math.pi * u)
                    rib |= c.capsule(prev, (bx, by), rad_b)
                    prev = (bx, by)
                hole = c.ellipse(R(-52, cx - 23.5, 26.5 + prog * 2.2), cx - 23.5, 26.5 + prog * 2.2, 3.6, 0.95)
                c.paint_fx(rib & ~hole, "paint_b")
                c.paint_fx(c.ellipse(R(-35, cx - 17.5, 19.8 + prog * 1.6), cx - 17.5, 19.8 + prog * 1.6, 3.8, 0.9), "paint_b2")
            elif pcol_key == "p":
                # #24 左手食指尖往左上彈出的兩顆水滴狀粉紅顏料珠！
                tip_x, tip_y = hL[0] - 6.0, hL[1] - 1.0
                d1x, d1y = tip_x - 3.5 - prog * 2.5, tip_y - 6.5 - prog * 3.0
                d2x, d2y = tip_x + 1.5 - prog * 1.2, tip_y - 5.2 - prog * 2.4
                drop1 = c.capsule((tip_x - 1.5, tip_y - 3.2), (d1x, d1y), 1.2) | c.ellipse(T(0, 0), d1x, d1y - 1.2, 2.2, 2.6)
                drop2 = c.capsule((tip_x + 1.0, tip_y - 2.6), (d2x, d2y), 1.0) | c.ellipse(T(0, 0), d2x, d2y - 1.0, 1.8, 2.2)
                c.paint_fx(drop1, "paint_p")
                c.paint_fx(drop2, "paint_p")
                c.paint_fx(c.ellipse(T(0, 0), d1x - 0.5, d1y - 1.8, 0.8, 0.8), "paint_p2")

        # (F) #27-#35 MARTIAN 紅色筆畫長棍重砸拆字 + 幾何三角碎片
        if p["red_bar"] is not None:
            bar_ang, shards = p["red_bar"]
            ar = math.radians(bar_ang)
            tip = (hR[0] + math.cos(ar) * 23.0, hR[1] + math.sin(ar) * 23.0)
            c.paint(c.capsule(hR, tip, 2.2), "red_ink", 69)
            if shards > 0:
                sh_x = cx + 23.0 + shards * 2.8
                sh_y = 48.0 + shards * 4.5
                tri = [
                    (sh_x, sh_y - 4.8),
                    (sh_x + 4.8, sh_y + 3.6),
                    (sh_x - 4.2, sh_y + 2.8),
                ]
                c.paint_fx(c.poly(tri), "red_ink")
                c.paint_fx(c.box(R(-25 * shards, cx + 18, 70 + shards * 2), cx + 18, 70 + shards * 2, 2.8, 1.8, 0.2), "red_ink")

        # (G) #36-#37 MARSJANIN 黑白鋼琴鍵盤與漂浮音符
        if p["piano"] is not None:
            ph = p["piano"]
            ky = 67.5
            c.paint(c.box(T(0, 0), cx, ky + 2.6, 21.0, 4.0, 1.0), "suit", 74, sep="line")
            c.paint(c.box(T(0, 0), cx, ky, 19.4, 2.6, 0.4), "white", 74)
            for kx in (-15.0, -10.5, -4.5, 0.0, 4.5, 10.5, 15.0):
                c.paint(c.box(T(0, 0), cx + kx, ky - 0.9, 1.15, 1.7, 0.2), "ink", 74)
            # 無黑框金色八分音符
            nx = cx + 16.5 + (ph % 2) * 4.2
            ny = 41.0 - ph * 3.0
            note_m = (c.ellipse(T(0, 0), nx, ny, 2.0, 1.5) |
                      c.capsule((nx + 1.4, ny), (nx + 1.4, ny - 5.2), 0.75) |
                      c.capsule((nx + 1.4, ny - 5.2), (nx + 3.6, ny - 3.8), 0.75))
            c.paint_fx(note_m, "star")

        # (H) #47-#48 марсианин 胸前自然捧著翻開的深藍精裝書《АЭЛИТА》
        if p["book"] is not None:
            bk_x, bk_y = hL[0] + 3.5, hL[1] - 2.2
            c.paint(c.box(R(-10, bk_x, bk_y), bk_x, bk_y, 7.6, 5.4, 0.8), "navy_t", 75, sep="line")
            c.paint(c.box(R(-10, bk_x, bk_y), bk_x + 0.6, bk_y - 1.0, 6.4, 4.0, 0.4), "white", 75)
            c.paint(c.capsule((bk_x + 0.4, bk_y - 4.4), (bk_x + 1.0, bk_y + 2.6), 0.65), "sweater_sh", 75)
            c.paint(c.capsule((bk_x - 3.6, bk_y - 1.2), (bk_x - 0.8, bk_y - 1.6), 0.65), "red_ink", 75)

        # (I) #51-#52 Huǒxīng rén 胸前握持清晰立體桌球拍 + 橘黃乒乓球與白色殘影！
        if p["pingpong"] is not None:
            ball_h = p["pingpong"]
            # 略帶 3/4 透視角度的圓形桌球拍（拍柄＋暗紅膠皮＋黑色拍邊），一眼看懂是桌球拍！
            px_p, py_p = cx + 1.5, 63.5
            # 木拍柄與握拍手指
            c.paint(c.capsule((px_p + 1.5, py_p + 4.5), (px_p + 3.2, py_p + 10.5), 1.6), "wood_sh", 70, sep="line")
            # 3/4 斜視桌球拍面（深色底板 + 暗紅膠皮）
            blade_m = c.ellipse(R(-18, px_p, py_p), px_p, py_p, 4.2, 6.2)
            rubber_m = c.ellipse(R(-18, px_p - 0.5, py_p), px_p - 0.5, py_p, 3.3, 5.4)
            c.paint(blade_m, "ink", 70, sep="line")
            c.paint(rubber_m, "paddle_red", 70)
            # 右手手指自然扣在拍柄上緣 (#51-#52)
            c.paint(c.ellipse(T(0, 0), px_p + 2.6, py_p + 5.6, 2.6, 2.2), "skin", 70, sep="line")

            # 垂直彈跳動線殘影（無黑框柔和白線）
            by_ball = py_p - 8.2 - ball_h
            if ball_h > 2.0:
                c.paint_fx(c.capsule((px_p - 0.5, by_ball + 4.2), (px_p - 0.5, by_ball + 8.5), 0.7), "steam")
            # 渾圓橘黃乒乓球 + 高光點
            ball_m = c.ellipse(T(0, 0), px_p - 0.5, by_ball, 2.8, 2.8)
            c.paint(ball_m, "ball", 71, sep="line")
            c.paint(c.ellipse(T(0, 0), px_p - 1.3, by_ball - 0.9, 0.85, 0.85), "star_hi", 71)

        # (J) #54 MARSLI 雙手自然捧在嘴邊的白瓷熱咖啡杯（含杯耳、深色咖啡液面、無黑框柔和蒸氣！）
        if p["coffee_sip"] is not None:
            sip = p["coffee_sip"]
            mx = cx
            my = 44.8 - sip * 3.2
            # 杯耳
            handle_m = c.ellipse(T(0, 0), mx + 4.4, my + 0.4, 2.2, 2.6) & ~c.ellipse(T(0, 0), mx + 4.0, my + 0.4, 1.0, 1.4)
            c.paint(handle_m, "white", 77, sep="line")
            # 白瓷馬克杯身
            mug_m = c.box(R(-6 * sip, mx, my), mx, my, 4.0, 4.5, 1.2)
            c.paint(mug_m, "white", 77, sep="line")
            c.paint(c.ellipse(R(-6 * sip, mx, my - 3.4), mx, my - 3.4, 3.1, 1.0), "wood_sh", 77)
            # 雙手自然包覆在馬克杯兩側（手肘已在下方自然收攏！）
            c.paint(c.ellipse(T(0, 0), mx - 4.4, my + 0.8, 2.4, 3.0), "skin", 77, sep="line")
            c.paint(c.ellipse(T(0, 0), mx + 4.2, my + 1.2, 2.3, 2.8), "skin", 77, sep="line")
            # 裊裊升起的白色咖啡蒸氣（無黑框！）
            st_y = my - 7.5 - (sip * 1.8)
            w1 = c.capsule((mx - 1.6, st_y), (mx - 2.6, st_y - 3.6), 0.75) | c.capsule((mx - 2.6, st_y - 3.6), (mx - 1.2, st_y - 6.8), 0.65)
            w2 = c.capsule((mx + 1.8, st_y - 1.4), (mx + 2.8, st_y - 5.0), 0.7)
            c.paint_fx(w1 | w2, "steam")

        # (K) #65-#78 紅色信號槍升空與無黑框漫天紅紫星空花瓣煙火
        if p["flare_gun"] is not None:
            st = p["flare_gun"]
            if st in (1, 2):
                c.paint(c.capsule(hR, (hR[0] + 0.8, hR[1] - 7.8), 2.1), "red_ink", 72, sep="line")
            if st == 2:
                c.paint_fx(c.capsule((hR[0] + 0.8, hR[1] - 9.2), (hR[0] + 0.8, 3.0), 2.5), "star")
                c.paint_fx(c.capsule((hR[0] + 0.8, hR[1] - 9.2), (hR[0] + 0.8, 3.0), 1.2), "white")
            if st in (3, 4):
                drop = 0 if st == 3 else 5.5
                sparks = [
                    (-28,  9 + drop, "red_ink"), (-17,  5 + drop, "flare_p"), (-6,  7 + drop, "star"),
                    (  9,  5 + drop, "red_ink"), ( 20,  9 + drop, "flare_p"), (30, 13 + drop, "red_ink"),
                    (-24, 22 + drop, "flare_p"), ( 26, 24 + drop, "star"),   (-32, 33 + drop, "red_ink"),
                    ( 33, 35 + drop, "flare_p"), (-12, 15 + drop, "star_hi"), (14, 16 + drop, "star_hi"),
                ]
                for sx_o, sy_p, scol in sparks:
                    petal = c.ellipse(R(35, cx + sx_o, sy_p), cx + sx_o, sy_p, 2.2, 1.3)
                    c.paint_fx(petal, scol)

    # 8. 全角色乾淨 1px 深色外框 + 疊加無黑框特效層
    filled = c.col > 0
    ring = dilate(filled) & ~filled
    c.col[ring] = c.idx["line"]
    fx_mask = c.fx > 0
    c.col[fx_mask] = c.fx[fx_mask]
    return c


def to_image(c):
    rgba = np.zeros((c.h, c.w, 4), np.uint8)
    for name, i in c.idx.items():
        rgba[c.col == i] = (*PALETTE[name], 255)
    return Image.fromarray(rgba, "RGBA")


# ---------------------------------------------------------------- 12 組高精細 MV 8 格像素動畫
def anim_idle(t, look="lookL"):
    """待機：呼吸、觸手輕擺、每輪眨一次眼。look 決定這一輪眼睛看哪邊（lookL 往左、lookR 往右）；
    app 和小工具每 10 秒在兩個方向之間切換一次。"""
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        ( 0,  0,  0.0, look),
        ( 0,  0,  0.9, look),
        ( 0, -2,  1.6, look),
        (-2,  0,  0.4, look),
        (-2,  0, -1.4, "half"),
        ( 0,  0, -1.8, "closed"),
        ( 0,  0, -0.6, "half"),
        ( 0,  0,  0.5, look),
    ]
    dy, bob, lag, eyes = table[idx]
    return dict(dy=dy, bob=bob, tent_lag=lag, sway=2 * math.pi * t, sway_amp=2.5, eyes=eyes)


def anim_idle_right(t):
    return anim_idle(t, "lookR")


def arm_to(side, target, bend=1, d=DESIGN_MV):
    """算出讓手掌剛好碰到 target（畫布座標）的手臂角度。side：-1 左手、1 右手；bend：手肘往哪一側彎。"""
    sx, sy = d["shoulder"]
    L1, L2 = d["arm"][0], d["arm"][1] + 2.0
    ux, uy = side * (target[0] - (d["cx"] + side * sx)), target[1] - sy
    full = math.hypot(ux, uy)
    dist = max(abs(L1 - L2) + 0.01, min(L1 + L2 - 0.01, full))
    ux, uy = ux * dist / full, uy * dist / full
    a1 = math.atan2(ux, uy) + bend * math.acos((L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist))
    a12 = math.atan2(ux - L1 * math.sin(a1), uy - L1 * math.cos(a1))
    return (math.degrees(a1), math.degrees(a12 - a1), True)


def anim_bat(t):
    """雙手持球棒：棒子舉在右肩 → 往後拉 → 斜斜往左下砸 → 收回。第 3 格是擊中的瞬間（玻璃碎裂）。"""
    idx = int(round(t * FRAMES)) % FRAMES
    cx = DESIGN_MV["cx"]
    table = [  # 身體傾斜, 握棒位置, 球棒角度, 紅墨, 右腳, 觸手被風帶動, 眼睛
        ( 0, (cx + 14, 56), -82, 0, (0, 0),   0, "chill"),
        ( 3, (cx + 16, 52), -64, 0, (-1, 2), -8, "chill"),
        ( 6, (cx + 17, 49), -46, 0, (-2, 5), -14, "squint"),
        (-5, (cx - 6, 66),  158, 1, (4, 6),  22, "wide"),
        (-8, (cx - 8, 68),  172, 2, (5, 8),  26, "wide"),
        (-5, (cx - 7, 67),  164, 0, (4, 4),  14, "chill"),
        (-1, (cx + 8, 60), -112, 0, (1, 1),   4, "chill"),
        ( 0, (cx + 13, 57), -86, 0, (0, 0),   0, "chill"),
    ]
    lean, grip, ang, splash, legR, wind, eyes = table[idx]
    ar = math.radians(ang)
    lower = (grip[0] - math.cos(ar) * 4.0, grip[1] - math.sin(ar) * 4.0)      # 左手握在右手下面
    return dict(lean=lean, armR=arm_to(1, grip), armL=arm_to(-1, lower), legR=legR,
                bat=(ang, splash), two_hands=True, tent_wind=wind, eyes=eyes)


def anim_batball(t):
    """打棒球：左手握著紅球 → 往上拋 → 雙手揮棒擊中 → 球飛出去。第 3 格擊中，第 4 格球撞上畫面。"""
    idx = int(round(t * FRAMES)) % FRAMES
    cx = DESIGN_MV["cx"]
    table = [  # 傾斜, 握棒位置, 球棒角度, 左手位置（None = 握在球棒上）, 紅球, 右腳, 眼睛
        ( 0, (cx + 13, 56),  -80, (cx - 17, 62), (None, None, None, False),        (0, 0),  "chill"),
        ( 0, (cx + 13, 55),  -78, (cx - 17, 54), (cx - 17.5, 42.0, (0, 6), False), (0, 0),  "lookL"),
        ( 5, (cx + 16, 50),  -46, None,          (cx - 18.0, 32.0, None, False),   (-2, 5), "squint"),
        (-3, (cx - 10, 56),  190, None,          (cx - 30.0, 51.0, None, True),    (4, 6),  "wide"),
        (-6, (cx - 12, 52),  235, None,          (cx - 39.0, 29.0, (8, 6), False), (5, 8),  "wide"),
        (-5, (cx - 9, 50),   262, None,          None,                             (4, 4),  "chill"),
        (-1, (cx + 8, 60),  -112, None,          None,                             (1, 1),  "chill"),
        ( 0, (cx + 13, 57),  -86, (cx - 16, 64), (None, None, None, False),        (0, 0),  "chill"),
    ]
    lean, grip, ang, left, ball, legR, eyes = table[idx]
    ar = math.radians(ang)
    if left is None:                                   # 左手握在右手下面的握把上
        left = (grip[0] - math.cos(ar) * 4.0, grip[1] - math.sin(ar) * 4.0)
    return dict(lean=lean, armR=arm_to(1, grip), armL=arm_to(-1, left), legR=legR,
                bat=(ang, 0), ball=ball, two_hands=True, eyes=eyes)


def _wave(t, eyes):
    idx = int(round(t * FRAMES)) % FRAMES
    swing = [34, 52, 70, 52, 34, 52, 70, 52][idx]          # 前臂來回揮兩次
    return dict(armR=(112, swing, True), tilt=3,              # 手掌維持圓圓的一顆，不畫手指
                bob=-1 if idx in (2, 6) else 0,
                lean=1.5 if idx in (1, 2, 5, 6) else 0, sway=2 * math.pi * t, sway_amp=3.0, eyes=eyes)


def anim_wave(t):
    """揮手：右手舉起來張開手掌左右揮。"""
    return _wave(t, "chill")


def anim_wavejoy(t):
    """開心揮手：同樣的揮手，眼睛瞇成括號般的弧形。"""
    return _wave(t, "joy")


def anim_bubble(t):
    """03 吹紅泡泡（#08-#11）：朝右側身構圖，雙手捧嘴 → 水平細長紅管吹出超大亮面紅氣球 → 破掉！"""
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        (True,  0.00,  2, "chill"),   # 0: #08 側身微低頭雙手捧嘴
        (False, 0.16,  0, "chill"),   # 1: #09 伸出紅吹管開始吹氣
        (False, 0.36, -1, "chill"),   # 2: 紅氣球鼓起
        (False, 0.58, -1, "chill"),   # 3: #10 中大型亮面紅氣球
        (False, 0.76, -2, "chill"),   # 4: #11 超大紅氣球
        (False, 0.85, -2, "wide"),    # 5: 脹到極限！
        (False, 0.94,  0, "wide"),    # 6: 啵一聲破成小紅水珠
        (True,  0.00,  1, "chill"),   # 7: 收回嘴邊準備下一輪
    ]
    cup, bub, tilt, eyes = table[idx]
    return dict(profile_r=True, cup_mouth=cup, bubble=bub, tilt=tilt,
                sway=2 * math.pi * t, sway_amp=2.2, eyes=eyes)


def anim_paint(t):
    """04 揮灑彩墨（#15-#24）：湖水綠寬 T，忠於 #16 左手遮額右手拋綠水花 → #20 過頭拉天藍水弧 → #24 平伸食指噴粉紅水珠！"""
    idx = int(round(t * FRAMES)) % FRAMES
    # (lean, tilt, armL, armR, paint_arc, pointLeft, wind, eyes)
    table = [
        (-2, -2, (112, 118, True), (58,  32, True),  None,       False,  -6, "chill"),
        (-4, -3, (118, 124, True), (118, 22, True),  ("g", 0.2), False, -12, "chill"),   # #16 左手遮額、右手往右上拋出薄荷綠水花
        (-3, -2, (116, 122, True), (132, 16, True),  ("g", 0.9), False, -10, "wide"),
        ( 4,  5, (148,  26, True), (12,   8, False), ("b", 0.2), False,  16, "chill"),   # #20 左手過頭拉出柔順天藍水彩緞帶
        ( 6,  7, (132,  36, True), (10,   6, False), ("b", 0.9), False,  22, "chill"),
        (-2, -2, (88,    3, True), (10,   6, False), ("p", 0.3), True,   16, "squint"),  # #24 左手水平伸直食指噴粉紅水珠！
        (-2, -2, (88,    3, True), (10,   6, False), ("p", 0.9), True,   14, "squint"),
        ( 0,  0, (24,   12, False),(20,  10, False), None,       False,   0, "chill"),
    ]
    lean, tilt, aL, aR, arc, ptL, wind, eyes = table[idx]
    return dict(shirt="teal_t", lean=lean, tilt=tilt, armL=aL, armR=aR,
                paint_arc=arc, pointLeft=ptL, tent_wind=wind, eyes=eyes)


def anim_sparkle(t):
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        ((56,  28, True), False, False, 0,  0, "chill"),
        ((118, 22, True), True,  False, 0, -1, "chill"),
        ((122, 20, True), True,  False, 0, -1, "chill"),
        ((128, 16, True), False, True,  2, -2, "chill"),
        ((128, 16, True), False, True,  3, -2, "chill"),
        ((126, 18, True), False, True,  2, -2, "squint"),
        ((118, 22, True), False, True,  1, -1, "chill"),
        ((52,  24, True), False, False, 0,  0, "chill"),
    ]
    armR, threeF, palm, spk, tilt, eyes = table[idx]
    return dict(shirt="teal_t", hi_side=1, armR=armR, threeFingerR=threeF, openPalmR=palm,
                sparkle=spk, tilt=tilt, sway=2 * math.pi * t, sway_amp=2.8, eyes=eyes)


def anim_smash(t):
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        ( 2, (24, 34, True), (44,  34, True), ( 35, 0),  0, "chill"),
        (-3, (64, 44, True), (94,  30, True), (-125,0), -6, "chill"),
        (-6, (124,24, True), (146, 15, True), (-135,0),-12, "wide"),
        ( 5, (64, 24, True), (80,  15, True), ( -12,1), 16, "squint"),
        ( 7, (34, 28, True), (42,  24, True), (  28,2), 12, "squint"),
        ( 4, (28, 24, True), (36,  20, True), (  35,3),  4, "chill"),
        ( 1, (14, 14, False),(26,  20, True), (  55,0),  0, "chill"),
        ( 0, ( 6,  6, False),(12,  10, False),(  75,0),  0, "chill"),
    ]
    lean, aL, aR, bar, wind, eyes = table[idx]
    sq = 0.93 if idx == 4 else 1.0
    return dict(lean=lean, squash=sq, armL=aL, armR=aR, red_bar=bar, tent_wind=wind, eyes=eyes)


def anim_piano(t):
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        ( 2,  4, (14, -36, True), (18, -28, True), 0, "lookD"),
        ( 3,  5, (18, -28, True), (12, -38, True), 1, "lookD"),
        ( 3,  6, (15, -34, True), (20, -26, True), 2, "closed"),
        ( 2,  4, (20, -26, True), (14, -36, True), 3, "lookD"),
        ( 2,  3, (12, -38, True), (18, -28, True), 0, "lookD"),
        ( 3,  5, (19, -28, True), (12, -38, True), 1, "lookD"),
        ( 4,  6, (16, -32, True), (21, -24, True), 2, "half"),
        ( 2,  4, (14, -36, True), (16, -32, True), 3, "lookD"),
    ]
    lean, tilt, aL, aR, ph, eyes = table[idx]
    return dict(shirt="suit", hi_side=1, lean=lean, tilt=tilt, armL=aL, armR=aR,
                piano=ph, sway=2 * math.pi * t, sway_amp=2.2, eyes=eyes)


def anim_point(t):
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        ( 0,  0, (144,-148, True), (144,-148, True), 1.2,   0, False, "closed"),
        (-3, -5, (148,-150, True), (148,-150, True), 1.2,  -8, False, "closed"),
        ( 6,  8, (42,   18, False),(112, -52, True), 0.4,  24, False, "chill"),
        ( 2,  3, (10,    8, False),(82,   24, True), 0.1,   8, False, "squint"),
        ( 0,  0, ( 7,    5, False),(76,   44, True), 0.0,   0, True,  "squint"),
        ( 0,  0, ( 7,    5, False),(76,   44, True), 0.0,   0, True,  "squint"),
        ( 0,  0, ( 7,    5, False),(74,   42, True), 0.0,   0, True,  "chill"),
        ( 0,  0, ( 6,    4, False),(30,   18, False),0.0,   0, False, "chill"),
    ]
    lean, tilt, aL, aR, fl, wind, pt_you, eyes = table[idx]
    return dict(shirt="yellow_t", hi_side=-1, lean=lean, tilt=tilt, armL=aL, armR=aR,
                flare=fl, tent_wind=wind, pointAtYou=pt_you, eyes=eyes)


def anim_read(t):
    """09 書房讀書（#47-#48）：手肘自然貼肋下收，右手托臉頰、左手胸前捧書，抬頭望向陽光"""
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        (-3, (22, -88, True), (24, -158, True), "lookD"),
        (-3, (24, -90, True), (24, -158, True), "lookD"),
        (-4, (26, -94, True), (24, -158, True), "half"),
        (-2, (22, -88, True), (23, -156, True), "lookD"),
        ( 2, (20, -84, True), (22, -152, True), "lookR"),
        ( 3, (20, -84, True), (22, -152, True), "lookR"),
        ( 1, (21, -86, True), (23, -154, True), "chill"),
        (-2, (22, -88, True), (24, -158, True), "lookD"),
    ]
    tilt, aL, aR, eyes = table[idx]
    return dict(shirt="sweater", hi_side=1, tilt=tilt, armL=aL, armR=aR,
                book=idx, sway=2 * math.pi * t, sway_amp=2.0, eyes=eyes)


def anim_pingpong(t):
    """10 打乒乓球（#51-#52）：深藍撞色袖 T 恤，右手肘自然下垂、前臂往胸口內收握持清晰桌球拍顛球！"""
    idx = int(round(t * FRAMES)) % FRAMES
    # a1=16~20 (上臂自然朝下微向外), a2=-74~-82 (前臂自然往胸口正中央內收，完全不外翻雞翅！)
    table = [
        ((18, -74, True),  0.4, "lookD",  0),  # #52 球擊中拍面
        ((20, -80, True),  5.2, "lookD",  0),  # 往上彈起
        ((19, -78, True), 10.2, "chill", -2),  # #51 飛到胸前觸手高度！
        ((18, -76, True),  5.6, "lookD",  0),  # 落下
        ((16, -72, True),  0.4, "lookD",  0),  # 擊中拍面
        ((20, -80, True),  5.6, "lookD",  0),  # 彈起
        ((19, -78, True), 10.6, "chill", -2),  # 最高點
        ((18, -76, True),  4.8, "lookD",  0),  # 落下
    ]
    armR, ball_h, eyes, bob = table[idx]
    return dict(shirt="navy_t", hi_side=-1, armL=(7, 5, False), armR=armR, pingpong=ball_h,
                eyes=eyes, bob=bob, sway=2 * math.pi * t, sway_amp=2.0)


def anim_cafe(t):
    """11 土耳其帽喝咖啡（#54 MARSLI）：統一完整 8 格紅毯帽＋圓墨鏡＋卡其夾克，手肘自然在外緣捧白瓷杯啜飲！"""
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        (0.0,  0, (35, -134, True), (35, -134, True)),
        (0.4, -1, (37, -138, True), (37, -138, True)),
        (0.8, -2, (39, -142, True), (39, -142, True)),
        (1.0, -3, (40, -144, True), (40, -144, True)),
        (1.0, -3, (40, -144, True), (40, -144, True)),
        (0.7, -2, (38, -140, True), (38, -140, True)),
        (0.3, -1, (36, -136, True), (36, -136, True)),
        (0.0,  0, (35, -134, True), (35, -134, True)),
    ]
    sip, bob, aL, aR = table[idx]
    return dict(shirt="tan_j", fez=True, eyes="glasses", bob=bob,
                armL=aL, armR=aR, coffee_sip=sip, sway=2 * math.pi * t, sway_amp=1.8)


def anim_flare(t):
    idx = int(round(t * FRAMES)) % FRAMES
    table = [
        ( 0,  0, (32, 60, True),  (52, 60, True),  ( 0, 0), ( 0, 0), 1, 0.0, "chill"),
        ( 0, -2, (10,  8, False), (162, 6, True),  ( 0, 0), ( 0, 0), 1, 0.1, "wide"),
        (-2, -2, (10,  8, False), (165, 4, True),  ( 0, 0), ( 0, 0), 2, 0.3, "wide"),
        (-7,  5, (112, 8, True),  (122, 8, True),  (-5, 6), ( 7, 9), 3, 0.8, "wide"),
        (-10, 3, (108, 6, True),  (115, 6, True),  (-4, 8), ( 6, 7), 4, 0.9, "wide"),
        (-8, -3, (115, 6, True),  (108, 6, True),  ( 6, 7), (-4, 6), 3, 0.8, "chill"),
        (-4, -1, (75, 12, True),  (75, 12, True),  ( 2, 4), (-2, 2), 4, 0.4, "chill"),
        ( 0,  0, (18, 10, False), (145,12, True),  ( 0, 0), ( 0, 0), None,0.0,"chill"),
    ]
    dy, lean, aL, aR, lL, lR, f_st, fl, eyes = table[idx]
    return dict(shirt="yellow_t", hi_side=0, dy=dy, lean=lean, armL=aL, armR=aR,
                legL=lL, legR=lR, peaceR=(idx == 7), flare_gun=f_st, flare=fl,
                tent_lag=-1.4 if dy < -3 else 0.4, eyes=eyes)


# 目前使用的動作。其餘動作的函式還留在上面，之後要加回來只要補回這個清單。
ANIMS = [
    ("idleL",   "01 待機（眼睛往左）", anim_idle,       165),
    ("idleR",   "02 待機（眼睛往右）", anim_idle_right, 165),
    ("bat",     "03 雙手球棒擊破",     anim_bat,        110),
    ("wave",    "04 揮手",             anim_wave,       120),
    ("wavejoy", "05 開心揮手",         anim_wavejoy,    120),
]


def font(size):
    for path in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def on_bg(img, scale, bg=BG):
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    out = Image.new("RGB", big.size, bg)
    out.paste(big, (0, 0), big)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    d = DESIGN_MV
    ddir = os.path.join(OUT, "MV")
    fdir = os.path.join(ddir, "frames")
    os.makedirs(fdir, exist_ok=True)

    to_image(render(d, {})).save(os.path.join(ddir, "sprite.png"))

    all_frames = {}
    meta = {"frame_width": d["W"], "frame_height": d["H"], "frames": FRAMES, "animations": {}}

    for name, label, fn, ms in ANIMS:
        fr = [to_image(render(d, fn(i / FRAMES))) for i in range(FRAMES)]
        all_frames[name] = fr
        sheet = Image.new("RGBA", (d["W"] * FRAMES, d["H"]))
        for i, im in enumerate(fr):
            sheet.paste(im, (i * d["W"], 0))
            im.save(os.path.join(fdir, f"{name}-{i}.png"))
        sheet.save(os.path.join(ddir, f"{name}.png"))
        bg_c = (36, 34, 56) if name in ("flare", "piano") else BG
        gif_fr = [on_bg(im, PREVIEW_SCALE, bg=bg_c) for im in fr]
        gif_fr[0].save(os.path.join(ddir, f"{name}-preview.gif"), save_all=True,
                       append_images=gif_fr[1:], duration=ms, loop=0)
        meta["animations"][name] = {"label": label, "file": f"MV/{name}.png", "frame_ms": ms}

    with open(os.path.join(OUT, "sprites.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    sc = 2
    w, h = d["W"] * sc, d["H"] * sc
    label_w = 245
    strip = Image.new("RGB", (label_w + w * FRAMES + 24, (h + 8) * len(ANIMS) + 76), (20, 23, 32))
    dr = ImageDraw.Draw(strip)
    dr.text((18, 18), "ヨルシカ《火星人》高精細 96×108 純色像素總覽",
            font=font(24), fill=(248, 248, 252))
    for j, (name, label, _, _) in enumerate(ANIMS):
        y0 = 68 + j * (h + 8)
        dr.text((16, y0 + h // 2 - 12), label, font=font(18), fill=(232, 238, 248))
        bg_card = (36, 34, 56) if name in ("flare", "piano") else BG
        for i in range(FRAMES):
            x0 = label_w + i * w
            dr.rounded_rectangle([x0 + 3, y0 + 2, x0 + w - 3, y0 + h - 2], radius=12, fill=bg_card)
            big = all_frames[name][i].resize((w, h), Image.NEAREST)
            strip.paste(big, (x0, y0), big)
    strip.save(os.path.join(OUT, "mv-all-frames.png"))
    print("Generated 96x108 HD pixel animations (96 frames) →", OUT)


if __name__ == "__main__":
    main()
