#!/usr/bin/env python3
"""Single entry point for Media Scripts.

Run an interactive menu, or start one script by name. A container can use
this file as its command:

    python orchestrator.py list
    python orchestrator.py grab-all-posters
    python orchestrator.py plex/check-square-art --sample-size 1
    python orchestrator.py picker
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CATEGORIES = {
    "plex": ROOT / "Plex",
    "kometa": ROOT / "Kometa",
    "tmdb": ROOT / "TMDB",
}

# Libraries that live next to the runnable scripts.
SKIP_NAMES = {
    "config.py",
    "database.py",
    "helpers.py",
    "kometa-helpers.py",
    "logs.py",
}

# These scripts prompt for their own credentials and do not read config.yaml.
CONFIG_OPTIONAL = {
    "kometa-mal-auth.py",
    "kometa-trakt-auth.py",
}

PICKER_DIR = ROOT / "Plex Image Picker"


class ScriptLookupError(Exception):
    """A script name matched nothing, or matched more than one script."""


def runnable_scripts(category=None):
    """Return (category, path) pairs for scripts a user can launch."""
    categories = CATEGORIES
    if category is not None:
        if category not in CATEGORIES:
            known = ", ".join(CATEGORIES)
            raise ScriptLookupError(f"Unknown category '{category}'. Known categories: {known}")
        categories = {category: CATEGORIES[category]}

    found = []
    for name, directory in categories.items():
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_") or path.name in SKIP_NAMES:
                continue
            found.append((name, path))
    return found


def resolve_script(token):
    """Resolve a script token to (category, path).

    Accepts 'grab-all-posters', 'grab-all-posters.py', or 'plex/grab-all-posters'.
    """
    token = token.strip().replace("\\", "/")
    category = None
    name = token
    if "/" in token:
        category, name = token.split("/", 1)
        if category not in CATEGORIES:
            known = ", ".join(CATEGORIES)
            raise ScriptLookupError(f"Unknown category '{category}'. Known categories: {known}")

    stem = name[:-3] if name.endswith(".py") else name
    filename = f"{stem}.py"
    matches = [
        item
        for item in runnable_scripts(category)
        if item[1].name == filename or item[1].stem == stem
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ScriptLookupError(f"No script named '{token}'. Try: python orchestrator.py list")
    names = ", ".join(f"{item[0]}/{item[1].stem}" for item in matches)
    raise ScriptLookupError(f"'{token}' matches more than one script: {names}")


def config_path():
    return ROOT / "config.yaml"


def require_config(script_name, args):
    if script_name in CONFIG_OPTIONAL or config_path().is_file():
        return None
    if args and args[0] in {"-h", "--help"}:
        return None
    return (
        "config.yaml was not found at the repository root. "
        "Copy config.template.yaml to config.yaml and edit it."
    )


def run_script(path, args):
    """Run a script with its own directory as the working directory."""
    problem = require_config(path.name, args)
    if problem:
        print(problem, file=sys.stderr)
        return 2
    completed = subprocess.run(
        [sys.executable, path.name, *args],
        cwd=path.parent,
        check=False,
    )
    return completed.returncode


def run_picker(args):
    """Start the Plex Image Picker web UI."""
    if not (PICKER_DIR / "app.py").is_file():
        print(f"Plex Image Picker was not found at {PICKER_DIR}", file=sys.stderr)
        return 2
    command = [sys.executable, "-m", "flask", "run", "--host=0.0.0.0", *args]
    completed = subprocess.run(
        command,
        cwd=PICKER_DIR,
        env={**os.environ.copy(), "FLASK_APP": "app.py"},
        check=False,
    )
    return completed.returncode


def print_help():
    print(
        """Media Scripts orchestrator

  python orchestrator.py                         Interactive menu on a TTY
  python orchestrator.py menu
  python orchestrator.py list [plex|kometa|tmdb]
  python orchestrator.py <script> [args...]      Run one script
  python orchestrator.py run <script> [args...]
  python orchestrator.py picker                  Plex Image Picker on 0.0.0.0:5000

Script names match the filename, with or without .py.
A category prefix is optional unless two scripts share a name.

  python orchestrator.py grab-all-posters
  python orchestrator.py plex/check-square-art --sample-size 1

Each script runs from its own directory and reads ../config.yaml.
Copy config.template.yaml to config.yaml at the repository root.
"""
    )


def print_list(category=None):
    scripts = runnable_scripts(category)
    current = None
    for name, path in scripts:
        if name != current:
            print(f"{name}:")
            current = name
        print(f"  {path.stem}")
    print("picker:")
    print("  app.py")


def cmd_run(argv):
    if not argv:
        print("Name the script to run. Try: python orchestrator.py list", file=sys.stderr)
        return 2
    if argv[0] in CATEGORIES and len(argv) >= 2:
        token = f"{argv[0]}/{argv[1]}"
        args = argv[2:]
    else:
        token = argv[0]
        args = argv[1:]
    category, path = resolve_script(token)
    print(f"Running {category}/{path.name}")
    return run_script(path, args)


def interactive_menu():
    import menu

    return menu.main()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        if sys.stdin.isatty():
            return interactive_menu()
        print_help()
        return 2

    command = argv[0]
    if command in {"-h", "--help", "help"}:
        print_help()
        return 0
    if command == "menu":
        return interactive_menu()
    if command == "list":
        if len(argv) > 2:
            print("Usage: python orchestrator.py list [plex|kometa|tmdb]", file=sys.stderr)
            return 2
        try:
            print_list(argv[1] if len(argv) == 2 else None)
        except ScriptLookupError as exc:
            print(exc, file=sys.stderr)
            return 2
        return 0
    if command == "picker":
        return run_picker(argv[1:])
    if command == "run":
        try:
            return cmd_run(argv[1:])
        except ScriptLookupError as exc:
            print(exc, file=sys.stderr)
            return 2
    try:
        return cmd_run(argv)
    except ScriptLookupError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
