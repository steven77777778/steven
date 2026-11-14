import { Matrix, Vector3 } from "@babylonjs/core/Maths/math.vector";
import type { Scene } from "@babylonjs/core/scene";

/** DOM 疊加的 HUD。第 1 步只有除錯資訊與鎖定準星。 */
export class Hud {
  private readonly debugEl = document.getElementById("debug")!;
  private readonly reticleEl = document.getElementById("reticle")!;
  private readonly projected = new Vector3();
  private readonly identity = Matrix.Identity();
  private debugTimer = 0;
  private reticleVisible = false;

  constructor(private readonly scene: Scene) {}

  /** 文字每 0.2 秒才更新一次，避免每幀改 DOM */
  setDebug(dt: number, build: () => string): void {
    this.debugTimer -= dt;
    if (this.debugTimer > 0) return;
    this.debugTimer = 0.2;
    this.debugEl.textContent = build();
  }

  setReticle(worldPos: Vector3 | null): void {
    const camera = this.scene.activeCamera;
    if (!worldPos || !camera) {
      if (this.reticleVisible) {
        this.reticleEl.style.display = "none";
        this.reticleVisible = false;
      }
      return;
    }
    const engine = this.scene.getEngine();
    const w = engine.getRenderWidth();
    const h = engine.getRenderHeight();
    Vector3.ProjectToRef(worldPos, this.identity, this.scene.getTransformMatrix(), camera.viewport.toGlobal(w, h), this.projected);
    const behind = this.projected.z < 0 || this.projected.z > 1;
    if (behind) {
      this.reticleEl.style.display = "none";
      this.reticleVisible = false;
      return;
    }
    const canvas = engine.getRenderingCanvas()!;
    const sx = canvas.clientWidth / w;
    const sy = canvas.clientHeight / h;
    this.reticleEl.style.transform = `translate(${(this.projected.x * sx).toFixed(1)}px, ${(this.projected.y * sy).toFixed(1)}px)`;
    if (!this.reticleVisible) {
      this.reticleEl.style.display = "block";
      this.reticleVisible = true;
    }
  }
}
