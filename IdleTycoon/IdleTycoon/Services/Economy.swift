import Foundation

enum Economy {
    static func incomePerSecond(save: GameSave) -> Double {
        let raw = save.businesses.reduce(0) { $0 + $1.incomePerSecond }
        return raw * save.globalMultiplier
    }

    static func tapValue(save: GameSave) -> Double {
        GameBalance.tapBase * save.globalMultiplier
    }

    static func applyPassive(save: inout GameSave, delta: TimeInterval, efficiency: Double = 1) {
        guard delta > 0 else { return }
        let earned = incomePerSecond(save: save) * delta * efficiency
        save.coins += earned
        save.lifetimeCoins += earned
    }

    /// Settle time away from the app (capped + discounted).
    @discardableResult
    static func collectOfflineEarnings(save: inout GameSave, now: Date = .now) -> Double {
        let elapsed = now.timeIntervalSince(save.lastTick)
        let capped = min(max(0, elapsed), GameBalance.maxOfflineSeconds)
        let before = save.coins
        applyPassive(save: &save, delta: capped, efficiency: GameBalance.offlineEfficiency)
        save.lastTick = now
        return save.coins - before
    }

    static func canAfford(_ cost: Double, save: GameSave) -> Bool {
        save.coins + 1e-9 >= cost
    }

    @discardableResult
    static func buyBusiness(id: String, count: Int = 1, save: inout GameSave) -> Bool {
        guard count > 0,
              let index = save.businesses.firstIndex(where: { $0.id == id })
        else { return false }

        let cost = save.businesses[index].costToBuy(count: count)
        guard canAfford(cost, save: save) else { return false }

        save.coins -= cost
        save.businesses[index].buy(count: count)
        return true
    }

    static func multiplierUpgradeCost(save: GameSave) -> Double {
        let steps = max(0, (save.globalMultiplier - 1) / GameBalance.multiplierUpgradeStep)
        return GameBalance.multiplierUpgradeBaseCost
            * pow(GameBalance.multiplierUpgradeGrowth, steps)
    }

    @discardableResult
    static func buyMultiplier(save: inout GameSave) -> Bool {
        let cost = multiplierUpgradeCost(save: save)
        guard canAfford(cost, save: save) else { return false }
        save.coins -= cost
        save.globalMultiplier += GameBalance.multiplierUpgradeStep
        return true
    }

    static func tap(save: inout GameSave) {
        let value = tapValue(save: save)
        save.coins += value
        save.lifetimeCoins += value
        save.totalTaps += 1
    }
}

enum CurrencyFormat {
    private static let suffixes = ["", "K", "M", "B", "T", "Qa", "Qi", "Sx"]

    static func coins(_ value: Double) -> String {
        let sign = value < 0 ? "-" : ""
        var n = abs(value)
        var idx = 0
        while n >= 1000 && idx < suffixes.count - 1 {
            n /= 1000
            idx += 1
        }
        if idx == 0 {
            if n >= 100 { return "\(sign)\(Int(n.rounded()))" }
            if n >= 10 { return String(format: "%@%.1f", sign, n) }
            return String(format: "%@%.2f", sign, n)
        }
        return String(format: "%@%.2f%@", sign, n, suffixes[idx])
    }

    static func rate(_ value: Double) -> String {
        "\(coins(value))/s"
    }
}
