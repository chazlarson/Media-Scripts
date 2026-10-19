import SwiftUI

struct BusinessRowView: View {
    let business: Business
    let coins: Double
    let multiplier: Double
    let onBuy: () -> Void

    private var cost: Double { business.costToBuy() }
    private var affordable: Bool { coins + 1e-9 >= cost }
    private var rate: Double { business.incomePerSecond * multiplier }

    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text(business.name)
                    .font(.system(.headline, design: .rounded).weight(.bold))
                    .foregroundStyle(TycoonTheme.foam)
                Text(business.blurb)
                    .font(.system(.caption, design: .rounded))
                    .foregroundStyle(TycoonTheme.foam.opacity(0.7))
                    .lineLimit(2)
                Text("Owned \(business.owned) · \(CurrencyFormat.rate(rate))")
                    .font(.system(.caption2, design: .rounded).monospacedDigit())
                    .foregroundStyle(TycoonTheme.moss)
            }

            Spacer(minLength: 8)

            Button(action: onBuy) {
                VStack(spacing: 2) {
                    Text("Buy")
                        .font(.system(.caption, design: .rounded).weight(.bold))
                    Text(CurrencyFormat.coins(cost))
                        .font(.system(.caption2, design: .rounded).monospacedDigit())
                }
                .foregroundStyle(affordable ? TycoonTheme.ink : TycoonTheme.foam.opacity(0.45))
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(affordable ? TycoonTheme.citrus : TycoonTheme.foam.opacity(0.08))
                )
            }
            .buttonStyle(.plain)
            .disabled(!affordable)
            .accessibilityLabel("Buy \(business.name) for \(CurrencyFormat.coins(cost))")
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(TycoonTheme.foam.opacity(0.06))
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(TycoonTheme.foam.opacity(0.08), lineWidth: 1)
                )
        )
    }
}
