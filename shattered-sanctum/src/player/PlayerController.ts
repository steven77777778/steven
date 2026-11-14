import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { MeshBuilder } from "@babylonjs/core/Meshes/meshBuilder";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import {
  CharacterSupportedState,
  PhysicsCharacterController,
} from "@babylonjs/core/Physics/v2/characterController";
import type { Scene } from "@babylonjs/core/scene";
import { tuning } from "../config/tuning";
import { moveTowards, rotateTowards } from "../core/math";
import type { InputManager } from "../input/InputManager";

export type PlayerState = "locomotion" | "dodge";

const DOWN = Vector3.DownReadOnly;
/** 角色控制器與地面保持的間隙（公尺） */
const SKIN = 0.02;

/**
 * 玩家角色：Havok 角色控制器（膠囊）+ 簡易狀態機。
 * 第 1 步只有 移動／奔跑／跳躍／閃避；第 2 步會在這裡掛上戰鬥狀態（攻擊、格擋、彈反…）。
 */
export class PlayerController {
  /** 腳底位置與朝向的根節點，之後 GLB 模型掛在這底下 */
  readonly root: TransformNode;
  readonly meshes: Mesh[] = [];
  state: PlayerState = "locomotion";
  /** 角色面向（rad，0 = +Z） */
  yaw = 0;
  grounded = true;
  sprinting = false;
  /** 水平速率（m/s），給動畫混合與 HUD 用 */
  speed = 0;

  private readonly controller: PhysicsCharacterController;
  private readonly velocity = new Vector3();
  private readonly gravity = new Vector3();
  private readonly headPos = new Vector3();
  private stateTime = 0;
  private airTime = 0;
  private dodgeCooldown = 0;
  private dodgeDirX = 0;
  private dodgeDirZ = 1;
  private dodgeDistance = 0;
  private jumpLock = 0;

  constructor(
    private readonly scene: Scene,
    spawn: Vector3,
  ) {
    const p = tuning.player;
    this.root = new TransformNode("player", scene);
    this.buildPlaceholderKnight();

    const center = spawn.add(new Vector3(0, p.capsuleHeight / 2, 0));
    this.controller = new PhysicsCharacterController(
      center,
      { capsuleHeight: p.capsuleHeight, capsuleRadius: p.capsuleRadius },
      scene,
    );
    this.controller.maxSlopeCosine = Math.cos((50 * Math.PI) / 180); // 可走上 50° 以內的斜坡
    // 預設值（0.05 / 0.1）會讓角色浮在地面上 5~15 公分，收緊後再用 SKIN 補回視覺位置
    this.controller.keepDistance = SKIN;
    this.controller.keepContactTolerance = SKIN * 2;
    this.syncTransform();
  }

  /** 腳底世界座標 */
  get position(): Vector3 {
    return this.root.position;
  }

  /** 頭部世界座標（鎖定視線判斷用） */
  get head(): Vector3 {
    return this.headPos;
  }

  /** 閃避無敵幀中？（第 2 步的受擊判定會讀這個值） */
  get invulnerable(): boolean {
    const p = tuning.player;
    return this.state === "dodge" && this.stateTime >= p.dodgeIFrameStart && this.stateTime <= p.dodgeIFrameEnd;
  }

  teleport(feet: Vector3): void {
    this.controller.setPosition(feet.add(new Vector3(0, tuning.player.capsuleHeight / 2, 0)));
    this.controller.setVelocity(Vector3.Zero());
    this.syncTransform();
  }

