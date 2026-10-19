import Foundation

/// Disk-friendly snapshot of progress. No accounts, no ads, no cloud.
struct GameSave: Codable, Equatable, Sendable {
    var coins: Double
    var lifetimeCoins: Double
    var globalMultiplier: Double
    var businesses: [Business]
    var lastTick: Date
    var totalTaps: Int

    static func fresh() -> GameSave {
        GameSave(
            coins: 0,
            lifetimeCoins: 0,
            globalMultiplier: 1,
            businesses: BusinessCatalog.starterBusinesses(),
            lastTick: .now,
            totalTaps: 0
        )
    }
}

enum GameBalance {
    /// Manual tap income before multipliers.
    static let tapBase: Double = 1
    /// Cap how long offline earnings accrue (8 hours).
    static let maxOfflineSeconds: TimeInterval = 8 * 60 * 60
    /// Offline pays a fraction of online rate (keeps returning rewarding but not broken).
    static let offlineEfficiency: Double = 0.5
    /// Soft prestige-style multiplier bump cost (very light for a starter).
    static let multiplierUpgradeBaseCost: Double = 50_000
    static let multiplierUpgradeGrowth: Double = 2.5
    static let multiplierUpgradeStep: Double = 0.25
}
