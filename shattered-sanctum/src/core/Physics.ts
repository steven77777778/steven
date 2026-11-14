import HavokPhysics from "@babylonjs/havok";
// 用 ?url 讓 Vite 把 wasm 當成靜態資產輸出，dev 與 build 都找得到
import havokWasmUrl from "@babylonjs/havok/lib/esm/HavokPhysics.wasm?url";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { HavokPlugin } from "@babylonjs/core/Physics/v2/Plugins/havokPlugin";
import type { Scene } from "@babylonjs/core/scene";
// Babylon 9 的 deep import 不會自動帶入副作用，Scene.enablePhysics 需要這兩行註冊
import "@babylonjs/core/Physics/joinedPhysicsEngineComponent";
import "@babylonjs/core/Physics/v2/physicsEngineComponent";

/** 碰撞分層（bitmask） */
export const CollisionLayer = {
  World: 1 << 0, // 靜態場景：地板、牆、柱
  Enemy: 1 << 1,
  Player: 1 << 2,
} as const;

export async function enablePhysics(scene: Scene, gravity: number): Promise<HavokPlugin> {
  const havok = await HavokPhysics({ locateFile: () => havokWasmUrl });
  const plugin = new HavokPlugin(true, havok);
  scene.enablePhysics(new Vector3(0, -gravity, 0), plugin);
  return plugin;
}
