import type { AbstractEngine } from "@babylonjs/core/Engines/abstractEngine";
import { DefaultRenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline";
import { ImageProcessingConfiguration } from "@babylonjs/core/Materials/imageProcessingConfiguration";
import { Scene } from "@babylonjs/core/scene";
import { ThirdPersonCamera } from "../camera/ThirdPersonCamera";
import { LockOnSystem } from "../combat/LockOnSystem";
import { tuning } from "../config/tuning";
import { InputManager } from "../input/InputManager";
import { PlayerController } from "../player/PlayerController";
import { Hud } from "../ui/Hud";
import { addShadowCasters, createTestArena, type Arena } from "../world/TestArena";
import { createEngine, type Backend } from "./EngineFactory";
import { enablePhysics } from "./Physics";

/** 單幀最大 dt：分頁切回來或卡頓時避免角色穿牆 */
const MAX_DT = 1 / 20;

export class Game {
  readonly tuning = tuning;

  private constructor(
    readonly engine: AbstractEngine,
    readonly backend: Backend,
    readonly scene: Scene,
    readonly input: InputManager,
    readonly player: PlayerController,
    readonly camera: ThirdPersonCamera,
    readonly lockOn: LockOnSystem,
    readonly arena: Arena,
    readonly hud: Hud,
  ) {}

  static async create(canvas: HTMLCanvasElement, onProgress: (text: string) => void): Promise<Game> {
    onProgress("初始化繪圖引擎…");
    const { engine, backend } = await createEngine(canvas);

    const scene = new Scene(engine);
    scene.skipPointerMovePicking = true; // 不用 Babylon 的滑鼠拾取，省下每幀射線
    scene.autoClear = true;

    onProgress("載入物理引擎…");
    await enablePhysics(scene, tuning.player.gravity);

    onProgress("建立場景…");
    const arena = createTestArena(scene);
    const input = new InputManager(canvas);
    const camera = new ThirdPersonCamera(scene);
    const player = new PlayerController(scene, arena.spawn);
    addShadowCasters(arena, player.meshes);
    const lockOn = new LockOnSystem(scene);
    for (const d of arena.dummies) lockOn.register(d);
    const hud = new Hud(scene);

    // 第 1 步只開最基本的後製；SSAO／SSR／景深／體積光留到第 6 步畫質分級
    const pipeline = new DefaultRenderingPipeline("default", true, scene, [camera.camera]);
    pipeline.samples = 4;
    pipeline.fxaaEnabled = true;
    pipeline.bloomEnabled = true;
    pipeline.bloomThreshold = 0.85;
    pipeline.bloomWeight = 0.25;
    pipeline.bloomKernel = 48;
    pipeline.bloomScale = 0.5;
    pipeline.imageProcessing.toneMappingEnabled = true;
    pipeline.imageProcessing.toneMappingType = ImageProcessingConfiguration.TONEMAPPING_ACES;
    pipeline.imageProcessing.exposure = 1.15;
    pipeline.imageProcessing.contrast = 1.15;
    pipeline.imageProcessing.vignetteEnabled = true;
    pipeline.imageProcessing.vignetteWeight = 1.6;

    const game = new Game(engine, backend, scene, input, player, camera, lockOn, arena, hud);
    scene.onBeforeRenderObservable.add(() => game.update());
    window.addEventListener("resize", () => engine.resize());

    onProgress("編譯著色器…");
    await scene.whenReadyAsync();
    return game;
  }

  start(): void {
    this.engine.runRenderLoop(() => this.scene.render());
  }

  /** 每幀邏輯。順序很重要：輸入 → 世界 → 鎖定 → 玩家 → 鏡頭 → HUD */
  private update(): void {
    const dt = Math.min(this.engine.getDeltaTime() / 1000, MAX_DT);
    if (dt <= 0) return;

    this.input.update(dt);
    this.arena.update(dt);
    this.lockOn.update(dt, this.input, this.player.head, this.player.yaw, this.camera);

    const lockPoint = this.lockOn.target?.lockPoint ?? null;
    this.player.update(dt, this.input, this.camera.yaw, lockPoint);
    this.camera.update(dt, this.input.lookX, this.input.lookY, this.player.position, lockPoint);

    this.hud.setReticle(lockPoint);
    this.hud.setDebug(dt, () => {
      const p = this.player.position;
      return [
        `${this.backend}  ${this.engine.getFps().toFixed(0)} FPS  ${this.engine.getRenderWidth()}×${this.engine.getRenderHeight()}`,
        `pos ${p.x.toFixed(1)}, ${p.y.toFixed(1)}, ${p.z.toFixed(1)}  speed ${this.player.speed.toFixed(1)}`,
        `state ${this.player.state}${this.player.sprinting ? " (sprint)" : ""}${this.player.grounded ? "" : " (air)"}${this.player.invulnerable ? " [i-frame]" : ""}`,
        `lock ${this.lockOn.target?.name ?? "-"}  input ${this.input.lastDevice}`,
      ].join("\n");
    });
  }

  /** F2 開關 Babylon Inspector（僅 npm run dev） */
  private inspectorToken: { dispose(): void } | null = null;
  async toggleInspector(): Promise<void> {
    if (this.inspectorToken) {
      this.inspectorToken.dispose();
      this.inspectorToken = null;
      return;
    }
    // 只在開發模式提供，正式版不會打包 Inspector（它很大）
    if (!import.meta.env.DEV) return;
    const { ShowInspector } = await import("@babylonjs/inspector");
    this.inspectorToken = ShowInspector(this.scene);
    document.exitPointerLock();
  }
}