  /**
   * @param cameraYaw 鏡頭水平角，移動輸入以鏡頭為基準
   * @param lockPoint 鎖定目標位置；有值時角色面向目標並橫移
   */
  update(dt: number, input: InputManager, cameraYaw: number, lockPoint: Vector3 | null): void {
    const p = tuning.player;
    this.stateTime += dt;
    this.dodgeCooldown = Math.max(0, this.dodgeCooldown - dt);
    this.jumpLock = Math.max(0, this.jumpLock - dt);

    // ── 地面偵測 ──
    const support = this.controller.checkSupport(dt, DOWN);
    this.grounded = support.supportedState === CharacterSupportedState.SUPPORTED;
    this.airTime = this.grounded ? 0 : this.airTime + dt;

    // ── 鏡頭相對的移動方向 ──
    const sin = Math.sin(cameraYaw);
    const cos = Math.cos(cameraYaw);
    let dirX = sin * input.moveY + cos * input.moveX;
    let dirZ = cos * input.moveY - sin * input.moveX;
    const inputMag = Math.min(1, Math.hypot(dirX, dirZ));
    if (inputMag > 0.001) {
      const len = Math.hypot(dirX, dirZ);
      dirX /= len;
      dirZ /= len;
    }
    const hasInput = inputMag > 0.1;

    // ── 狀態轉換 ──
    if (this.state === "dodge" && this.stateTime >= p.dodgeDuration) {
      this.setState("locomotion");
      this.dodgeCooldown = p.dodgeCooldown;
    }
    if (this.state === "locomotion" && this.grounded && this.dodgeCooldown <= 0 && input.consume("dodge")) {
      // 按下瞬間就閃避（隻狼式），之後繼續按住則轉為奔跑
      if (hasInput) {
        this.dodgeDirX = dirX;
        this.dodgeDirZ = dirZ;
        this.dodgeDistance = p.dodgeDistance;
        if (!lockPoint) this.yaw = Math.atan2(dirX, dirZ);
      } else {
        // 沒有方向輸入：後撤步
        this.dodgeDirX = -Math.sin(this.yaw);
        this.dodgeDirZ = -Math.cos(this.yaw);
        this.dodgeDistance = p.backstepDistance;
      }
      this.setState("dodge");
    }

    this.sprinting = this.state === "locomotion" && input.isHeld("dodge") && hasInput && this.grounded;

    // ── 速度 ──
    const current = this.controller.getVelocity();
    let vx = current.x;
    let vy = current.y;
    let vz = current.z;

    if (this.state === "dodge") {
      // 線性遞減的速度曲線，積分後剛好等於 dodgeDistance：起步爆發、尾段收招
      const k = 1 - this.stateTime / p.dodgeDuration;
      const s = ((2 * this.dodgeDistance) / p.dodgeDuration) * Math.max(0, k);
      vx = this.dodgeDirX * s;
      vz = this.dodgeDirZ * s;
    } else {
      const maxSpeed = this.sprinting ? p.sprintSpeed : lockPoint ? p.lockedStrafeSpeed : p.walkSpeed;
      const tx = dirX * maxSpeed * inputMag;
      const tz = dirZ * maxSpeed * inputMag;
      let rate = hasInput ? p.acceleration : p.deceleration;
      if (!this.grounded) rate *= p.airControl;
      vx = moveTowards(vx, tx, rate * dt);
      vz = moveTowards(vz, tz, rate * dt);
    }

    // ── 跳躍（含 coyote time 與輸入緩衝） ──
    const canJump = this.state === "locomotion" && this.airTime <= p.coyoteTime && this.jumpLock <= 0;
    if (canJump && input.consume("jump")) {
      vy = Math.sqrt(2 * p.gravity * p.jumpHeight);
      this.jumpLock = 0.25;
      this.grounded = false;
    } else if (this.grounded && this.jumpLock <= 0) {
      // 貼地：沿著地面法線投影，上下坡不會彈跳
      const n = support.averageSurfaceNormal;
      vy = n.y > 0.01 ? -(vx * n.x + vz * n.z) / n.y : 0;
      vy = Math.min(vy, 0) - 0.5;
    } else {
      vy -= p.gravity * dt;
    }

    this.velocity.set(vx, vy, vz);
    this.controller.setVelocity(this.velocity);
    // 重力已自行積分，這裡傳 0 避免被套用兩次
    this.gravity.set(0, 0, 0);
    this.controller.integrate(dt, support, this.gravity);

    // ── 面向 ──
    if (this.state === "locomotion") {
      if (lockPoint && !this.sprinting) {
        const dx = lockPoint.x - this.root.position.x;
        const dz = lockPoint.z - this.root.position.z;
        if (dx * dx + dz * dz > 0.04) {
          this.yaw = rotateTowards(this.yaw, Math.atan2(dx, dz), p.lockedTurnSpeed * dt);
        }
      } else if (hasInput) {
        this.yaw = rotateTowards(this.yaw, Math.atan2(dirX, dirZ), p.turnSpeed * dt);
      }
    }

    this.syncTransform();
    const actual = this.controller.getVelocity();
    this.speed = Math.hypot(actual.x, actual.z);
  }

