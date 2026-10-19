import SwiftUI

enum TycoonTheme {
    static let backgroundTop = Color(red: 0.07, green: 0.18, blue: 0.20)
    static let backgroundBottom = Color(red: 0.12, green: 0.28, blue: 0.26)
    static let citrus = Color(red: 0.98, green: 0.78, blue: 0.22)
    static let pulp = Color(red: 0.95, green: 0.55, blue: 0.20)
    static let foam = Color(red: 0.93, green: 0.96, blue: 0.94)
    static let moss = Color(red: 0.35, green: 0.72, blue: 0.55)
    static let ink = Color(red: 0.05, green: 0.12, blue: 0.14)

    static var background: LinearGradient {
        LinearGradient(
            colors: [backgroundTop, backgroundBottom],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }
}
