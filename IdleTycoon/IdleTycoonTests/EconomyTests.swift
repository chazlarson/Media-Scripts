import XCTest
@testable import IdleTycoon

final class EconomyTests: XCTestCase {
    func testGeometricBuyCostMatchesSeries() {
        var business = Business(
            id: "t",
            name: "Test",
            blurb: "",
            baseCost: 100,
            baseIncomePerSecond: 1,
            costGrowth: 1.15,
            owned: 0
        )

        let one = business.costToBuy(count: 1)
        XCTAssertEqual(one, 100, accuracy: 1e-9)

        let three = business.costToBuy(count: 3)
        let expected = 100 + 100 * 1.15 + 100 * 1.15 * 1.15
        XCTAssertEqual(three, expected, accuracy: 1e-9)

        business.buy(count: 2)
        XCTAssertEqual(business.owned, 2)
        XCTAssertEqual(business.costToBuy(), 100 * pow(1.15, 2), accuracy: 1e-9)
    }

    func testPassiveIncomeUsesMultiplier() {
        var save = GameSave.fresh()
        save.globalMultiplier = 2
        // Starter owns 1 lemon cart @ 0.1/s → 0.2/s with multiplier
        Economy.applyPassive(save: &save, delta: 10)
        XCTAssertEqual(save.coins, 2.0, accuracy: 1e-9)
    }

    func testBuyRejectsWhenBroke() {
        var save = GameSave.fresh()
        save.coins = 10
        let ok = Economy.buyBusiness(id: "stand", save: &save)
        XCTAssertFalse(ok)
        XCTAssertEqual(save.businesses.first { $0.id == "stand" }?.owned, 0)
    }

    func testOfflineEarningsCappedAndDiscounted() {
        var save = GameSave.fresh()
        save.lastTick = Date().addingTimeInterval(-24 * 60 * 60)
        let income = Economy.incomePerSecond(save: save)
        let earned = Economy.collectOfflineEarnings(save: &save)
        let expected = income * GameBalance.maxOfflineSeconds * GameBalance.offlineEfficiency
        XCTAssertEqual(earned, expected, accuracy: 1e-6)
    }

    func testCurrencyFormatSuffixes() {
        XCTAssertEqual(CurrencyFormat.coins(12.34), "12.3")
        XCTAssertEqual(CurrencyFormat.coins(9.87), "9.87")
        XCTAssertEqual(CurrencyFormat.coins(1_500), "1.50K")
        XCTAssertEqual(CurrencyFormat.coins(2_000_000), "2.00M")
    }
}
