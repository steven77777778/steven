import SwiftUI

/// iPhone 17 / iOS 26「液態玻璃（Liquid Glass）」自適應封裝 + 擬真厚強化玻璃碎裂折射塗層
extension View {
    @ViewBuilder
    func marsLiquidGlassCapsule(tint: Color? = nil, interactive: Bool = false) -> some View {
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            if let tint {
                self.glassEffect(
                    interactive ? .regular.tint(tint).interactive() : .regular.tint(tint),
                    in: .capsule
                )
            } else {
                self.glassEffect(
                    interactive ? .regular.interactive() : .regular,
                    in: .capsule
                )
            }
        } else {
            legacyGlassCapsule(tint: tint)
        }
        #else
        legacyGlassCapsule(tint: tint)
        #endif
    }

    @ViewBuilder
    func marsLiquidGlassCard(cornerRadius: CGFloat = 24, tint: Color? = nil) -> some View {
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            if let tint {
                self.glassEffect(.regular.tint(tint), in: .rect(cornerRadius: cornerRadius))
            } else {
                self.glassEffect(.regular, in: .rect(cornerRadius: cornerRadius))
            }
        } else {
            legacyGlassCard(cornerRadius: cornerRadius, tint: tint)
        }
        #else
        legacyGlassCard(cornerRadius: cornerRadius, tint: tint)
        #endif
    }

    private func legacyGlassCapsule(tint: Color?) -> some View {
        self.background(
            ZStack {
                Capsule().fill(.ultraThinMaterial)
                if let tint {
                    Capsule().fill(tint.opacity(0.18))
                }
                Capsule()
                    .strokeBorder(
                        LinearGradient(
                            colors: [.white.opacity(0.55), .white.opacity(0.12), .white.opacity(0.30)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 0.9
                    )
            }
        )
    }

    private func legacyGlassCard(cornerRadius: CGFloat, tint: Color?) -> some View {
        let shape = RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
        return self.background(
            ZStack {
                shape.fill(.ultraThinMaterial)
                if let tint {
                    shape.fill(tint.opacity(0.14))
                }
                shape.strokeBorder(
                    LinearGradient(
                        colors: [.white.opacity(0.52), .white.opacity(0.08), .white.opacity(0.26)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1.0
                )
            }
        )
    }
}

// MARK: - 擬真厚強化玻璃／液態玻璃受擊碎裂塗層（非對稱分岔應力裂紋＋白霧粉碎撞擊坑＋玻璃厚度全反射切面）
struct ShatteredLiquidGlassOverlay: View {
    var impactOrigin: UnitPoint = UnitPoint(x: 0.72, y: 0.45)
    var intenseFlash: Bool = false

    private struct CrackSegment {
        let p0: CGPoint
        let p1: CGPoint
        let width: CGFloat
        let alpha: Double
    }

    var body: some View {
        Canvas { context, size in
            let cx = size.width * impactOrigin.x
            let cy = size.height * impactOrigin.y
            let reach = hypot(size.width, size.height)

            // 1. 撞擊瞬間的玻璃內部應力閃光
            if intenseFlash {
                let r = reach * 0.42
                context.fill(
                    Path(ellipseIn: CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)),
                    with: .radialGradient(
                        Gradient(colors: [.white.opacity(0.52), Color(red: 0.82, green: 0.95, blue: 1.0).opacity(0.18), .clear]),
                        center: CGPoint(x: cx, y: cy),
                        startRadius: 1,
                        endRadius: r
                    )
                )
            }

            // 2. 非對稱真實玻璃應力主裂紋（不規則角度、折角與粗細漸縮，徹底告別假蜘蛛網！）
            // (起始角度, 每段推進比例與角度微折偏移)
            let primarySpecs: [(Double, [(Double, Double)])] = [
                (-2.94, [(0.06,  0.08), (0.14, -0.14), (0.29,  0.11), (0.52, -0.07), (0.86,  0.05)]),
                (-2.38, [(0.05, -0.11), (0.13,  0.16), (0.26, -0.09), (0.48,  0.14), (0.78, -0.06)]),
                (-1.86, [(0.07,  0.12), (0.17, -0.08), (0.35,  0.15), (0.64, -0.10)]),
                (-1.32, [(0.05, -0.09), (0.15,  0.13), (0.31, -0.16), (0.55,  0.08)]),
                (-0.62, [(0.06,  0.14), (0.16, -0.11), (0.34,  0.09), (0.68, -0.12)]),
                ( 0.08, [(0.05, -0.12), (0.14,  0.09), (0.30, -0.14), (0.58,  0.07)]),
                ( 0.72, [(0.06,  0.09), (0.18, -0.15), (0.38,  0.12), (0.74, -0.08)]),
                ( 1.38, [(0.05, -0.13), (0.14,  0.11), (0.28, -0.08), (0.56,  0.13)]),
                ( 2.04, [(0.07,  0.10), (0.19, -0.14), (0.41,  0.09), (0.84, -0.11)]),
                ( 2.58, [(0.06, -0.08), (0.16,  0.15), (0.36, -0.12), (0.76,  0.09), (1.02, -0.05)]),
            ]

            var segments: [CrackSegment] = []
            var chainNodes: [[CGPoint]] = []

            for (idx, (baseAng, steps)) in primarySpecs.enumerated() {
                var prev = CGPoint(x: cx, y: cy)
                var nodes: [CGPoint] = [prev]
                var curAng = baseAng

                for (sIdx, (distFrac, bend)) in steps.enumerated() {
                    curAng += bend
                    let r = reach * distFrac
                    let next = CGPoint(x: cx + cos(curAng) * r, y: cy + sin(curAng) * r)
                    let progress = Double(sIdx) / Double(max(1, steps.count))
                    let w = CGFloat(2.15 * (1.0 - progress * 0.72))
                    let al = 0.96 - progress * 0.34
                    segments.append(CrackSegment(p0: prev, p1: next, width: w, alpha: al))
                    nodes.append(next)

                    // 真實樹枝狀次級分岔細裂紋 (18°~34° 銳角分岔，迅速收細成髮絲紋)
                    if sIdx == 1 || sIdx == 2 || (sIdx == 3 && idx % 2 == 0) {
                        let sign = ((idx + sIdx) % 2 == 0) ? 1.0 : -1.0
                        let fAng1 = curAng + sign * (0.34 + Double(sIdx) * 0.06)
                        let fMid = CGPoint(
                            x: next.x + cos(fAng1) * (reach * 0.09),
                            y: next.y + sin(fAng1) * (reach * 0.09)
                        )
                        let fTip = CGPoint(
                            x: fMid.x + cos(fAng1 - sign * 0.14) * (reach * 0.10),
                            y: fMid.y + sin(fAng1 - sign * 0.14) * (reach * 0.10)
                        )
                        segments.append(CrackSegment(p0: next, p1: fMid, width: w * 0.56, alpha: al * 0.78))
                        segments.append(CrackSegment(p0: fMid, p1: fTip, width: 0.42, alpha: al * 0.52))
                    }
                    prev = next
                }
                chainNodes.append(nodes)
            }

            // 3. 傾斜玻璃碎塊切面（不同角度全反射高光與冷調陰影，營造玻璃翹起錯位立體感）
            for i in 0..<chainNodes.count {
                let j = (i + 1) % chainNodes.count
                if chainNodes[i].count > 3 && chainNodes[j].count > 3 {
                    let a1 = chainNodes[i][1], a2 = chainNodes[i][2]
                    let b1 = chainNodes[j][1], b2 = chainNodes[j][2]

                    // 不規則橫向應力橋接裂紋（錯開半徑，不連成對稱圓環！）
                    if i % 3 != 1 {
                        let bridgeTarget = (i % 2 == 0) ? b2 : b1
                        segments.append(CrackSegment(p0: a1, p1: bridgeTarget, width: 0.85, alpha: 0.68))
                    }

                    var shard = Path()
                    shard.move(to: a1)
                    shard.addLine(to: a2)
                    shard.addLine(to: b2)
                    shard.addLine(to: b1)
                    shard.closeSubpath()

                    if i % 3 == 0 {
                        context.fill(
                            shard,
                            with: .linearGradient(
                                Gradient(colors: [.white.opacity(0.20), Color(red: 0.75, green: 0.94, blue: 1.0).opacity(0.04)]),
                                startPoint: a1,
                                endPoint: b2
                            )
                        )
                    } else if i % 3 == 1 {
                        context.fill(shard, with: .color(.black.opacity(0.09)))
                    }
                }
            }

            // 4. 繪製 3mm 玻璃厚度切面（內部全反射銀藍邊 + 底層暗溝槽 + 刀鋒白霧裂紋）
            for seg in segments {
                var p = Path()
                p.move(to: seg.p0)
                p.addLine(to: seg.p1)

                // 玻璃底層暗部折射陰影
                var shCtx = context
                shCtx.translateBy(x: 0.8, y: 1.3)
                shCtx.stroke(p, with: .color(.black.opacity(seg.alpha * 0.42)), lineWidth: seg.width + 0.6)

                // 玻璃斷面厚度全反射冷白銀邊（僅粗主裂紋明顯）
                if seg.width > 0.9 {
                    var bevCtx = context
                    bevCtx.translateBy(x: -1.1, y: -0.8)
                    bevCtx.stroke(
                        p,
                        with: .color(Color(red: 0.72, green: 0.94, blue: 1.0).opacity(seg.alpha * 0.55)),
                        lineWidth: seg.width * 1.35
                    )
                }

                // 銳利表面破裂白線
                context.stroke(
                    p,
                    with: .color(.white.opacity(seg.alpha)),
                    style: StrokeStyle(lineWidth: seg.width, lineCap: .round)
                )
            }

            // 5. 撞擊中心「粉碎白霧玻璃坑（Pulverized Impact Crater）」：密集微碎晶格與霧化白斑
            let craterR = max(7.0, reach * 0.048)
            context.fill(
                Path(ellipseIn: CGRect(x: cx - craterR * 1.5, y: cy - craterR * 1.5, width: craterR * 3.0, height: craterR * 3.0)),
                with: .radialGradient(
                    Gradient(colors: [.white.opacity(0.78), Color(red: 0.86, green: 0.95, blue: 1.0).opacity(0.32), .clear]),
                    center: CGPoint(x: cx, y: cy),
                    startRadius: 0.5,
                    endRadius: craterR * 1.5
                )
            )
            // 撞擊坑內微細碎晶網
            for k in 0..<7 {
                let a = Double(k) * 0.92 + 0.2
                let r1 = craterR * (0.45 + Double(k % 3) * 0.28)
                let pA = CGPoint(x: cx + cos(a) * r1, y: cy + sin(a) * r1)
                let pB = CGPoint(x: cx + cos(a + 1.1) * (r1 * 0.85), y: cy + sin(a + 1.1) * (r1 * 0.85))
                var cr = Path()
                cr.move(to: CGPoint(x: cx, y: cy))
                cr.addLine(to: pA)
                cr.addLine(to: pB)
                cr.closeSubpath()
                context.fill(cr, with: .color(.white.opacity(k % 2 == 0 ? 0.45 : 0.22)))
                context.stroke(cr, with: .color(.white.opacity(0.92)), lineWidth: 0.75)
            }
        }
        .allowsHitTesting(false)
    }
}
