import { Constants } from "@babylonjs/core/Engines/constants";
import { DirectionalLight } from "@babylonjs/core/Lights/directionalLight";
import { HemisphericLight } from "@babylonjs/core/Lights/hemisphericLight";
import { CascadedShadowGenerator } from "@babylonjs/core/Lights/Shadows/cascadedShadowGenerator";
import "@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent";
import { Color3, Color4 } from "@babylonjs/core/Maths/math.color";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { RawCubeTexture } from "@babylonjs/core/Materials/Textures/rawCubeTexture";
import "@babylonjs/core/Engines/Extensions/engine.rawTexture";
import "@babylonjs/core/Engines/WebGPU/Extensions/engine.rawTexture";
import { InstancedMesh } from "@babylonjs/core/Meshes/instancedMesh";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { MeshBuilder } from "@babylonjs/core/Meshes/meshBuilder";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { PhysicsAggregate } from "@babylonjs/core/Physics/v2/physicsAggregate";
import { PhysicsShapeType } from "@babylonjs/core/Physics/v2/IPhysicsEnginePlugin";
import type { Scene } from "@babylonjs/core/scene";
import { CollisionLayer } from "../core/Physics";
import { TrainingDummy } from "./TrainingDummy";

export interface Arena {
  spawn: Vector3;
  dummies: TrainingDummy[];
  shadows: CascadedShadowGenerator;
  update(dt: number): void;
}

/**
 * 第 1 步的測試場景：石板地、一圈大理石柱（Instancing）、哥德式殘牆、斜坡與平台、三個假人。
 * 全部用程式產生，不需要任何外部素材，方便先把手感調好。
 */
export function createTestArena(scene: Scene): Arena {
  scene.clearColor = new Color4(0.035, 0.04, 0.055, 1);
  scene.ambientColor = new Color3(0, 0, 0);
  scene.fogMode = 2; // Scene.FOGMODE_EXP2
  scene.fogDensity = 0.012;
  scene.fogColor = new Color3(0.05, 0.06, 0.08);

  // ── 環境光照（佔位）：程式產生的漸層天空 cubemap，之後換成 .env / HDR ──
  try {
    scene.environmentTexture = createGradientEnvironment(scene);
    scene.environmentIntensity = 1.5;
  } catch (err) {
    console.warn("[arena] 無法建立環境貼圖：", err);
  }

  const hemi = new HemisphericLight("fill", new Vector3(0, 1, 0), scene);
  hemi.intensity = 0.25;
  hemi.diffuse = new Color3(0.55, 0.62, 0.8);
  hemi.groundColor = new Color3(0.12, 0.1, 0.09);

  const sun = new DirectionalLight("moon", new Vector3(-0.45, -0.8, 0.4).normalize(), scene);
  sun.intensity = 3.2;
  sun.diffuse = new Color3(1.0, 0.86, 0.7);

  // ── Cascaded Shadow Maps ──
  const shadows = new CascadedShadowGenerator(2048, sun);
  shadows.numCascades = 4;
  shadows.lambda = 0.85;
  shadows.shadowMaxZ = 70;
  shadows.cascadeBlendPercentage = 0.08;
  shadows.stabilizeCascades = true;
  shadows.filteringQuality = 1; // QUALITY_MEDIUM
  shadows.usePercentageCloserFiltering = true;
  shadows.bias = 0.004;
  shadows.normalBias = 0.02;
  shadows.autoCalcDepthBounds = false;

  // ── 材質 ──
  const stone = new PBRMaterial("stoneFloor", scene);
  stone.albedoColor = new Color3(0.21, 0.2, 0.19);
  stone.metallic = 0;
  stone.roughness = 0.82;

  const marble = new PBRMaterial("marble", scene);
  marble.albedoColor = new Color3(0.78, 0.76, 0.7);
  marble.metallic = 0;
  marble.roughness = 0.35;

  const gothic = new PBRMaterial("gothicStone", scene);
  gothic.albedoColor = new Color3(0.14, 0.14, 0.16);
  gothic.metallic = 0;
  gothic.roughness = 0.9;

  const addStatic = (mesh: AbstractMesh, type: PhysicsShapeType, castShadow = true): void => {
    const agg = new PhysicsAggregate(mesh, type, { mass: 0, friction: 0.8 }, scene);
    agg.shape.filterMembershipMask = CollisionLayer.World;
    if (!(mesh instanceof InstancedMesh)) mesh.receiveShadows = true; // instance 沿用來源網格的設定
    if (castShadow) shadows.addShadowCaster(mesh);
    mesh.freezeWorldMatrix();
  };

  // ── 地板 ──
  const ground = MeshBuilder.CreateBox("ground", { width: 90, height: 1, depth: 90 }, scene);
  ground.position.y = -0.5;
  ground.material = stone;
  addStatic(ground, PhysicsShapeType.BOX, false);

  // ── 大理石柱：一個來源網格 + Instances（同材質只算一次 draw call） ──
  const column = MeshBuilder.CreateCylinder("column", { height: 1, diameter: 1.4, tessellation: 24 }, scene);
  column.material = marble;
  column.isVisible = false;
  column.receiveShadows = true;
  const columnCount = 14;
  for (let i = 0; i < columnCount; i++) {
    const a = (i / columnCount) * Math.PI * 2;
    const broken = i % 5 === 2;
    const h = broken ? 2.2 + (i % 3) : 9;
    const inst = column.createInstance("column" + i);
    inst.scaling.y = h;
    inst.position.set(Math.sin(a) * 17, h / 2, Math.cos(a) * 17);
    inst.computeWorldMatrix(true);
    addStatic(inst, PhysicsShapeType.CYLINDER);
  }

  // ── 哥德式殘牆 ──
  const wallDefs: [number, number, number, number, number, number, number][] = [
    // x, z, 寬, 高, 厚, 旋轉Y, 高度偏移
    [0, 30, 40, 12, 2, 0, 0],
    [-30, 4, 30, 8, 2, Math.PI / 2, 0],
    [30, -6, 24, 10, 2, Math.PI / 2, 0],
    [-8, -6, 6, 3.2, 1, 0.5, 0],
    [9, 7, 5, 2.6, 1, -0.9, 0],
  ];
  wallDefs.forEach(([x, z, w, h, d, ry], i) => {
    const wall = MeshBuilder.CreateBox("wall" + i, { width: w, height: h, depth: d }, scene);
    wall.position.set(x, h / 2, z);
    wall.rotation.y = ry;
    wall.material = gothic;
    wall.computeWorldMatrix(true);
    addStatic(wall, PhysicsShapeType.BOX);
  });

  // ── 斜坡 + 平台（測試上下坡、跳躍、鏡頭碰撞） ──
  const platform = MeshBuilder.CreateBox("platform", { width: 8, height: 2, depth: 8 }, scene);
  platform.position.set(-16, 1, -18);
  platform.material = marble;
  platform.computeWorldMatrix(true);
  addStatic(platform, PhysicsShapeType.BOX);

  const rampAngle = Math.atan2(2, 8);
  const ramp = MeshBuilder.CreateBox("ramp", { width: 4, height: 0.4, depth: Math.hypot(2, 8) }, scene);
  ramp.rotation.x = rampAngle; // 左手座標：正值讓 -Z 端抬高，接上平台
  ramp.position.set(-16, 1 - 0.2 * Math.cos(rampAngle), -10);
  ramp.material = stone;
  ramp.computeWorldMatrix(true);
  addStatic(ramp, PhysicsShapeType.BOX);

  // ── 假人 ──
  const dummies = [
    new TrainingDummy(scene, "dummyA", new Vector3(0, 0, 9), 2.0),
    new TrainingDummy(scene, "dummyB", new Vector3(-7, 0, 12), 2.0, 3, 0.7),
    new TrainingDummy(scene, "dummyGiant", new Vector3(9, 0, 14), 6.0),
  ];
  for (const d of dummies) {
    shadows.addShadowCaster(d.mesh);
    d.mesh.receiveShadows = true;
  }

  return {
    spawn: new Vector3(0, 0.05, -4),
    dummies,
    shadows,
    update(dt: number): void {
      for (const d of dummies) d.update(dt);
    },
  };
}

