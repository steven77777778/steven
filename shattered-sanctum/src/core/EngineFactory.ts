import type { AbstractEngine } from "@babylonjs/core/Engines/abstractEngine";

export type Backend = "WebGPU" | "WebGL2";

export interface EngineBundle {
  engine: AbstractEngine;
  backend: Backend;
}

/**
 * 優先建立 WebGPU 引擎，不支援或初始化失敗時退回 WebGL2。
 * 網址加上 `?webgl` 可強制使用 WebGL2（方便比較效能與除錯）。
 * 兩種引擎都用動態 import，沒用到的後端不會被下載。
 */
export async function createEngine(canvas: HTMLCanvasElement): Promise<EngineBundle> {
  const forceWebGL = new URLSearchParams(location.search).has("webgl");

  if (!forceWebGL && "gpu" in navigator) {
    try {
      const { WebGPUEngine } = await import("@babylonjs/core/Engines/webgpuEngine");
      if (await WebGPUEngine.IsSupportedAsync) {
        const engine = new WebGPUEngine(canvas, {
          antialias: true,
          stencil: true,
          powerPreference: "high-performance",
          adaptToDeviceRatio: false,
        });
        await engine.initAsync();
        return { engine, backend: "WebGPU" };
      }
    } catch (err) {
      console.warn("[engine] WebGPU 初始化失敗，退回 WebGL2：", err);
    }
  }

  const { Engine } = await import("@babylonjs/core/Engines/engine");
  const engine = new Engine(
    canvas,
    true,
    { stencil: true, powerPreference: "high-performance", preserveDrawingBuffer: false },
    false,
  );
  return { engine, backend: "WebGL2" };
}
