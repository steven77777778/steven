import ActivityKit
import SwiftUI

struct ContentView: View {
    @State private var up = false
    @State private var blink = false
    @State private var waveFrame = 0          // 0 = 沒在招手，1...3 = 招手的三個姿勢
    @State private var waveTask: Task<Void, Never>?
    @State private var position = CGSize.zero
    @State private var dragStart = CGSize.zero
    @State private var islandOn = false
    @State private var message = "點一下火星人，他會向你招手"

    private let bobTimer = Timer.publish(every: 0.65, on: .main, in: .common).autoconnect()
    private let blinkTimer = Timer.publish(every: 3.4, on: .main, in: .common).autoconnect()

    private var frameName: String {
        if waveFrame > 0 { return "pet-wave\(waveFrame)" }
        return blink ? "pet-blink" : "pet-idle"
    }

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            Image(frameName)
                .resizable()
                .interpolation(.none)
                .scaledToFit()
                .frame(height: 420)
                .offset(x: position.width, y: position.height + (up ? -4 : 0))
                .onTapGesture { wave() }
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
                Text("版本 6")
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
        .onReceive(bobTimer) { _ in up.toggle() }
        .onReceive(blinkTimer) { _ in
            blink = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.16) { blink = false }
        }
        .onAppear { islandOn = !Activity<PetActivityAttributes>.activities.isEmpty }
    }

    /// 招手約兩秒
    private func wave() {
        waveTask?.cancel()
        waveTask = Task { @MainActor in
            for i in 0..<13 {
                waveFrame = i % 3 + 1
                try? await Task.sleep(nanoseconds: 170_000_000)
                if Task.isCancelled { return }
            }
            waveFrame = 0
        }
    }

    private func startIsland() {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            message = "請到「設定 → 火星人」打開「即時動態」"
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
            message = "點一下火星人，他會向你招手"
        }
    }
}
