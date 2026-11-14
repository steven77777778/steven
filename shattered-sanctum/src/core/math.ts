const TAU = Math.PI * 2;

/** 把角度包到 (-π, π] */
export function wrapAngle(a: number): number {
  a = (a + Math.PI) % TAU;
  if (a < 0) a += TAU;
  return a - Math.PI;
}

/** 與幀率無關的指數平滑係數 */
export function dampFactor(lambda: number, dt: number): number {
  return 1 - Math.exp(-lambda * dt);
}

export function damp(current: number, target: number, lambda: number, dt: number): number {
  return current + (target - current) * dampFactor(lambda, dt);
}

export function dampAngle(current: number, target: number, lambda: number, dt: number): number {
  return current + wrapAngle(target - current) * dampFactor(lambda, dt);
}

/** 以固定角速度轉向目標角度 */
export function rotateTowards(current: number, target: number, maxStep: number): number {
  const d = wrapAngle(target - current);
  if (Math.abs(d) <= maxStep) return target;
  return current + Math.sign(d) * maxStep;
}

export function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

export function moveTowards(current: number, target: number, maxStep: number): number {
  const d = target - current;
  if (Math.abs(d) <= maxStep) return target;
  return current + Math.sign(d) * maxStep;
}
