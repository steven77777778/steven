# 破碎聖域 Shattered Sanctum

Babylon.js（WebGPU → WebGL2 fallback）+ TypeScript + Vite + Havok 的魂系 Boss Rush。

目前進度：**第 1 步** — 第三人稱角色移動、跳躍、閃避、鎖定鏡頭、測試場景。

```bash
npm install
npm run dev        # http://localhost:5173 （加 ?webgl 強制 WebGL2）
npm run build      # 型別檢查 + 正式版輸出到 dist/
npm run preview    # 預覽正式版
```

| 操作 | 鍵鼠 | 手把（Xbox 配置） |
| --- | --- | --- |
| 移動 | WASD | 左搖桿 |
| 視角 | 滑鼠（點擊畫面啟用 Pointer Lock） | 右搖桿 |
| 閃避／按住奔跑 | Shift | B |
| 跳躍 | Space | A |
| 鎖定／解除 | 滑鼠中鍵、Tab | R3 |
| 切換目標 | 滾輪 | 右搖桿左右撥 |
| Inspector（僅 dev） | F2 | — |

手感參數都在 `src/config/tuning.ts`，執行中可在 console 用 `__game.tuning` 即時修改。
