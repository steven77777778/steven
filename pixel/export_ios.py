#!/usr/bin/env python3
"""把選定的造型（A7）輸出成 iOS app 用的圖片：每個動畫 8 格，全部是原生像素。

用法：python3 pixel/export_ios.py   →  寫入 ios/Shared/Assets.xcassets/
"""
import glob
import json
import os
import shutil

import generate as g

DESIGN = g.VARIANTS["A7"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "ios", "Shared", "Assets.xcassets")


def save(name, img):
    d = os.path.join(ASSETS, f"{name}.imageset")
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, f"{name}.png"))
    json.dump({"images": [{"idiom": "universal", "filename": f"{name}.png"}],
               "info": {"author": "xcode", "version": 1}}, open(os.path.join(d, "Contents.json"), "w"), indent=2)


def main():
    for old in glob.glob(os.path.join(ASSETS, "pet-*.imageset")):
        shutil.rmtree(old)
    for name, _, fn, _ in g.ANIMS:
        if name == "walk":                    # 走路這個動作 app 裡不用
            continue
        for i in range(g.FRAMES):
            save(f"pet-{name}-{i}", g.to_image(g.render(DESIGN, fn(i / g.FRAMES))))
    # 小工具用的分層圖：身體、頭、左右手各一張，畫布大小相同，疊起來就是完整的火星人。
    # 小工具裡由系統把各層旋轉、位移，動作才會平滑。
    straight = dict(armL=(0, 0, False), armR=(0, 0, False))
    for layer in g.LAYERS:
        save(f"pet-part-{layer}", g.to_image(g.render(DESIGN, straight, only=layer)))
    # 靈動島用的頭部特寫
    save("pet-head", g.to_image(g.render(DESIGN, {})).crop((12, 8, 32, 27)))
    print("exported", len(glob.glob(os.path.join(ASSETS, "pet-*.imageset"))), "images")


if __name__ == "__main__":
    main()
