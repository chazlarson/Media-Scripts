import Foundation

protocol GamePersisting: Sendable {
    func load() -> GameSave?
    func save(_ state: GameSave)
    func clear()
}

/// Local JSON in Application Support. Private play — no network, no ads SDK.
struct FileGameStore: GamePersisting {
    private let fileURL: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(filename: String = "idle-tycoon-save.json") {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        self.fileURL = dir.appendingPathComponent(filename)
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }

    func load() -> GameSave? {
        guard let data = try? Data(contentsOf: fileURL) else { return nil }
        return try? decoder.decode(GameSave.self, from: data)
    }

    func save(_ state: GameSave) {
        guard let data = try? encoder.encode(state) else { return }
        try? data.write(to: fileURL, options: [.atomic])
    }

    func clear() {
        try? FileManager.default.removeItem(at: fileURL)
    }
}
