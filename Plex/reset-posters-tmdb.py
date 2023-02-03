from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
import logging
import os
from dotenv import load_dotenv
from tmdbapis import TMDbAPIs
import requests
import pathlib
from pathlib import Path
import platform
from timeit import default_timer as timer
import time

from helpers import booler, get_ids, get_plex, get_all

# import tvdb_v4_official

start = timer()

import logging
from pathlib import Path
SCRIPT_NAME = Path(__file__).stem

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info(f"No environment [.env] file.  Exiting.")
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")

if PLEX_URL is None:
    print("Your .env file is incomplete or missing: PLEX_URL is empty")
    exit()

PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TMDB_KEY = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
TARGET_LABELS = os.getenv("TARGET_LABELS")
TRACK_RESET_STATUS = os.getenv("TRACK_RESET_STATUS")
REMOVE_LABELS = booler(os.getenv("REMOVE_LABELS"))
RESET_SEASONS = booler(os.getenv("RESET_SEASONS"))
RESET_EPISODES = booler(os.getenv("RESET_EPISODES"))
LOCAL_RESET_ARCHIVE = booler(os.getenv("LOCAL_RESET_ARCHIVE"))

DELAY = 0
try:
    DELAY = int(os.getenv("DELAY"))
except:
    DELAY = 0

if TARGET_LABELS:
    LBL_ARRAY = TARGET_LABELS.split(",")
else:
    LBL_ARRAY = ["xy22y1973"]

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

IS_WINDOWS = platform.system() == "Windows"

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

local_dir = os.path.join(os.getcwd(), "posters")

os.makedirs(local_dir, exist_ok=True)

show_dir = os.path.join(os.getcwd(), "shows")
movie_dir = os.path.join(os.getcwd(), "movies")

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

def print_and_log(msg):
    logging.info(msg)
    print(msg)

def localFilePath(tgt_dir, rating_key):
    for ext in ["jpg", "png"]:
        local_file = os.path.join(tgt_dir, f"{item.ratingKey}.{ext}")
        if os.path.exists(local_file):
            return local_file
    return None


print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = "original"

plex = get_plex(PLEX_URL, PLEX_TOKEN)