  private setState(next: PlayerState): void {
    this.state = next;
    this.stateTime = 0;
  }

  private syncTransform(): void {
    const half = tuning.player.capsuleHeight / 2;
    const c = this.controller.getPosition();
    this.root.position.set(c.x, c.y - half - SKIN, c.z);
    this.root.rotation.y = this.yaw;
    this.headPos.set(c.x, c.y + half - 0.2, c.z);
  }

  /**
   * 佔位用騎士（基本幾何體）。第 2 步換成 GLB：
   * 把載入的模型 parent 到 this.root 並刪掉這個函式即可，其餘邏輯不用改。
   */
  private buildPlaceholderKnight(): void {
    const scene = this.scene;
    const steel = new PBRMaterial("knightSteel", scene);
    steel.albedoColor = new Color3(0.56, 0.57, 0.6);
    steel.metallic = 1;
    steel.roughness = 0.38;

    const cloth = new PBRMaterial("knightCloth", scene);
    cloth.albedoColor = new Color3(0.32, 0.05, 0.06);
    cloth.metallic = 0;
    cloth.roughness = 0.9;

    const add = (mesh: Mesh, mat: PBRMaterial, x: number, y: number, z: number): Mesh => {
      mesh.material = mat;
      mesh.parent = this.root;
      mesh.position.set(x, y, z);
      mesh.isPickable = false;
      this.meshes.push(mesh);
      return mesh;
    };

    add(MeshBuilder.CreateCapsule("torso", { height: 0.95, radius: 0.27 }, scene), steel, 0, 1.12, 0);
    add(MeshBuilder.CreateCapsule("legL", { height: 0.9, radius: 0.12 }, scene), steel, -0.14, 0.45, 0);
    add(MeshBuilder.CreateCapsule("legR", { height: 0.9, radius: 0.12 }, scene), steel, 0.14, 0.45, 0);
    add(MeshBuilder.CreateCapsule("armL", { height: 0.72, radius: 0.09 }, scene), steel, -0.37, 1.12, 0);
    add(MeshBuilder.CreateCapsule("armR", { height: 0.72, radius: 0.09 }, scene), steel, 0.37, 1.12, 0);
    add(MeshBuilder.CreateSphere("helm", { diameter: 0.34, segments: 16 }, scene), steel, 0, 1.72, 0);
    // 面甲：凸向 +Z，方便辨認角色正面
    add(MeshBuilder.CreateBox("visor", { width: 0.2, height: 0.07, depth: 0.1 }, scene), cloth, 0, 1.73, 0.15);
    add(MeshBuilder.CreateBox("tabard", { width: 0.4, height: 0.75, depth: 0.03 }, scene), cloth, 0, 0.95, 0.27);
    add(MeshBuilder.CreateBox("cape", { width: 0.5, height: 1.05, depth: 0.04 }, scene), cloth, 0, 0.95, -0.29);
    const sword = add(MeshBuilder.CreateBox("sword", { width: 0.06, height: 1.1, depth: 0.02 }, scene), steel, 0.42, 0.95, 0.3);
    sword.rotation.x = 1.15;
    add(MeshBuilder.CreateBox("guard", { width: 0.24, height: 0.04, depth: 0.04 }, scene), steel, 0.42, 0.74, 0.08).rotation.x = 1.15;
  }
}
