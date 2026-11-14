import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { MeshBuilder } from "@babylonjs/core/Meshes/meshBuilder";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { PhysicsAggregate } from "@babylonjs/core/Physics/v2/physicsAggregate";
import { PhysicsMotionType, PhysicsShapeType } from "@babylonjs/core/Physics/v2/IPhysicsEnginePlugin";
import type { Scene } from "@babylonjs/core/scene";
import type { Lockable } from "../combat/LockOnSystem";
import { CollisionLayer } from "../core/Physics";

/** 測試鎖定用的假人。可設定繞圈移動，用來檢查鏡頭追蹤是否平順。 */
export class TrainingDummy implements Lockable {
  readonly lockPoint = new Vector3();
  readonly mesh: Mesh;
  alive = true;

  private time = 0;
  private readonly origin: Vector3;

  constructor(
    scene: Scene,
    readonly name: string,
    position: Vector3,
    private readonly height: number,
    /** 繞圈半徑，0 = 靜止 */
    private readonly orbitRadius = 0,
    private readonly orbitSpeed = 0.6,
  ) {
    this.origin = position.clone();
    this.mesh = MeshBuilder.CreateCapsule(name, { height, radius: height * 0.2 }, scene);
    this.mesh.position.set(position.x, position.y + height / 2, position.z);

    const mat = new PBRMaterial(name + "Mat", scene);
    mat.albedoColor = new Color3(0.55, 0.36, 0.2);
    mat.metallic = 1;
    mat.roughness = 0.45;
    this.mesh.material = mat;

    const agg = new PhysicsAggregate(this.mesh, PhysicsShapeType.CAPSULE, { mass: 0 }, scene);
    agg.shape.filterMembershipMask = CollisionLayer.Enemy;
    if (orbitRadius > 0) {
      // ANIMATED：由程式移動、會推開其他物體但不受力
      agg.body.setMotionType(PhysicsMotionType.ANIMATED);
      agg.body.disablePreStep = false;
    }
    this.update(0);
  }

  update(dt: number): void {
    if (this.orbitRadius > 0) {
      this.time += dt;
      const a = this.time * this.orbitSpeed;
      this.mesh.position.x = this.origin.x + Math.cos(a) * this.orbitRadius;
      this.mesh.position.z = this.origin.z + Math.sin(a) * this.orbitRadius;
    }
    // 鎖定點在身高約 70% 處（胸口）
    this.lockPoint.set(this.mesh.position.x, this.origin.y + this.height * 0.7, this.mesh.position.z);
  }
}