logging.info("connection success")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    status_file_name = the_lib.uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        with open(f"{status_file_name}") as fp:
            for line in fp:
                id_array.append(line.strip())

    for lbl in LBL_ARRAY:
        if lbl == "xy22y1973":
            print(f"{os.linesep}getting all items from the library [{lib}]...")
            items = get_all(plex, the_lib)
            REMOVE_LABELS = False
        else:
            print(
                f"{os.linesep}getting items from the library [{lib}] with the label [{lbl}]..."
            )
            items = the_lib.search(label=lbl)
        item_total = len(items)
        print_and_log(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - TMDB") as bar:
            for item in items:
                item_count = item_count + 1
                i_rk = item.ratingKey
                i_t = item.title
                if id_array.count(f"{i_rk}") == 0:
                    id_array.append(i_rk)

                    imdbid, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)
                    try:
                        bar_and_log(bar, f"-> starting: {i_t}")
                        pp = None
                        local_file = None
                        tmdb_item = None

                        if item.TYPE == "show":
                            tgt_dir = show_dir
                            if LOCAL_RESET_ARCHIVE:
                                local_file = localFilePath(tgt_dir, i_rk)
                                pp = local_file
                            if local_file is None:
                                try:
                                    if tmdb_id:
                                        tmdb_item = tmdb.tv_show(tmdb_id)
                                    else:
                                        tmdb_item = (
                                            tmdb.find_by_id(tvdb_id=tvdb_id)
                                            .tv_results[0]
                                            .poster_path
                                        )
                                    tmdb_item.reload()
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

                        logging.info(f"poster_path: {pp}")

                        if pp is not None:
                            seriesPosterURL = f"{base_url}{size_str}{pp}"
                            logging.info(f"seriesPosterURL: {seriesPosterURL}")

                            if LOCAL_RESET_ARCHIVE:
                                if local_file is None or not os.path.exists(local_file):
                                    ext = pathlib.Path(pp).suffix
                                    local_file = os.path.join(tgt_dir, f"{i_rk}.{ext}")
                                    bar_and_log(bar, f"-> downloading poster: {i_t}")

                                if not os.path.exists(local_file):
                                    r = requests.get(
                                        seriesPosterURL, allow_redirects=True
                                    )
                                    open(f"{local_file}", "wb").write(r.content)

                                bar_and_log(bar, f"-> uploading poster: {i_t}")
                                item.uploadPoster(filepath=local_file)
                            else:
                                bar_and_log(bar, f"-> setting poster URL: {i_t}")
                                item.uploadPoster(url=seriesPosterURL)

                            if item.TYPE == "show":

                                if RESET_SEASONS:
                                    # get seasons
                                    seasons = item.seasons()
                                    tmdb_seasons = tmdb_item.seasons

                                    # loop over all:
                                    s_idx = 0
                                    for s in seasons:
                                        s_id = s.seasonNumber
                                        s_found = False

                                        for ss in tmdb_seasons:
                                            ss.reload()

                                            if ss.season_number == s_id and not s_found:
                                                s_found = True

                                                pp = ss.poster_path
                                                if pp is None:
                                                    posterURL = seriesPosterURL
                                                    pp = posterURL.rsplit("/", 1)[-1]
                                                else:
                                                    posterURL = (
                                                        f"{base_url}{size_str}{pp}"
                                                    )
                                                local_file = localFilePath(
                                                    tgt_dir, f"{i_rk}-S{s_id}"
                                                )
                                                logging.info(f"posterURL: {posterURL}")

                                                if LOCAL_RESET_ARCHIVE:
                                                    if (
                                                        local_file is None
                                                        or not os.path.exists(
                                                            local_file
                                                        )
                                                    ):
                                                        ext = pathlib.Path(pp).suffix
                                                        local_file = os.path.join(
                                                            tgt_dir,
                                                            f"{i_rk}-S{s_id}{ext}",
                                                        )
                                                        bar_and_log(bar, f"-> downloading poster: {i_t} S{s_id}")

                                                    if not os.path.exists(local_file):
                                                        r = requests.get(
                                                            posterURL,
                                                            allow_redirects=True,
                                                        )
                                                        open(
                                                            f"{local_file}", "wb"
                                                        ).write(r.content)

                                                    bar_and_log(bar, f"-> uploading poster: {i_t} S{s_id}")
                                                    s.uploadPoster(filepath=local_file)
                                                else:
                                                    bar_and_log(bar, f"-> setting poster URL: {i_t} S{s_id}")
                                                    s.uploadPoster(url=posterURL)

                                                if RESET_EPISODES:
                                                    # get episodes
                                                    tmdb_episodes = ss.episodes
                                                    episodes = s.episodes()

                                                    for plex_ep in episodes:
                                                        e_id = plex_ep.episodeNumber
                                                        e_found = False
                                                        for tmdb_ep in tmdb_episodes:
                                                            if not e_found and tmdb_ep.season_number == s_id and tmdb_ep.episode_number == e_id:
                                                                #  that's the one
                                                                e_found = True
                                                                pp = (
                                                                    tmdb_ep.still_path
                                                                )

                                                                if pp is not None:
                                                                    posterURL = f"{base_url}{size_str}{pp}"
                                                                    local_file = localFilePath(
                                                                        tgt_dir,
                                                                        f"{i_rk}-S{s_id}E{e_id}",
                                                                    )

                                                                    logging.info(f"posterURL: {posterURL}")

                                                                    if LOCAL_RESET_ARCHIVE:
                                                                        if (
                                                                            local_file
                                                                            is None
                                                                            or not os.path.exists(
                                                                                local_file
                                                                            )
                                                                        ):
                                                                            ext = pathlib.Path(
                                                                                pp
                                                                            ).suffix
                                                                            local_file = os.path.join(
                                                                                tgt_dir,
                                                                                f"{i_rk}-S{s_id}E{e_id}.{ext}",
                                                                            )
                                                                            bar_and_log(bar, f"-> downloading poster: {i_t} S{s_id}E{e_id}")

                                                                        if not os.path.exists(
                                                                            local_file
                                                                        ):
                                                                            r = requests.get(
                                                                                posterURL,
                                                                                allow_redirects=True,
                                                                            )
                                                                            open(
                                                                                f"{local_file}",
                                                                                "wb",
                                                                            ).write(
                                                                                r.content
                                                                            )

                                                                        bar_and_log(bar, f"-> uploading poster: {i_t} S{s_id}E{e_id}")
                                                                        plex_ep.uploadPoster(
                                                                            filepath=local_file
                                                                        )
                                                                    else:
                                                                        bar_and_log(bar, f"-> setting poster URL: {i_t} S{s_id}E{e_id}")
                                                                        plex_ep.uploadPoster(
                                                                            url=posterURL
                                                                        )                                                        

                                        s_idx += 1
                        else:
                            bar_and_log(bar, f"-> unknown type: {i_t}")

                        if REMOVE_LABELS:
                            bar_and_log(bar, f"-> removing label {lbl}: {i_t}")
                            item.removeLabel(lbl, True)

                        # write out item_array to file.
                        with open(status_file, "a", encoding="utf-8") as sf:
                            sf.write(f"{i_rk}{os.linesep}")

                    except Exception as ex:
                        print(f'Exception processing "{i_t}": {ex}')

                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

    # delete the status file
    if status_file.is_file():
        os.remove(status_file)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processing complete in {elapsed:.2f} seconds.")
