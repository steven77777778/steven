/**
 * 所有可調整的手感參數集中在這裡。
 * 開發時可在瀏覽器 console 直接改：`__game.tuning.player.walkSpeed = 6`
 */
export const tuning = {
  player: {
    capsuleHeight: 1.8, // 公尺
    capsuleRadius: 0.35,
    walkSpeed: 4.6, // m/s
    sprintSpeed: 7.4,
    lockedStrafeSpeed: 4.0, // 鎖定時的移動速度（略慢，強調對峙感）
    acceleration: 38, // m/s²，越大起步越快
    deceleration: 46, // m/s²，越大煞車越快（放開方向鍵時）
    airControl: 0.35, // 空中可控比例 0~1
    turnSpeed: 14, // rad/s，角色轉向移動方向的速度
    lockedTurnSpeed: 18, // rad/s，鎖定時轉向目標的速度
    jumpHeight: 1.35, // 公尺
    gravity: 26, // m/s²（比真實重，跳躍才有俐落感）
    coyoteTime: 0.1, // 秒，離地後仍可起跳的寬限
    dodgeDistance: 3.6, // 公尺
    dodgeDuration: 0.38, // 秒
    dodgeIFrameStart: 0.03, // 秒，無敵開始
    dodgeIFrameEnd: 0.26, // 秒，無敵結束
    dodgeCooldown: 0.12, // 秒，閃避結束到下一次可閃避
    backstepDistance: 2.2, // 無方向輸入時的後撤步距離
  },
  input: {
    mouseSensitivity: 0.0022, // rad / 像素
    padLookSpeedX: 3.2, // rad/s
    padLookSpeedY: 2.0,
    padDeadzone: 0.18,
    invertY: false,
    bufferTime: 0.18, // 秒，輸入緩衝（提早按也會在可行動時觸發）
  },
  camera: {
    distance: 4.6, // 公尺
    lockedDistance: 5.2,
    pivotHeight: 1.55, // 鏡頭注視點高度（相對腳底）
    shoulderOffset: 0.35, // 右肩偏移
    minPitch: -1.0, // rad（往上看）
    maxPitch: 1.25, // rad（往下看）
    defaultPitch: 0.22,
    lockedPitch: 0.26,
    followDamping: 16, // 越大跟隨越緊
    lockYawDamping: 9, // 鎖定時鏡頭追目標的速度
    lockPitchDamping: 6,
    collisionMargin: 0.25, // 與牆面保持的距離
    collisionRecover: 6, // 鏡頭被擠近後拉回的速度
    fov: 0.95, // rad（約 54°）
    minDistance: 0.8,
  },
  lockOn: {
    acquireRange: 22, // 可鎖定距離
    breakRange: 30, // 超過自動解除
    acquireHalfAngle: 1.05, // rad，以鏡頭前方為中心的可鎖定錐角（約 60°）
    angleWeight: 12, // 評分：角度權重（公尺 / rad）
    requireLineOfSight: true,
    losBreakTime: 2.5, // 視線被擋超過幾秒自動解除
  },
};

export type Tuning = typeof tuning;
