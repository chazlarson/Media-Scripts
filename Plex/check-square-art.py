#!/usr/bin/env python

from collections import Counter
from datetime import datetime
from itertools import islice
from pathlib import Path
import argparse

from helpers import get_plex, get_target_libraries
from logs import plogger, setup_logger

SCRIPT_NAME = Path(__file__).stem
VERSION = "0.1.0"

now = datetime.now()
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger("activity_log", ACTIVITY_LOG)


def count_or_none(fetcher):
    try:
        return len(fetcher())
    except Exception:
        return None


def sample_items(lib, sample_size):
    if sample_size <= 0:
        return list(lib.all())
    return list(islice(lib.all(), sample_size))


def summarize_library(lib, sample_size):
    items = sample_items(lib, sample_size)
    summary = Counter()
    examples = []

    for item in items:
        posters = count_or_none(item.posters)
        backgrounds = count_or_none(item.arts)
        logos = count_or_none(item.logos) if hasattr(item, "logos") else None
        squares = (
            count_or_none(item.squareArts) if hasattr(item, "squareArts") else None
        )
        current_square = bool(getattr(item, "squareArtUrl", None))

        if posters and posters > 0:
            summary["items_with_posters"] += 1
        if backgrounds and backgrounds > 0:
            summary["items_with_backgrounds"] += 1
        if logos and logos > 0:
            summary["items_with_logos"] += 1
        if squares and squares > 0:
            summary["items_with_square_art"] += 1
            if len(examples) < 5:
                examples.append(f"{item.title} ({squares})")
        if current_square:
            summary["items_with_current_square_url"] += 1

    return items, summary, examples


def main():
    parser = argparse.ArgumentParser(
        description="Report Plex square-art availability in target libraries."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=25,
        help="Number of items to sample per library. Use 0 to scan every item.",
    )
    args = parser.parse_args()

    plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

    plex = get_plex()
    libs = get_target_libraries(plex)

    for lib_name in libs:
        lib = plex.library.section(lib_name)
        if lib.type not in ("movie", "show"):
            plogger(f"Skipping {lib_name} ({lib.type}); unsupported library type", "info", "a")
            continue

        items, summary, examples = summarize_library(lib, args.sample_size)
        total = len(items)
        plogger(f"LIBRARY: {lib_name} ({lib.type}) sampled={total}", "info", "a")
        plogger(
            f"  posters: {summary['items_with_posters']}/{total}",
            "info",
            "a",
        )
        plogger(
            f"  backgrounds: {summary['items_with_backgrounds']}/{total}",
            "info",
            "a",
        )
        plogger(
            f"  logos: {summary['items_with_logos']}/{total}",
            "info",
            "a",
        )
        plogger(
            f"  square_art_list: {summary['items_with_square_art']}/{total}",
            "info",
            "a",
        )
        plogger(
            f"  current_square_url: {summary['items_with_current_square_url']}/{total}",
            "info",
            "a",
        )
        if examples:
            plogger(f"  square art examples: {', '.join(examples)}", "info", "a")
        plogger("", "info", "a")


if __name__ == "__main__":
    main()
