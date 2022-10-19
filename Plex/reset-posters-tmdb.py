from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
import pathlib
import platform
from timeit import default_timer as timer
import time

from helpers import booler, redact, getTID, validate_filename, getPath

# import tvdb_v4_official

start = timer()

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')

if PLEX_URL is None:
    print("Your .env file is incomplete or missing: PLEX_URL is empty")
    exit()

PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
TMDB_KEY = os.getenv('TMDB_KEY')
TVDB_KEY = os.getenv('TVDB_KEY')
TARGET_LABELS = os.getenv('TARGET_LABELS')
TRACK_RESET_STATUS = os.getenv('TRACK_RESET_STATUS')
REMOVE_LABELS = booler(os.getenv('REMOVE_LABELS'))
RESET_SEASONS = booler(os.getenv('RESET_SEASONS'))
RESET_EPISODES = booler(os.getenv('RESET_EPISODES'))
LOCAL_RESET_ARCHIVE = booler(os.getenv('LOCAL_RESET_ARCHIVE'))

DELAY = 0
try:
    DELAY = int(os.getenv('DELAY'))
except:
    DELAY = 0

if TARGET_LABELS:
    lbl_array = TARGET_LABELS.split(",")
else:
    lbl_array = ["xy22y1973"]

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

IS_WINDOWS = platform.system() == 'Windows'

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

local_dir = os.path.join(os.getcwd(), "posters")

os.makedirs(local_dir, exist_ok=True)

show_dir = os.path.join(os.getcwd(), "shows")
movie_dir = os.path.join(os.getcwd(), "movies")

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def localFilePath(tgt_dir, rating_key):
    for ext in ['jpg','png']:
        local_file = os.path.join(tgt_dir, f"{item.ratingKey}.{ext}")
        if os.path.exists(local_file):
            return local_file
    return None

print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = 'original'

