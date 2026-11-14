import { tuning } from "../config/tuning";

export type Action =
  | "jump"
  | "dodge"
  | "lockOn"
  | "targetPrev"
  | "targetNext"
  // 以下為第 2 步戰鬥系統預留
  | "lightAttack"
  | "heavyAttack"
  | "block";

/**
 * 輸入來源代碼：
 *  - 鍵盤：KeyboardEvent.code（"KeyW"、"Space"…）
 *  - 滑鼠："Mouse0"(左) "Mouse1"(中) "Mouse2"(右)、"WheelUp"、"WheelDown"
 *  - 手把："Pad0".."Pad16"（標準配置按鈕索引）、"PadRSLeft"、"PadRSRight"（右搖桿撥動）
 */
const bindings: Record<Action, string[]> = {
  jump: ["Space", "Pad0"],
  dodge: ["ShiftLeft", "ShiftRight", "Pad1"],
  lockOn: ["Mouse1", "Tab", "Pad11"],
  targetPrev: ["WheelUp", "PadRSLeft"],
  targetNext: ["WheelDown", "PadRSRight"],
  lightAttack: ["Mouse0", "Pad5"],
  heavyAttack: ["KeyR", "Pad7"],
  block: ["Mouse2", "Pad4"],
};

const ACTIONS = Object.keys(bindings) as Action[];

export class InputManager {
  /** 移動向量，x=右、y=前，長度 ≤ 1 */
  moveX = 0;
  moveY = 0;
  /** 本幀視角變化量（rad），已含靈敏度與 dt */
  lookX = 0;
  lookY = 0;
  /** 最後使用的裝置，用來切換 UI 提示 */
  lastDevice: "keyboard" | "gamepad" = "keyboard";

  readonly bindings = bindings;

  private readonly down = new Set<string>();
  private readonly justPressed = new Set<string>();
  private readonly held = new Map<Action, boolean>();
  private readonly pressedAt = new Map<Action, number>();
  private mouseDX = 0;
  private mouseDY = 0;
  private time = 0;
  private padPrev: boolean[] = [];
  private padFlick = 0;

