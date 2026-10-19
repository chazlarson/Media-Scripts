import Foundation

/// A purchasable generator that produces currency over time.
struct Business: Identifiable, Codable, Hashable, Sendable {
    let id: String
    let name: String
    let blurb: String
    let baseCost: Double
    let baseIncomePerSecond: Double
    /// Multiplier applied to cost after each purchase (classic idle curve).
    let costGrowth: Double
    var owned: Int

    func costToBuy(count: Int = 1) -> Double {
        guard count > 0 else { return 0 }
        // Sum of geometric series: base * r^owned * (r^n - 1) / (r - 1)
        let r = costGrowth
        let start = pow(r, Double(owned))
        if abs(r - 1) < 1e-12 {
            return baseCost * start * Double(count)
        }
        return baseCost * start * (pow(r, Double(count)) - 1) / (r - 1)
    }

    var incomePerSecond: Double {
        baseIncomePerSecond * Double(owned)
    }

    mutating func buy(count: Int = 1) {
        owned += count
    }
}

enum BusinessCatalog {
    /// Starter businesses for a small private tycoon — swap names/art later.
    static func starterBusinesses() -> [Business] {
        [
            Business(
                id: "cart",
                name: "Lemon Cart",
                blurb: "A folding table and a pitcher.",
                baseCost: 15,
                baseIncomePerSecond: 0.1,
                costGrowth: 1.15,
                owned: 1
            ),
            Business(
                id: "stand",
                name: "Corner Stand",
                blurb: "Painted sign, real napkins.",
                baseCost: 100,
                baseIncomePerSecond: 0.5,
                costGrowth: 1.15,
                owned: 0
            ),
            Business(
                id: "cafe",
                name: "Sidewalk Cafe",
                blurb: "Two tables and a loyal regular.",
                baseCost: 1_100,
                baseIncomePerSecond: 4,
                costGrowth: 1.14,
                owned: 0
            ),
            Business(
                id: "truck",
                name: "Food Truck",
                blurb: "Wheels, a window, lunch rush.",
                baseCost: 12_000,
                baseIncomePerSecond: 30,
                costGrowth: 1.13,
                owned: 0
            ),
            Business(
                id: "hall",
                name: "Market Hall",
                blurb: "A whole aisle of your brand.",
                baseCost: 130_000,
                baseIncomePerSecond: 220,
                costGrowth: 1.12,
                owned: 0
            ),
            Business(
                id: "factory",
                name: "Bottling Works",
                blurb: "Cans clatter; the town notices.",
                baseCost: 1_400_000,
                baseIncomePerSecond: 1_500,
                costGrowth: 1.12,
                owned: 0
            ),
        ]
    }
}