/** 讓某些網格投射陰影（給玩家模型用） */
export function addShadowCasters(arena: Arena, meshes: Mesh[]): void {
  for (const m of meshes) {
    arena.shadows.addShadowCaster(m);
    m.receiveShadows = true;
  }
}

/** 產生 32×32×6 的漸層天空 cubemap：夜空藍 → 地平線暖光 → 深色地面 */
function createGradientEnvironment(scene: Scene): RawCubeTexture {
  const size = 32;
  const faces: Uint8Array[] = [];
  const sunDir = new Vector3(0.45, 0.8, -0.4).normalize();
  for (let face = 0; face < 6; face++) {
    const data = new Uint8Array(size * size * 4);
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const u = ((x + 0.5) / size) * 2 - 1;
        const v = ((y + 0.5) / size) * 2 - 1;
        let dx = 0;
        let dy = 0;
        let dz = 0;
        if (face === 0) [dx, dy, dz] = [1, -v, -u];
        else if (face === 1) [dx, dy, dz] = [-1, -v, u];
        else if (face === 2) [dx, dy, dz] = [u, 1, v];
        else if (face === 3) [dx, dy, dz] = [u, -1, -v];
        else if (face === 4) [dx, dy, dz] = [u, -v, 1];
        else [dx, dy, dz] = [-u, -v, -1];
        const len = Math.hypot(dx, dy, dz);
        dx /= len;
        dy /= len;
        dz /= len;

        const up = Math.max(0, dy);
        const down = Math.max(0, -dy);
        const horizon = Math.pow(1 - Math.abs(dy), 4);
        const glow = Math.pow(Math.max(0, dx * sunDir.x + dy * sunDir.y + dz * sunDir.z), 6);
        let r = 0.1 + 0.1 * up + 0.3 * horizon + 0.75 * glow - 0.07 * down;
        let g = 0.12 + 0.14 * up + 0.24 * horizon + 0.62 * glow - 0.08 * down;
        let b = 0.17 + 0.25 * up + 0.2 * horizon + 0.45 * glow - 0.12 * down;
        r = Math.min(1, Math.max(0, r));
        g = Math.min(1, Math.max(0, g));
        b = Math.min(1, Math.max(0, b));
        const i = (y * size + x) * 4;
        data[i] = r * 255;
        data[i + 1] = g * 255;
        data[i + 2] = b * 255;
        data[i + 3] = 255;
      }
    }
    faces.push(data);
  }
  return new RawCubeTexture(
    scene,
    faces,
    size,
    Constants.TEXTUREFORMAT_RGBA,
    Constants.TEXTURETYPE_UNSIGNED_BYTE,
    true,
    false,
    Constants.TEXTURE_TRILINEAR_SAMPLINGMODE,
  );
}