  constructor(private readonly canvas: HTMLCanvasElement) {
    window.addEventListener("keydown", this.onKeyDown);
    window.addEventListener("keyup", this.onKeyUp);
    window.addEventListener("blur", this.onBlur);
    canvas.addEventListener("mousedown", this.onMouseDown);
    window.addEventListener("mouseup", this.onMouseUp);
    window.addEventListener("mousemove", this.onMouseMove);
    canvas.addEventListener("wheel", this.onWheel, { passive: false });
    canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  get pointerLocked(): boolean {
    return document.pointerLockElement === this.canvas;
  }

  /** 每幀最先呼叫 */
  update(dt: number): void {
    this.time += dt;
    const t = tuning.input;

    // ── 鍵盤移動 ──
    let mx = (this.down.has("KeyD") ? 1 : 0) - (this.down.has("KeyA") ? 1 : 0);
    let my = (this.down.has("KeyW") ? 1 : 0) - (this.down.has("KeyS") ? 1 : 0);
    const kLen = Math.hypot(mx, my);
    if (kLen > 1) {
      mx /= kLen;
      my /= kLen;
    }

    // ── 滑鼠視角 ──
    let lx = this.mouseDX * t.mouseSensitivity;
    let ly = this.mouseDY * t.mouseSensitivity;
    this.mouseDX = 0;
    this.mouseDY = 0;

    // ── 手把 ──
    const pad = this.activePad();
    if (pad) {
      const [sx, sy] = radialDeadzone(pad.axes[0] ?? 0, pad.axes[1] ?? 0, t.padDeadzone);
      const [rx, ry] = radialDeadzone(pad.axes[2] ?? 0, pad.axes[3] ?? 0, t.padDeadzone);
      if (sx !== 0 || sy !== 0) {
        mx = sx;
        my = -sy;
        this.lastDevice = "gamepad";
      }
      // 平方曲線：小幅度更精細
      lx += rx * Math.abs(rx) * t.padLookSpeedX * dt;
      ly += ry * Math.abs(ry) * t.padLookSpeedY * dt;

      for (let i = 0; i < pad.buttons.length; i++) {
        const pressed = pad.buttons[i].pressed;
        const code = "Pad" + i;
        if (pressed && !this.padPrev[i]) {
          this.down.add(code);
          this.justPressed.add(code);
          this.lastDevice = "gamepad";
        } else if (!pressed && this.padPrev[i]) {
          this.down.delete(code);
        }
        this.padPrev[i] = pressed;
      }

      // 右搖桿左右撥動（鎖定時用來切換目標）
      const rawRX = pad.axes[2] ?? 0;
      const flick = rawRX > 0.75 ? 1 : rawRX < -0.75 ? -1 : Math.abs(rawRX) < 0.4 ? 0 : this.padFlick;
      if (flick !== 0 && flick !== this.padFlick) {
        this.justPressed.add(flick > 0 ? "PadRSRight" : "PadRSLeft");
      }
      this.padFlick = flick;
    }

    this.moveX = mx;
    this.moveY = my;
    this.lookX = lx;
    this.lookY = t.invertY ? -ly : ly;

    // ── 動作狀態與緩衝 ──
    for (const action of ACTIONS) {
      let isDown = false;
      let pressed = false;
      for (const code of bindings[action]) {
        if (this.down.has(code)) isDown = true;
        if (this.justPressed.has(code)) pressed = true;
      }
      if (pressed) this.pressedAt.set(action, this.time);
      this.held.set(action, isDown);
    }
    this.justPressed.clear();
  }

  /** 按鍵是否持續按住 */
  isHeld(action: Action): boolean {
    return this.held.get(action) === true;
  }

  /**
   * 取用一次「按下」事件（含輸入緩衝）。
   * 在緩衝時間內按過就回傳 true 並消耗掉，確保一次按鍵只觸發一次。
   */
  consume(action: Action, buffer = tuning.input.bufferTime): boolean {
    const at = this.pressedAt.get(action);
    if (at === undefined || this.time - at > buffer) return false;
    this.pressedAt.delete(action);
    return true;
  }

  /** 丟棄尚未消耗的按下事件 */
  clear(action: Action): void {
    this.pressedAt.delete(action);
  }

  /** 手把震動（第 6 步打擊感會用到） */
  rumble(strong: number, weak: number, durationMs: number): void {
    const pad = this.activePad();
    const actuator = pad?.vibrationActuator;
    if (!actuator) return;
    void actuator
      .playEffect("dual-rumble", { duration: durationMs, strongMagnitude: strong, weakMagnitude: weak })
      .catch(() => {});
  }

  private activePad(): Gamepad | null {
    if (!navigator.getGamepads) return null;
    for (const pad of navigator.getGamepads()) {
      if (pad && pad.connected && pad.mapping === "standard") return pad;
    }
    return null;
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    if (e.code === "Tab" || e.code === "Space") e.preventDefault();
    if (e.repeat) return;
    this.down.add(e.code);
    this.justPressed.add(e.code);
    this.lastDevice = "keyboard";
  };

  private onKeyUp = (e: KeyboardEvent): void => {
    this.down.delete(e.code);
  };

  private onBlur = (): void => {
    this.down.clear();
    this.justPressed.clear();
  };

  private onMouseDown = (e: MouseEvent): void => {
    e.preventDefault();
    this.canvas.focus();
    if (!this.pointerLocked) {
      // 第一次點擊只用來鎖定滑鼠，不當成攻擊
      void Promise.resolve(this.canvas.requestPointerLock()).catch(() => {});
      return;
    }
    const code = "Mouse" + e.button;
    this.down.add(code);
    this.justPressed.add(code);
    this.lastDevice = "keyboard";
  };

  private onMouseUp = (e: MouseEvent): void => {
    this.down.delete("Mouse" + e.button);
  };

  private onMouseMove = (e: MouseEvent): void => {
    if (!this.pointerLocked) return;
    this.mouseDX += e.movementX;
    this.mouseDY += e.movementY;
  };

  private onWheel = (e: WheelEvent): void => {
    e.preventDefault();
    if (e.deltaY !== 0) this.justPressed.add(e.deltaY < 0 ? "WheelUp" : "WheelDown");
  };
}

function radialDeadzone(x: number, y: number, dz: number): [number, number] {
  const len = Math.hypot(x, y);
  if (len < dz) return [0, 0];
  const scaled = Math.min(1, (len - dz) / (1 - dz));
  return [(x / len) * scaled, (y / len) * scaled];
}