from pathlib import Path

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    id_array = []
    status_file_name = plex.library.section(lib).uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        with open(f"{status_file_name}") as fp:
            for line in fp:
                id_array.append(line.strip())

    for lbl in lbl_array:
        if lbl == "xy22y1973":
            print(f"{os.linesep}getting all items from the library [{lib}]...")
            items = plex.library.section(lib).all()
            REMOVE_LABELS = False
        else:
            print(f"{os.linesep}getting items from the library [{lib}] with the label [{lbl}]...")
            items = plex.library.section(lib).search(label=lbl)
        item_total = len(items)
        print(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title='Poster Reset - TMDB') as bar:
            for item in items:
                item_count = item_count + 1
                i_rk = item.ratingKey
                if id_array.count(f"{i_rk}") == 0:
                    id_array.append(i_rk)

                    imdbid, tmdb_id, tvdb_id = getTID(item.guids)
                    try:
                        bar.text = f'-> starting: {item.title}'
                        pp = None
                        local_file = None
                        tmdb_item = None

                        if item.TYPE == 'show':
                            tgt_dir = show_dir
                            if LOCAL_RESET_ARCHIVE:
                                local_file = localFilePath(tgt_dir, i_rk)
                                pp = local_file
                            if local_file is None:
                                try:
                                    if tmdb_id:
                                        tmdb_item = tmdb.tv_show(tmdb_id)
                                    else:
                                        tmdb_item = tmdb.find_by_id(tvdb_id=tvdb_id).tv_results[0].poster_path
                                    pp = tmdb_item.poster_path
                                except:
                                    pp = None
                        else:
                            tgt_dir = movie_dir
                            if LOCAL_RESET_ARCHIVE:
                                local_file = localFilePath(tgt_dir, i_rk)
                                pp = local_file
                            if local_file is None:
                                try:
                                    tmdb_item = tmdb.movie(tmdb_id)
                                    pp = tmdb_item.poster_path
                                except:
                                    pp = None

                        if pp is not None:
                            posterURL = f"{base_url}{size_str}{pp}"

                            if LOCAL_RESET_ARCHIVE:
                                if local_file is None or not os.path.exists(local_file):
                                    ext = pathlib.Path(pp).suffix
                                    local_file = os.path.join(tgt_dir, f"{i_rk}.{ext}")
                                    bar.text = f'-> downloading poster: {item.title}'

                                if not os.path.exists(local_file):
                                    r = requests.get(posterURL, allow_redirects=True)
                                    open(f"{local_file}", 'wb').write(r.content)

                                bar.text = f'-> uploading poster: {item.title}'
                                item.uploadPoster(filepath=local_file)
                            else:
                                bar.text = f'-> setting poster URL: {item.title}'
                                item.uploadPoster(url=posterURL)

                            # if item.TYPE == 'show':

                            #     if RESET_SEASONS:
                            #         # get seasons
                            #         seasons = item.seasons()
                            #         tmdb_seasons = tmdb_item.seasons

                            #         # loop over all:
                            #         s_idx = 0
                            #         for s in seasons:
                            #             s_id = s.seasonNumber
                            #             s_found = False

                            #             for ss in tmdb_seasons:

                            #                 if ss.season_number == s_id and not s_found:
                            #                     s_found = True

                            #                     if tmdb_id:
                            #                         tmdb_episodes = tmdb.tv_show(tmdb_id).seasons[s_idx].episodes
                            #                     else:
                            #                         tmdb_episodes = tmdb.find_by_id(tvdb_id=tvdb_id).tv_results[0].seasons[s_idx].episodes


                            #                     pp = ss.poster_path

                            #                     posterURL = f"{base_url}{size_str}{pp}"
                            #                     local_file = localFilePath(tgt_dir, f"{i_rk}-S{s_id}")

                            #                     if LOCAL_RESET_ARCHIVE:
                            #                         if local_file is None or not os.path.exists(local_file):
                            #                             ext = pathlib.Path(pp).suffix
                            #                             local_file = os.path.join(tgt_dir, f"{i_rk}-S{s_id}.{ext}")
                            #                             bar.text = f'-> downloading poster: {item.title} S{s_id}'

                            #                         if not os.path.exists(local_file):
                            #                             r = requests.get(posterURL, allow_redirects=True)
                            #                             open(f"{local_file}", 'wb').write(r.content)

                            #                         bar.text = f'-> uploading poster: {item.title} S{s_id}'
                            #                         s.uploadPoster(filepath=local_file)
                            #                     else:
                            #                         bar.text = f'-> setting poster URL: {item.title} S{s_id}'
                            #                         s.uploadPoster(url=posterURL)

                            #                     if RESET_EPISODES:
                            #                         # get episodes
                            #                         episodes = item.episodes()

                            #                         # loop over all
                            #                         e_found = False
                            #                         e_idx = 0
                            #                         for e in episodes:
                            #                             e_id = e.episodeNumber

                            #                             if e.seasonNumber == s_id:
                            #                                 tmdb_ep = tmdb_episodes[e_idx]

                            #                                 if tmdb_ep.episode_number == e_id and tmdb_ep.season_number == s_id and not e_found:
                            #                                     e_found = True
                            #                                     pp = tmdb_ep.still_path
                            #                                     posterURL = f"{base_url}{size_str}{pp}"
                            #                                     local_file = localFilePath(tgt_dir, f"{i_rk}-S{s_id}E{e_id}")

                            #                                     if LOCAL_RESET_ARCHIVE:
                            #                                         if local_file is None or not os.path.exists(local_file):
                            #                                             ext = pathlib.Path(pp).suffix
                            #                                             local_file = os.path.join(tgt_dir, f"{i_rk}-S{s_id}E{e_id}.{ext}")
                            #                                             bar.text = f'-> downloading poster: {item.title} S{s_id}E{e_id}'

                            #                                         if not os.path.exists(local_file):
                            #                                             r = requests.get(posterURL, allow_redirects=True)
                            #                                             open(f"{local_file}", 'wb').write(r.content)

                            #                                         bar.text = f'-> uploading poster: {item.title} S{s_id}E{e_id}'
                            #                                         e.uploadPoster(filepath=local_file)
                            #                                     else:
                            #                                         bar.text = f'-> setting poster URL: {item.title} S{s_id}E{e_id}'
                            #                                         e.uploadPoster(url=posterURL)

                            #                             e_idx += 1

                            #             s_idx += 1
                        else:
                            bar.text = f'-> unknown type: {item.title}'

                        if REMOVE_LABELS:
                            bar.text = f'-> removing label {lbl}: {item.title}'
                            item.removeLabel(lbl, True)

                        # write out item_array to file.
                        with open(status_file, "a", encoding='utf-8') as sf:
                            sf.write(f"{i_rk}{os.linesep}")

                    except Exception as ex:
                        print(f'Exception processing "{item.title}"')

                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

    # delete the status file
    if status_file.is_file():
        os.remove(status_file)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
