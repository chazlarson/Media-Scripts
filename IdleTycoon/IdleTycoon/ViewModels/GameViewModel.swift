import Foundation
import Observation

@MainActor
@Observable
final class GameViewModel {
    private(set) var save: GameSave
    private(set) var offlineBanner: String?
    private(set) var lastSavedAt: Date?

    private let store: any GamePersisting
    private var autosaveTask: Task<Void, Never>?
    private var tickTask: Task<Void, Never>?

    var incomePerSecond: Double { Economy.incomePerSecond(save: save) }
    var tapValue: Double { Economy.tapValue(save: save) }
    var multiplierCost: Double { Economy.multiplierUpgradeCost(save: save) }

    init(store: any GamePersisting = FileGameStore()) {
        self.store = store
        if var loaded = store.load() {
            let earned = Economy.collectOfflineEarnings(save: &loaded)
            self.save = loaded
            if earned > 0.01 {
                self.offlineBanner = "While you were away: +\(CurrencyFormat.coins(earned))"
            }
            store.save(loaded)
            self.lastSavedAt = .now
        } else {
            self.save = .fresh()
        }
        startAutosave()
        startTicker()
    }

    deinit {
        autosaveTask?.cancel()
        tickTask?.cancel()
    }

    func dismissOfflineBanner() {
        offlineBanner = nil
    }

    func tick(delta: TimeInterval) {
        Economy.applyPassive(save: &save, delta: delta)
        save.lastTick = .now
    }

    func tapStand() {
        Economy.tap(save: &save)
    }

    func buy(_ businessID: String, count: Int = 1) {
        _ = Economy.buyBusiness(id: businessID, count: count, save: &save)
        persist()
    }

    func buyMultiplier() {
        _ = Economy.buyMultiplier(save: &save)
        persist()
    }

    func resetProgress() {
        store.clear()
        save = .fresh()
        offlineBanner = nil
        persist()
    }

    func persist() {
        store.save(save)
        lastSavedAt = .now
    }

    private func startAutosave() {
        autosaveTask?.cancel()
        autosaveTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(5))
                self?.persist()
            }
        }
    }

    private func startTicker() {
        tickTask?.cancel()
        tickTask = Task { [weak self] in
            var last = Date.now
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(100))
                let now = Date.now
                let delta = now.timeIntervalSince(last)
                last = now
                self?.tick(delta: min(delta, 1))
            }
        }
    }
}
