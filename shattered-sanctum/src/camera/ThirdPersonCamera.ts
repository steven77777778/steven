import { TargetCamera } from "@babylonjs/core/Cameras/targetCamera";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { PhysicsRaycastResult } from "@babylonjs/core/Physics/physicsRaycastResult";
import type { PhysicsEngine } from "@babylonjs/core/Physics/v2/physicsEngine";
import type { Scene } from "@babylonjs/core/scene";
import { tuning } from "../config/tuning";
import { clamp, damp, dampAngle, dampFactor, wrapAngle } from "../core/math";
import { CollisionLayer } from "../core/Physics";

/**
 * 第三人稱鏡頭。
 *  - 自由模式：滑鼠／右搖桿控制 yaw、pitch
 *  - 鎖定模式：yaw、pitch 自動追蹤「玩家 → 目標」方向，玩家永遠在畫面下方、目標在中央
 *  - 彈簧臂：用物理射線偵測牆面，被擋住時立即拉近，離開後平滑拉遠
 *
 * 角度定義（Babylon 左手座標）：yaw=0 朝 +Z，yaw 增加往 +X 轉；pitch 為正代表往下看。
 */
export class ThirdPersonCamera {
  readonly camera: TargetCamera;
  yaw = 0;
  pitch = tuning.camera.defaultPitch;

  private readonly pivot = new Vector3();
  private readonly forward = new Vector3();
  private readonly desired = new Vector3();
  private readonly lookAt = new Vector3();
  private readonly ray = new PhysicsRaycastResult();
  private currentDistance = tuning.camera.distance;
  private recenterYaw: number | null = null;
  private initialized = false;

  constructor(private readonly scene: Scene) {
    this.camera = new TargetCamera("playerCam", new Vector3(0, 3, -6), scene);
    this.camera.fov = tuning.camera.fov;
    this.camera.minZ = 0.1;
    this.camera.maxZ = 400;
    scene.activeCamera = this.camera;
  }

  /** 把鏡頭平滑轉到指定水平角（按鎖定但沒有目標時使用） */
  recenter(yaw: number): void {
    this.recenterYaw = yaw;
  }

  /**
   * @param feet 玩家腳底位置
   * @param lockPoint 鎖定目標位置，沒有鎖定傳 null
   */
  update(dt: number, lookX: number, lookY: number, feet: Vector3, lockPoint: Vector3 | null): void {
    const c = tuning.camera;

    // ── 注視點平滑跟隨玩家 ──
    const px = feet.x;
    const py = feet.y + c.pivotHeight;
    const pz = feet.z;
    if (!this.initialized) {
      this.pivot.set(px, py, pz);
      this.initialized = true;
    } else {
      const k = dampFactor(c.followDamping, dt);
      this.pivot.x += (px - this.pivot.x) * k;
      this.pivot.y += (py - this.pivot.y) * k;
      this.pivot.z += (pz - this.pivot.z) * k;
    }

    // ── 角度 ──
    let wantedDistance = c.distance;
    if (lockPoint) {
      this.recenterYaw = null;
      const dx = lockPoint.x - this.pivot.x;
      const dy = lockPoint.y - this.pivot.y;
      const dz = lockPoint.z - this.pivot.z;
      const horizontal = Math.hypot(dx, dz);
      if (horizontal > 0.3) {
        this.yaw = dampAngle(this.yaw, Math.atan2(dx, dz), c.lockYawDamping, dt);
      }
      // 目標比玩家高（巨人）時鏡頭抬頭，比玩家低時俯視；近身時減弱避免鏡頭亂甩
      const elevation = Math.atan2(-dy, Math.max(horizontal, 2.5));
      const wantedPitch = clamp(c.lockedPitch + elevation * 0.6, c.minPitch, c.maxPitch);
      this.pitch = damp(this.pitch, wantedPitch, c.lockPitchDamping, dt);
      wantedDistance = c.lockedDistance;
    } else {
      if (this.recenterYaw !== null) {
        if (lookX !== 0 || lookY !== 0) {
          this.recenterYaw = null; // 玩家一動視角就取消自動回正
        } else {
          this.yaw = dampAngle(this.yaw, this.recenterYaw, 12, dt);
          this.pitch = damp(this.pitch, c.defaultPitch, 12, dt);
          if (Math.abs(wrapAngle(this.recenterYaw - this.yaw)) < 0.01) this.recenterYaw = null;
        }
      }
      this.yaw = wrapAngle(this.yaw + lookX);
      this.pitch = clamp(this.pitch + lookY, c.minPitch, c.maxPitch);
    }

    // ── 位置 ──
    const cp = Math.cos(this.pitch);
    this.forward.set(Math.sin(this.yaw) * cp, -Math.sin(this.pitch), Math.cos(this.yaw) * cp);

    // 右肩偏移（鏡頭右方向 = (cos yaw, 0, -sin yaw)）
    const sx = Math.cos(this.yaw) * c.shoulderOffset;
    const sz = -Math.sin(this.yaw) * c.shoulderOffset;
    this.lookAt.set(this.pivot.x + sx, this.pivot.y, this.pivot.z + sz);

    this.desired.copyFrom(this.lookAt).addInPlace(this.forward.scale(-wantedDistance));

    // ── 彈簧臂碰撞 ──
    let allowed = wantedDistance;
    const physics = this.scene.getPhysicsEngine() as PhysicsEngine | null;
    if (physics) {
      this.ray.reset();
      physics.raycastToRef(this.lookAt, this.desired, this.ray, { collideWith: CollisionLayer.World });
      if (this.ray.hasHit) {
        allowed = Math.max(c.minDistance, this.ray.hitDistance - c.collisionMargin);
      }
    }
    // 被擋住：立刻拉近（否則會穿牆）；恢復：平滑拉遠
    this.currentDistance =
      allowed < this.currentDistance ? allowed : damp(this.currentDistance, allowed, c.collisionRecover, dt);

    this.camera.position.copyFrom(this.lookAt).addInPlace(this.forward.scale(-this.currentDistance));
    this.camera.setTarget(this.lookAt);
  }
}
