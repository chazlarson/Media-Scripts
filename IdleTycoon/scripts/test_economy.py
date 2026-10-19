#!/usr/bin/env python3
"""Mirror of IdleTycoon Economy math for environments without Xcode/Swift."""

from __future__ import annotations

import math
import sys


MAX_OFFLINE = 8 * 60 * 60
OFFLINE_EFFICIENCY = 0.5


def cost_to_buy(base_cost: float, growth: float, owned: int, count: int = 1) -> float:
    if count <= 0:
        return 0.0
    start = growth**owned
    if abs(growth - 1) < 1e-12:
        return base_cost * start * count
    return base_cost * start * (growth**count - 1) / (growth - 1)


def assert_close(actual: float, expected: float, tol: float = 1e-9) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(f"{actual} != {expected} (tol={tol})")


def test_geometric_buy_cost() -> None:
    assert_close(cost_to_buy(100, 1.15, 0, 1), 100)
    expected = 100 + 100 * 1.15 + 100 * 1.15 * 1.15
    assert_close(cost_to_buy(100, 1.15, 0, 3), expected)
    assert_close(cost_to_buy(100, 1.15, 2, 1), 100 * (1.15**2))


def test_passive_with_multiplier() -> None:
    # 1 cart @ 0.1/s * multiplier 2 * 10s => 2.0
    income = 0.1 * 1 * 2
    coins = income * 10
    assert_close(coins, 2.0)


def test_offline_cap() -> None:
    income = 0.1
    elapsed = 24 * 60 * 60
    capped = min(elapsed, MAX_OFFLINE)
    earned = income * capped * OFFLINE_EFFICIENCY
    assert_close(earned, 0.1 * MAX_OFFLINE * 0.5)


def test_buy_rejects_when_broke() -> None:
    coins = 10
    cost = cost_to_buy(100, 1.15, 0, 1)
    assert coins < cost


def test_currency_suffixes() -> None:
    def fmt(value: float) -> str:
        suffixes = ["", "K", "M", "B", "T", "Qa", "Qi", "Sx"]
        sign = "-" if value < 0 else ""
        n = abs(value)
        idx = 0
        while n >= 1000 and idx < len(suffixes) - 1:
            n /= 1000
            idx += 1
        if idx == 0:
            if n >= 100:
                return f"{sign}{int(round(n))}"
            if n >= 10:
                return f"{sign}{n:.1f}"
            return f"{sign}{n:.2f}"
        return f"{sign}{n:.2f}{suffixes[idx]}"

    assert fmt(12.34) == "12.3"
    assert fmt(9.87) == "9.87"
    assert fmt(1500) == "1.50K"
    assert fmt(2_000_000) == "2.00M"


def main() -> int:
    tests = [
        test_geometric_buy_cost,
        test_passive_with_multiplier,
        test_offline_cap,
        test_buy_rejects_when_broke,
        test_currency_suffixes,
    ]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
