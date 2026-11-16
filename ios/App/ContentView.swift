import ActivityKit
import SwiftUI
import WidgetKit

private struct AppPetAction: Identifiable {
    let id: String
    let label: String
    let subtitle: String
    let refNote: String
    let frameMs: UInt64
    let loops: Int
}

private let appActions: [AppPetAction] = [
    .init(id: "bat",      label: "球棒擊破 💥", subtitle: "火星人 — 開場雙手揮棒擊碎紅墨",        refNote: "對應截圖 #01-#04, #57-#59", frameMs: 110, loops: 2),
    .init(id: "wave",     label: "揮手 👋",     subtitle: "やあ",                                  refNote: "右手舉起來左右揮",          frameMs: 120, loops: 2),
    .init(id: "wavejoy",  label: "開心揮手 😊", subtitle: "やあ！",                                refNote: "揮手，眼睛瞇成弧形",        frameMs: 120, loops: 2),
]

struct ContentView: View {
    @State private var idleFrame = 0
    @State private var lookRight = false      // 待機時眼睛看哪邊，每 10 秒換一次
    @State private var activeSprite: String?
    @State private var activeLabel = "今日も火星が見える"
    @State private var activeRefNote = "待機呼吸中 (#64/#80) · 版本 21"
    @State private var activeActionId = "idle"
    @State private var nextIdx = 0
    @State private var actionTask: Task<Void, Never>?
    @State private var position = CGSize.zero
    @State private var dragStart = CGSize.zero
    @State private var islandOn = false
    @State private var glassCrackedOrigin: UnitPoint?
    @State private var glassFlash = false
    @State private var shakeX: CGFloat = 0
    @State private var statusHint = "點火星人或下方按鈕播放動作 · 球棒會敲碎玻璃"

    private let idleTimer = Timer.publish(every: 0.16, on: .main, in: .common).autoconnect()
    private let marsRed = Color(red: 0.85, green: 0.26, blue: 0.29)

    var body: some View {
        ZStack {
            // MV 火星暮光深邃漸層背景
            LinearGradient(
                colors: [
                    Color(red: 0.06, green: 0.07, blue: 0.13),
                    Color(red: 0.14, green: 0.10, blue: 0.18),
                    Color(red: 0.22, green: 0.11, blue: 0.16)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            // 頂部液態玻璃狀態與截圖編號膠囊
            VStack(spacing: 6) {
                HStack(spacing: 8) {
                    Circle()
                        .fill(activeSprite == nil ? marsRed : Color.yellow)
                        .frame(width: 8, height: 8)
                    Text(activeLabel)
                        .font(.system(size: 14, weight: .semibold, design: .rounded))
                        .foregroundStyle(.white)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 9)
                .marsLiquidGlassCapsule(tint: activeSprite == nil ? nil : marsRed)

                Text(activeRefNote)
                    .font(.system(size: 11, weight: .medium, design: .rounded))
                    .foregroundStyle(.white.opacity(0.62))

                Spacer()
            }
            .padding(.top, 12)

            // 中央火星人本體（乾淨純色像素 + 銳利無鋸齒縮放 + 液態玻璃觀測窗碎裂特效）
            ZStack {
                RoundedRectangle(cornerRadius: 36, style: .continuous)
                    .fill(.clear)
                    .frame(width: 318, height: 396)
                    .marsLiquidGlassCard(cornerRadius: 36)

                Ellipse()
                    .fill(.black.opacity(0.35))
                    .frame(width: 140, height: 20)
                    .blur(radius: 5)
                    .offset(y: 162)

                bmp(activeSprite ?? "pet-idle\(lookRight ? "R" : "L")-\(idleFrame)")
                    .resizable()
                    .interpolation(.none)
                    .scaledToFit()
                    .frame(height: 346)

                if let origin = glassCrackedOrigin {
                    ShatteredLiquidGlassOverlay(impactOrigin: origin, intenseFlash: glassFlash)
                        .frame(width: 318, height: 396)
                        .clipShape(RoundedRectangle(cornerRadius: 36, style: .continuous))
                        .transition(.opacity)
                }
            }
            .offset(x: position.width + shakeX, y: position.height - 20)
            .onTapGesture {
                let act = appActions[nextIdx % appActions.count]
                nextIdx += 1
                play(act)
            }
            .gesture(
                DragGesture(minimumDistance: 8)
                    .onChanged { g in
                        position = CGSize(
                            width: dragStart.width + g.translation.width,
                            height: dragStart.height + g.translation.height
                        )
                    }
                    .onEnded { _ in
                        withAnimation(.spring(response: 0.45, dampingFraction: 0.72)) {
                            position = .zero
                            dragStart = .zero
                        }
                    }
            )

            // 底部 iPhone 17 液態玻璃控制台
            VStack(spacing: 12) {
                Spacer()

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(appActions) { act in
                            let selected = activeActionId == act.id
                            Button {
                                play(act)
                            } label: {
                                Text(act.label)
                                    .font(.system(size: 13, weight: .semibold, design: .rounded))
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 9)
                                    .marsLiquidGlassCapsule(
                                        tint: selected ? marsRed : nil,
                                        interactive: true
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, 18)
                }

                HStack(spacing: 10) {
                    Button {
                        islandOn ? stopIsland() : startIsland()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: islandOn ? "sparkles" : "capsule.portrait")
                            Text(islandOn ? "收回靈動島" : "放到 iPhone 17 靈動島")
                                .font(.system(size: 13, weight: .semibold, design: .rounded))
                        }
                        .foregroundStyle(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .marsLiquidGlassCapsule(tint: marsRed, interactive: true)
                    }
                    .buttonStyle(.plain)

                    Button {
                        WidgetCenter.shared.reloadAllTimelines()
                        statusHint = "已同步刷新桌面小工具！回主畫面看看火星人吧 ✦"
                    } label: {
                        HStack(spacing: 5) {
                            Image(systemName: "arrow.clockwise")
                            Text("刷新小工具")
                                .font(.system(size: 13, weight: .medium, design: .rounded))
                        }
                        .foregroundStyle(.white.opacity(0.9))
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .marsLiquidGlassCapsule(interactive: true)
                    }
                    .buttonStyle(.plain)
                }

                Text(statusHint)
                    .font(.system(size: 11, weight: .regular, design: .rounded))
                    .foregroundStyle(.white.opacity(0.58))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)
                    .padding(.bottom, 6)
            }
        }
        .onReceive(idleTimer) { _ in
            idleFrame = (idleFrame + 1) % 8
            lookRight = Int(Date().timeIntervalSince1970 / 10) % 2 == 1
        }
        .onAppear {
            islandOn = !Activity<PetActivityAttributes>.activities.isEmpty
        }
    }

