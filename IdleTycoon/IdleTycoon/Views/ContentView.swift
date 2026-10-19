import SwiftUI

struct ContentView: View {
    @State private var game = GameViewModel()
    @State private var pulse = false

    var body: some View {
        ZStack {
            TycoonTheme.background.ignoresSafeArea()

            ScrollView {
                VStack(spacing: 20) {
                    header
                    if let banner = game.offlineBanner {
                        offlineCard(banner)
                    }
                    tapStage
                    multiplierRow
                    businessList
                    footer
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Corner Empire")
                .font(.system(size: 34, weight: .heavy, design: .rounded))
                .foregroundStyle(TycoonTheme.citrus)
            Text("A private idle tycoon — no ads, no store, just lemonade math.")
                .font(.system(.subheadline, design: .rounded))
                .foregroundStyle(TycoonTheme.foam.opacity(0.75))

            HStack(alignment: .firstTextBaseline, spacing: 12) {
                Text(CurrencyFormat.coins(game.save.coins))
                    .font(.system(size: 40, weight: .bold, design: .rounded).monospacedDigit())
                    .foregroundStyle(TycoonTheme.foam)
                    .contentTransition(.numericText())
                Text(CurrencyFormat.rate(game.incomePerSecond))
                    .font(.system(.headline, design: .rounded).monospacedDigit())
                    .foregroundStyle(TycoonTheme.moss)
            }
            .padding(.top, 4)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var tapStage: some View {
        Button(action: {
            game.tapStand()
            withAnimation(.spring(response: 0.28, dampingFraction: 0.55)) {
                pulse.toggle()
            }
        }) {
            ZStack {
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [TycoonTheme.citrus, TycoonTheme.pulp.opacity(0.85)],
                            center: .center,
                            startRadius: 10,
                            endRadius: 120
                        )
                    )
                    .frame(width: 180, height: 180)
                    .scaleEffect(pulse ? 1.04 : 1.0)
                    .shadow(color: TycoonTheme.citrus.opacity(0.35), radius: 24, y: 8)

                VStack(spacing: 6) {
                    Text("Squeeze")
                        .font(.system(.title2, design: .rounded).weight(.bold))
                    Text("+\(CurrencyFormat.coins(game.tapValue))")
                        .font(.system(.subheadline, design: .rounded).monospacedDigit())
                }
                .foregroundStyle(TycoonTheme.ink)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Squeeze for coins")
    }

    private var multiplierRow: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Global squeeze ×\(String(format: "%.2f", game.save.globalMultiplier))")
                    .font(.system(.subheadline, design: .rounded).weight(.semibold))
                    .foregroundStyle(TycoonTheme.foam)
                Text("Boosts taps and every business.")
                    .font(.system(.caption2, design: .rounded))
                    .foregroundStyle(TycoonTheme.foam.opacity(0.65))
            }
            Spacer()
            Button("Upgrade \(CurrencyFormat.coins(game.multiplierCost))") {
                game.buyMultiplier()
            }
            .font(.system(.caption, design: .rounded).weight(.bold))
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(
                Capsule()
                    .fill(
                        game.save.coins >= game.multiplierCost
                            ? TycoonTheme.moss
                            : TycoonTheme.foam.opacity(0.12)
                    )
            )
            .foregroundStyle(
                game.save.coins >= game.multiplierCost
                    ? TycoonTheme.ink
                    : TycoonTheme.foam.opacity(0.45)
            )
            .disabled(game.save.coins < game.multiplierCost)
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(TycoonTheme.foam.opacity(0.05))
        )
    }

    private var businessList: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Businesses")
                .font(.system(.title3, design: .rounded).weight(.bold))
                .foregroundStyle(TycoonTheme.foam)

            ForEach(game.save.businesses) { business in
                BusinessRowView(
                    business: business,
                    coins: game.save.coins,
                    multiplier: game.save.globalMultiplier
                ) {
                    game.buy(business.id)
                }
            }
        }
    }

    private var footer: some View {
        VStack(spacing: 8) {
            if let saved = game.lastSavedAt {
                Text("Saved \(saved.formatted(date: .omitted, time: .standard))")
                    .font(.system(.caption2, design: .rounded))
                    .foregroundStyle(TycoonTheme.foam.opacity(0.45))
            }
            Button("Reset private save", role: .destructive) {
                game.resetProgress()
            }
            .font(.system(.caption, design: .rounded))
            .foregroundStyle(TycoonTheme.pulp)
            .padding(.bottom, 24)
        }
        .frame(maxWidth: .infinity)
    }

    private func offlineCard(_ text: String) -> some View {
        HStack {
            Text(text)
                .font(.system(.subheadline, design: .rounded).weight(.medium))
                .foregroundStyle(TycoonTheme.ink)
            Spacer()
            Button("OK") { game.dismissOfflineBanner() }
                .font(.system(.caption, design: .rounded).weight(.bold))
                .foregroundStyle(TycoonTheme.ink)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(TycoonTheme.citrus)
        )
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}

#Preview {
    ContentView()
}
