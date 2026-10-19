# Corner Empire (Idle Tycoon)

Private SwiftUI idle tycoon for iPhone — **no ads, no IAP, no network**. Progress saves locally as JSON.

This is a starter you can reskin: same loop as the “same game, different art” genre kits, but your own code and balance.

## Open in Xcode (Mac)

1. Open `IdleTycoon/IdleTycoon.xcodeproj`.
2. Select an iPhone simulator or your device.
3. Set your Team under **Signing & Capabilities** (for device installs).
4. Run (⌘R).

Optional: regenerate the project file after adding sources:

```bash
python3 scripts/generate_xcodeproj.py
```

## What’s included

| Piece | Role |
| --- | --- |
| `Business` + `BusinessCatalog` | Generators with geometric cost growth |
| `Economy` | Tap, passive income, offline cap, global multiplier |
| `FileGameStore` | Local JSON in Application Support |
| `GameViewModel` | 10 Hz tick + autosave |
| SwiftUI views | One-screen tycoon UI (“Corner Empire”) |

## Core loop (idle formula)

- Business cost for the next `n` buys: geometric series on `baseCost * costGrowth^owned`
- Income/sec = `sum(baseIncome * owned) * globalMultiplier`
- Offline = min(away, 8h) × income/sec × 0.5
- Tap = `1 * globalMultiplier`

Tune numbers in `Models/GameSave.swift` (`GameBalance`) and `BusinessCatalog`.

## Private play, no ads

There is no AdMob (or any) SDK. Keep it that way for a personal build.

- **Simulator / your device (dev signing):** fine for private use
- **TestFlight / friends:** Apple Developer Program
- **App Store:** only if you want public distribution later

## Open references (SwiftUI idle / clicker)

Useful examples to read (not vendored here):

- [bennaro/ClickerGame](https://github.com/bennaro/clickergame) — Cookie Clicker–style SwiftUI
- [XanderJenei/ToggleTycoon](https://github.com/XanderJenei/ToggleTycoon) — incremental SwiftUI prototype
- [mat-sz/SwiftUI-Clicker](https://github.com/mat-sz/SwiftUI-Clicker) — small SwiftUI incremental demo

## Tests

On a Mac with Xcode:

```bash
xcodebuild -scheme IdleTycoon -destination 'platform=iOS Simulator,name=iPhone 16' test
```

On this Linux environment, economy math is mirrored in `scripts/test_economy.py`:

```bash
python3 scripts/test_economy.py
```

## Next levers (when you want to grow it)

1. Prestige / prestige currency that resets businesses
2. Managers that auto-buy or multiply one business
3. Simple art pack (SF Symbols → custom assets)
4. Haptics on squeeze / big purchases
5. Achievements (lifetime coins milestones)
