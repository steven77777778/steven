import ActivityKit
import SwiftUI

/// 點一下會輪流播放的動作（圖片名稱是 pet-<動作>-<第幾格>，每個動作 8 格）
let petActions: [(name: String, frameMs: UInt64, loops: Int)] = [
    ("wave", 110, 2), ("dance", 130, 2), ("walk", 100, 3), ("jump", 100, 2)
]

struct ContentView: View {
    @State private var idleFrame = 0
    @State private var actionFrame: String?   // 正在做動作時的圖片名稱，沒在動作時是 nil
    @State private var nextAction = 0         // 下一次點擊要播哪個動作
    @State private var actionTask: Task<Void, Never>?
    @State private var position = CGSize.zero
    @State private var dragStart = CGSize.zero
    @State private var islandOn = false
    @State private var message = "點一下火星人，每次會做一個不同的動作"

    private let idleTimer = Timer.publish(every: 0.14, on: .main, in: .common).autoconnect()

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            Image(actionFrame ?? "pet-idle-\(idleFrame)")
                .resizable()
                .interpolation(.none)
                .scaledToFit()
                .frame(height: 460)
                .offset(x: position.width, y: position.height)
                .onTapGesture { playNextAction() }
                .gesture(
                    DragGesture(minimumDistance: 10)
                        .onChanged { g in
                            position = CGSize(width: dragStart.width + g.translation.width,
                                              height: dragStart.height + g.translation.height)
                        }
                        .onEnded { _ in dragStart = position }
                )

            VStack(spacing: 12) {
                Spacer()
                Text("版本 10")
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.4))
                Text(message)
                    .font(.footnote)
                    .foregroundStyle(.white.opacity(0.8))
                    .multilineTextAlignment(.center)
                Button(islandOn ? "收回靈動島" : "放到靈動島") {
                    islandOn ? stopIsland() : startIsland()
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
            }
            .padding()
        }
        .onReceive(idleTimer) { _ in idleFrame = (idleFrame + 1) % 8 }
        .onAppear { islandOn = !Activity<PetActivityAttributes>.activities.isEmpty }
    }

    /// 播放下一個動作，播完回到待機
    private func playNextAction() {
        let action = petActions[nextAction % petActions.count]
        nextAction += 1
        actionTask?.cancel()
        actionTask = Task { @MainActor in
            for i in 0..<(8 * action.loops) {
                actionFrame = "pet-\(action.name)-\(i % 8)"
                try? await Task.sleep(nanoseconds: action.frameMs * 1_000_000)
                if Task.isCancelled { return }
            }
            actionFrame = nil
        }
    }

    private func startIsland() {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            message = "請到「設定」裡這個 app 的頁面打開「即時動態」"
            return
        }
        do {
            _ = try Activity<PetActivityAttributes>.request(
                attributes: PetActivityAttributes(),
                content: ActivityContent(state: .init(waving: false), staleDate: nil),
                pushType: nil
            )
            islandOn = true
            message = "回到主畫面，火星人就在靈動島上；長按靈動島可以叫他招手"
        } catch {
            message = "放到靈動島失敗：\(error.localizedDescription)"
        }
    }

    private func stopIsland() {
        Task { @MainActor in
            for activity in Activity<PetActivityAttributes>.activities {
                await activity.end(nil, dismissalPolicy: .immediate)
            }
            islandOn = false
            message = "點一下火星人，每次會做一個不同的動作"
        }
    }
}