    private func play(_ action: AppPetAction) {
        actionTask?.cancel()
        activeActionId = action.id
        activeLabel = action.subtitle
        activeRefNote = action.refNote
        if action.id != "bat" {
            glassCrackedOrigin = nil
            glassFlash = false
        }
        actionTask = Task { @MainActor in
            let breaksGlass = action.id == "bat"
            for i in 0..<(8 * action.loops) {
                let frame = i % 8
                activeSprite = "pet-\(action.id)-\(frame)"
                if breaksGlass && frame == 3 {
                    glassCrackedOrigin = UnitPoint(x: 0.18, y: 0.63)   // 球棒往左下砸的落點
                    glassFlash = true
                    withAnimation(.interactiveSpring(response: 0.08, dampingFraction: 0.25)) {
                        shakeX = (i % 2 == 0 ? 7 : -7)
                    }
                    try? await Task.sleep(nanoseconds: 55_000_000)
                    withAnimation(.spring(response: 0.22, dampingFraction: 0.55)) {
                        shakeX = 0
                    }
                    try? await Task.sleep(nanoseconds: max(10_000_000, action.frameMs * 1_000_000 - 55_000_000))
                    glassFlash = false
                } else {
                    try? await Task.sleep(nanoseconds: action.frameMs * 1_000_000)
                }
                if Task.isCancelled { return }
            }
            activeSprite = nil
            activeActionId = "idle"
            if breaksGlass {
                activeLabel = "……液態玻璃被砸裂了 💥（死魚眼裝沒事）"
                activeRefNote = "液態玻璃表面張力自癒復原中 💧"
                try? await Task.sleep(nanoseconds: 2_600_000_000)
                if Task.isCancelled { return }
                withAnimation(.easeOut(duration: 0.65)) {
                    glassCrackedOrigin = nil
                }
            }
            activeLabel = "今日も火星が見える"
            activeRefNote = "待機呼吸中 (#64/#80) · 版本 21"
        }
    }

    private func startIsland() {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            statusHint = "請到 iOS「設定 → 火星人」開啟「即時動態」權限"
            return
        }
        do {
            _ = try Activity<PetActivityAttributes>.request(
                attributes: PetActivityAttributes(),
                content: ActivityContent(state: .init(waving: false), staleDate: nil),
                pushType: nil
            )
            islandOn = true
            statusHint = "已登上靈動島！回到主畫面長按靈動島可以叫他動一下"
        } catch {
            statusHint = "啟動靈動島失敗：\(error.localizedDescription)"
        }
    }

    private func stopIsland() {
        Task { @MainActor in
            for activity in Activity<PetActivityAttributes>.activities {
                await activity.end(nil, dismissalPolicy: .immediate)
            }
            islandOn = false
            statusHint = "點火星人或下方按鈕播放動作"
        }
    }
}
