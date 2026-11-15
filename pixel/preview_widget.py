#!/usr/bin/env python3
"""模擬桌面小工具的畫法：把分層圖照小工具的方式疊起來、繞關節旋轉，輸出每個動作各姿勢的預覽圖。

小工具裡的旋轉是 iOS 做的，這裡用同樣的關節位置和角度重現，用來在安裝前檢查姿勢。
用法：python3 pixel/preview_widget.py  →  pixel/out/widget-poses.png
"""
import os

from PIL import Image, ImageDraw

import generate as g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "ios", "Shared", "Sprites")
K = 8                                   # 放大倍率（小工具上大約也是這個比例）

# 與 ios/Widget/PetWidget.swift 的姿勢一致。角度：度，正的是順時針。
REST = dict(armL=0, foreL=0, armR=0, foreR=0, head=0, lean=0, lift=0, squash=1)
POSES = {
    "站立": {},
    "招手 A": dict(armR=-115, foreR=-70, head=4),
    "招手 B": dict(armR=-115, foreR=-10, head=4),
    "火星人舞 左": dict(armL=22, foreL=-128, armR=-135, foreR=-12, head=-7, lean=-8),
    "火星人舞 右": dict(armL=135, foreL=12, armR=-22, foreR=128, head=7, lean=8),
    "歡呼": dict(armL=150, foreL=14, armR=-150, foreR=-14, lift=0.05),
}


def layer(name):
    im = Image.open(os.path.join(SPRITES, f"pet-part-{name}.bmp")).convert("RGBA")
    return im.resize((im.width * K, im.height * K), Image.NEAREST)


def rot(im, deg, x, y):
    """繞畫布上的像素座標 (x, y) 順時針轉 deg 度。"""
    return im.rotate(-deg, resample=Image.BICUBIC, center=(x * K, y * K)) if deg else im


def over(*ims):
    out = Image.new("RGBA", ims[0].size)
    for im in ims:
        out.alpha_composite(im)
    return out


def draw(pose):
    p = dict(REST, **pose)

    def arm(side, x, upper, fore):
        return rot(over(layer(f"upper{side}"), rot(layer(f"fore{side}"), fore, x, 31.9)), upper, x, 25.6)

    arms = {s: arm(s, x, p[f"arm{s}"], p[f"fore{s}"]) for s, x in (("L", 16.5), ("R", 27.5))}
    raised = {s: abs(p[f"arm{s}"]) > 45 or abs(p[f"fore{s}"]) > 45 for s in "LR"}
    empty = Image.new("RGBA", arms["L"].size)
    upper_body = over(layer("torso"),
                      *(arms[s] if not raised[s] else empty for s in "LR"),     # 垂著的手在觸手後面
                      rot(layer("head"), p["head"], 22, 24),
                      *(arms[s] if raised[s] else empty for s in "LR"))         # 舉起來的手在頭前面
    fig = over(layer("legs"), rot(upper_body, p["lean"], 22, 39.7))
    out = Image.new("RGBA", fig.size)
    out.alpha_composite(fig, (0, 0))
    if p["lift"]:
        shifted = Image.new("RGBA", fig.size)
        shifted.paste(fig, (0, -round(p["lift"] * fig.height)))
        out = shifted
    return out


def main():
    w, h = 44 * K, 54 * K
    sheet = Image.new("RGB", (w * len(POSES), h + 50), g.BG)
    dr = ImageDraw.Draw(sheet)
    for i, (name, pose) in enumerate(POSES.items()):
        im = draw(pose)
        sheet.paste(im, (i * w, 50), im)
        dr.text((i * w + 12, 10), name, font=g.font(26), fill=(20, 30, 40))
    path = os.path.join(ROOT, "pixel", "out", "widget-poses.png")
    sheet.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()
