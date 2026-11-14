import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { PhysicsRaycastResult } from "@babylonjs/core/Physics/physicsRaycastResult";
import type { PhysicsEngine } from "@babylonjs/core/Physics/v2/physicsEngine";
import type { Scene } from "@babylonjs/core/scene";
import { tuning } from "../config/tuning";
import { wrapAngle } from "../core/math";
import { CollisionLayer } from "../core/Physics";
import type { InputManager } from "../input/InputManager";

/** 任何可被鎖定的東西（Boss、小怪、訓練假人）都實作這個介面 */
export interface Lockable {
  readonly name: string;
  /** 鎖定點的世界座標（通常是胸口），每幀由擁有者更新 */
  readonly lockPoint: Vector3;
  alive: boolean;
}

export interface LockOnView {
  /** 鏡頭水平朝向（rad） */
  yaw: number;
  /** 找不到目標時把鏡頭轉回角色背後 */
  recenter(yaw: number): void;
}

export class LockOnSystem {
  target: Lockable | null = null;

  private readonly lockables: Lockable[] = [];
  private readonly ray = new PhysicsRaycastResult();
  private losBlockedTime = 0;

  constructor(private readonly scene: Scene) {}

  register(l: Lockable): void {
    this.lockables.push(l);
  }

  unregister(l: Lockable): void {
    const i = this.lockables.indexOf(l);
    if (i >= 0) this.lockables.splice(i, 1);
    if (this.target === l) this.target = null;
  }

  /**
   * @param eye 玩家頭部位置（判斷距離與視線的起點）
   * @param playerYaw 玩家面向，找不到目標時鏡頭轉回這個方向
   */
  update(dt: number, input: InputManager, eye: Vector3, playerYaw: number, view: LockOnView): void {
    const t = tuning.lockOn;

    if (input.consume("lockOn", 0.1)) {
      if (this.target) {
        this.target = null;
      } else {
        this.target = this.findBest(eye, view.yaw);
        this.losBlockedTime = 0;
        if (!this.target) view.recenter(playerYaw);
      }
    }

    if (!this.target) {
      input.clear("targetPrev");
      input.clear("targetNext");
      return;
    }

    // 自動解除：目標死亡、太遠、視線被擋太久
    if (!this.target.alive || Vector3.Distance(eye, this.target.lockPoint) > t.breakRange) {
      this.target = this.target.alive ? null : this.findBest(eye, view.yaw);
      return;
    }
    if (t.requireLineOfSight) {
      this.losBlockedTime = this.hasLineOfSight(eye, this.target.lockPoint) ? 0 : this.losBlockedTime + dt;
      if (this.losBlockedTime > t.losBreakTime) {
        this.target = null;
        return;
      }
    }

    const dir = input.consume("targetNext", 0.1) ? 1 : input.consume("targetPrev", 0.1) ? -1 : 0;
    if (dir !== 0) {
      const next = this.findSide(eye, dir);
      if (next) {
        this.target = next;
        this.losBlockedTime = 0;
      }
    }
  }

  /** 評分 = 距離 + 與鏡頭前方夾角 × 權重，越低越好 */
  private findBest(eye: Vector3, viewYaw: number): Lockable | null {
    const t = tuning.lockOn;
    let best: Lockable | null = null;
    let bestScore = Infinity;
    for (const l of this.lockables) {
      if (!l.alive) continue;
      const dx = l.lockPoint.x - eye.x;
      const dz = l.lockPoint.z - eye.z;
      const dist = Math.hypot(dx, dz);
      if (dist > t.acquireRange) continue;
      const angle = Math.abs(wrapAngle(Math.atan2(dx, dz) - viewYaw));
      // 貼身的敵人即使在鏡頭外也可以鎖定
      if (angle > t.acquireHalfAngle && dist > 3) continue;
      if (t.requireLineOfSight && !this.hasLineOfSight(eye, l.lockPoint)) continue;
      const score = dist + angle * t.angleWeight;
      if (score < bestScore) {
        bestScore = score;
        best = l;
      }
    }
    return best;
  }

  /** 以目前目標為基準，找左（-1）或右（+1）邊角度最接近的下一個目標 */
  private findSide(eye: Vector3, dir: number): Lockable | null {
    const cur = this.target!;
    const curYaw = Math.atan2(cur.lockPoint.x - eye.x, cur.lockPoint.z - eye.z);
    let best: Lockable | null = null;
    let bestDelta = Infinity;
    for (const l of this.lockables) {
      if (l === cur || !l.alive) continue;
      const dx = l.lockPoint.x - eye.x;
      const dz = l.lockPoint.z - eye.z;
      if (Math.hypot(dx, dz) > tuning.lockOn.acquireRange) continue;
      const delta = wrapAngle(Math.atan2(dx, dz) - curYaw) * dir;
      if (delta <= 0.01 || delta >= bestDelta) continue;
      if (tuning.lockOn.requireLineOfSight && !this.hasLineOfSight(eye, l.lockPoint)) continue;
      bestDelta = delta;
      best = l;
    }
    return best;
  }

  private hasLineOfSight(from: Vector3, to: Vector3): boolean {
    const physics = this.scene.getPhysicsEngine() as PhysicsEngine | null;
    if (!physics) return true;
    this.ray.reset();
    physics.raycastToRef(from, to, this.ray, { collideWith: CollisionLayer.World });
    return !this.ray.hasHit;
  }
}
