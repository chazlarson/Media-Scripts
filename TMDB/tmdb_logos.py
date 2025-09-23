from pathlib import Path
import requests
import os
from alive_progress import alive_bar
from config import Config
from plexapi.server import PlexServer
from helpers import get_plex, get_target_libraries, get_all_from_library

def download_tmdb_logo(tmdb_obj):
    """
    Downloads the logo for a movie or TV show from TMDB.

    Args:
        tmdb_id (int): The TMDB ID of the movie or TV show.
        api_key (str): Your TMDB API key.
        save_path (str): The directory where the logo will be saved.
        show_type (str): The type of content, either "movie" or "tv".
    """
    # TMDB API endpoint for images
    base_url = "https://api.themoviedb.org/3"
    image_base_url = "https://image.tmdb.org/t/p/original"

    api_key = config.get("general.tmdb_key", "NO_KEY_SPECIFIED")

    # Construct the API request URL
    api_url = f"{base_url}/{tmdb_obj['type']}/{tmdb_obj['tmdb_id']}/images?api_key={api_key}"

    save_path = config.get("image_download.where_to_put_it.logo_dir", "tmdb_logos")

    try:
        # Get the list of images from the TMDB API
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        # Find the first logo file path (logos are typically under "logos")
        logo_path = None
        if "logos" in data and data["logos"]:
            logo_path = data["logos"][0]["file_path"]

        # If a logo path is found, download the image
        if logo_path:
            full_image_url = f"{image_base_url}{logo_path}"

            # Get the file name from the URL
            file_name = os.path.basename(logo_path)

            # Download the image content
            image_response = requests.get(full_image_url)
            image_response.raise_for_status()

            # Create the full file path to save the image
            folder_path = os.path.join(save_path, tmdb_obj['library'], tmdb_obj['title'])
            Path(folder_path).mkdir(parents=True, exist_ok=True)

            # Create the full file path to save the image
            file_path = os.path.join(folder_path, file_name)

            # Save the image in binary write mode
            with open(file_path, "wb") as f:
                f.write(image_response.content)

            print(f"Successfully downloaded logo for TMDB ID {tmdb_obj['tmdb_id']} to {file_path}")
        else:
            print(f"No logo found for TMDB ID {tmdb_obj['tmdb_id']}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_tmdb_ids_from_plex():
    """
    Connects to a Plex server and retrieves TMDB IDs from a specific library.

    Args:
        baseurl (str): The URL of your Plex server.
        token (str): Your Plex authentication token.
        library_name (str): The name of the library (e.g., 'Movies', 'TV Shows').

    Returns:
        A list of dictionaries, where each dictionary contains the title and TMDB ID.
    """
    try:
        plex = get_plex()
        LIB_ARRAY = get_target_libraries(plex)

        tmdb_ids = []

        for lib in LIB_ARRAY:
            # Iterate through all items in the specified library
          the_lib = plex.library.section(lib)
          item_count, items = get_all_from_library(
              the_lib, None, None
              )

          if item_count > 0:
              print(f"looping over {item_count} items...", "info", "a")
              item_count = 0

              with alive_bar(
                  item_count,
                  dual_line=True,
                  title=f"Grab all posters {the_lib.title}",
              ) as bar:

                for item in items:
                    tmdb_id = None

                    # Plex stores external IDs in a list of GUIDs
                    for guid in item.guids:
                        if guid.id.startswith('tmdb://'):
                            tmdb_id = guid.id.split('://')[1]
                            break

                    # Only add items with a found TMDB ID to the list
                    if tmdb_id:
                        if item.TYPE == "show":
                            type = 'tv'
                        else:
                            type = 'movie'

                        tmdb_ids.append({
                            "library": the_lib.title,
                            "title": item.title,
                            "tmdb_id": int(tmdb_id),
                            "type": type
                        })

        return tmdb_ids

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

config = Config('../config.yaml')

tmdb_data = get_tmdb_ids_from_plex()

if tmdb_data:
    print(f"Found {len(tmdb_data)} items with TMDB IDs.")
    for item in tmdb_data:
        print(f"Title: {item['title']}, TMDB ID: {item['tmdb_id']}, Type: {item['type']}")
        download_tmdb_logo(item)
