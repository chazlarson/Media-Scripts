from pathlib import Path
import requests
import os
from alive_progress import alive_bar
from config import Config
from helpers import get_plex, get_target_libraries, get_all_from_library


def download_tmdb_logo(tmdb_obj):
    """
    Downloads the logo for a movie or TV show from TMDB.

    Args:
        tmdb_obj (dict): Item with library, title, tmdb_id, and type ("movie" or "tv").
    """
    config = Config("../config.yaml")
    base_url = "https://api.themoviedb.org/3"
    image_base_url = "https://image.tmdb.org/t/p/original"

    api_key = config.get("general.tmdb_key", "NO_KEY_SPECIFIED")
    api_url = (
        f"{base_url}/{tmdb_obj['type']}/{tmdb_obj['tmdb_id']}/images?api_key={api_key}"
    )
    save_path = config.get("image_download.where_to_put_it.logo_dir", "tmdb_logos")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        logo_path = None
        if "logos" in data and data["logos"]:
            logo_path = data["logos"][0]["file_path"]

        if logo_path:
            full_image_url = f"{image_base_url}{logo_path}"
            file_name = os.path.basename(logo_path)

            image_response = requests.get(full_image_url)
            image_response.raise_for_status()

            folder_path = os.path.join(
                save_path, tmdb_obj["library"], tmdb_obj["title"]
            )
            Path(folder_path).mkdir(parents=True, exist_ok=True)
            file_path = os.path.join(folder_path, file_name)

            with open(file_path, "wb") as f:
                f.write(image_response.content)

            print(
                f"Successfully downloaded logo for TMDB ID {tmdb_obj['tmdb_id']} to {file_path}"
            )
        else:
            print(f"No logo found for TMDB ID {tmdb_obj['tmdb_id']}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def get_tmdb_ids_from_plex():
    """
    Connects to a Plex server and retrieves TMDB IDs from the configured libraries.

    Returns:
        A list of dictionaries with library, title, tmdb_id, and type.
    """
    try:
        plex = get_plex()
        lib_array = get_target_libraries(plex)
        tmdb_ids = []

        for lib in lib_array:
            the_lib = plex.library.section(lib)
            _loaded_count, items = get_all_from_library(the_lib, None, None)

            if not items:
                continue

            print(f"looping over {len(items)} items...")
            with alive_bar(
                len(items),
                dual_line=True,
                title=f"TMDB logos {the_lib.title}",
            ) as bar:
                for item in items:
                    tmdb_id = None
                    for guid in item.guids:
                        if guid.id.startswith("tmdb://"):
                            tmdb_id = guid.id.split("://")[1]
                            break

                    if tmdb_id:
                        media_type = "tv" if item.TYPE == "show" else "movie"
                        tmdb_ids.append(
                            {
                                "library": the_lib.title,
                                "title": item.title,
                                "tmdb_id": int(tmdb_id),
                                "type": media_type,
                            }
                        )
                    bar()

        return tmdb_ids

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def main():
    tmdb_data = get_tmdb_ids_from_plex()

    if tmdb_data:
        print(f"Found {len(tmdb_data)} items with TMDB IDs.")
        for item in tmdb_data:
            print(
                f"Title: {item['title']}, TMDB ID: {item['tmdb_id']}, Type: {item['type']}"
            )
            download_tmdb_logo(item)


if __name__ == "__main__":
    main()
