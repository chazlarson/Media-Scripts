#!/usr/bin/env python3

import os
import sys
import yaml
import subprocess
from pathlib import Path

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found. Please create it first.")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config.yaml: {e}")
        sys.exit(1)

def get_available_scripts(directory):
    """Get list of available Python scripts in a directory"""
    scripts = []
    script_dir = Path(directory)
    if script_dir.exists():
        for file in script_dir.glob("*.py"):
            if not file.name.startswith("_") and file.name != "menu.py":
                scripts.append(file.name)
    return sorted(scripts)

def display_main_menu(config):
    """Display the main category selection menu"""
    print("\n" + "="*60)
    print("🎬 PLEX MEDIA MANAGEMENT TOOLKIT")
    print("="*60)

    # Show current config info
    plex_url = config.get('plex_api', {}).get('auth_server', {}).get('base_url', 'Not configured')
    libraries = config.get('general', {}).get('library_names', '').split(',')
    print(f"📡 Plex Server: {plex_url}")
    print(f"📚 Libraries: {len([lib.strip() for lib in libraries if lib.strip()])} configured")
    print("-"*60)

    print("\nSelect Script Category:")
    print("  1. 🎭 Plex Scripts")
    print("  2. 🎨 Kometa Scripts")
    print("  3. 🎬 TMDB Scripts")
    print("  4. 🖼️  Plex Image Picker")
    print("  5. Exit")
    print("-"*60)

def display_script_menu(category, scripts):
    """Display scripts for a specific category"""
    print(f"\n{category} - Available Scripts:")
    print("-"*60)

    script_map = {}
    for i, script in enumerate(scripts, 1):
        display_name = script.replace('.py', '').replace('-', ' ').title()
        print(f"  {i:2d}. {display_name}")
        script_map[i] = script

    print(f"  {len(scripts)+1:2d}. Back to Main Menu")
    print("-"*40)

    return script_map

def run_script(script_path):
    """Execute the selected script"""
    print(f"\n🚀 Running {script_path}...")
    print("-"*40)

    try:
        # Change to the script's directory and run it
        script_dir = Path(script_path).parent
        script_name = Path(script_path).name

        result = subprocess.run(
            [sys.executable, script_name],
            cwd=script_dir,
            check=True
        )
        print(f"\n✅ {script_name} completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {script_path} failed with exit code {e.returncode}")
    except KeyboardInterrupt:
        print(f"\n⚠️  {script_path} interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running {script_path}: {e}")

    input("\nPress Enter to continue...")

def handle_category_selection(category, directory, config):
    """Handle script selection within a category"""
    scripts = get_available_scripts(directory)

    if not scripts:
        print(f"\n❌ No scripts found in {directory}")
        input("Press Enter to continue...")
        return

    while True:
        try:
            script_map = display_script_menu(category, scripts)

            choice = input(f"\nSelect script (1-{len(script_map)+1}): ").strip()

            if not choice.isdigit():
                print("❌ Please enter a valid number")
                continue

            choice = int(choice)

            if choice == len(script_map) + 1:  # Back to main menu
                break
            elif choice in script_map:
                script_path = Path(directory) / script_map[choice]
                run_script(script_path)
            else:
                print("❌ Invalid selection")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            input("Press Enter to continue...")

def main():
    """Main menu loop"""
    # Load configuration
    config = load_config()

    while True:
        try:
            display_main_menu(config)

            choice = input("\nSelect category (1-5): ").strip()

            if not choice.isdigit():
                print("❌ Please enter a valid number")
                continue

            choice = int(choice)

            if choice == 1:
                handle_category_selection("🎭 Plex Scripts", "Plex", config)
            elif choice == 2:
                handle_category_selection("🎨 Kometa Scripts", "Kometa", config)
            elif choice == 3:
                handle_category_selection("🎬 TMDB Scripts", "TMDB", config)
            elif choice == 4:
                print("\n🖼️  Starting Plex Image Picker...")
                print("Navigate to: Plex Image Picker directory and run 'flask run'")
                input("Press Enter to continue...")
            elif choice == 5:
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid selection")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()