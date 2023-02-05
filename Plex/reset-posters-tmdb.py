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
CLEAR_RESET_STATUS = os.getenv("CLEAR_RESET_STATUS")
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

def plex_knows_this_image(item, source, path):
    logging.info(f"Retrieving posters for {item}")
    item.reload()
    attempts = 0
    while attempts < 5:
        try:
            list_of_posters = item.posters()
            logging.info(f"Checking {len(list_of_posters)} posters")
            for poster in list_of_posters:
                if poster.provider == source:
                    if poster.key == path:
                        return poster
            attempts = 6
        except Exception as ex:
            logging.info(f'Exception processing "{item}": {ex}')
            attempts += 1

    return None

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
                imdbid, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)
                try:
                    bar_and_log(bar, f"-> starting: {i_t}")
                    pp = None
                    local_file = None
                    tmdb_item = None
                    if tmdb_id:
                        tmdb_item = tmdb.tv_show(tmdb_id)
                    else:
                        tmdb_search = (
                            tmdb.find_by_id(tvdb_id=tvdb_id)
                        )
                        if len(tmdb_search.tv_results) > 0:
                            tmdb_item = tmdb_search.tv_results[0]
                    
                    if item.TYPE == "show":
                        tgt_dir = show_dir
                    else:
                        tgt_dir = movie_dir
                        tmdb_item = tmdb.movie(tmdb_id)

                    if LOCAL_RESET_ARCHIVE:
                        local_file = localFilePath(tgt_dir, i_rk)
                        pp = local_file
                    if local_file is None:
                        try:
                            tmdb_item.reload()
                            pp = tmdb_item.poster_path
                        except:
                            pp = None

                    if pp is not None:
                        seriesPosterURL = f"{base_url}{size_str}{pp}"
                        logging.info(f"seriesPosterURL: {seriesPosterURL}")

                    if id_array.count(f"{i_rk}-top") == 0:
                        
                        if pp is not None:
                            bar_and_log(bar, f"-> checking if Plex knows about this image: {seriesPosterURL}")
                            pp_o = plex_knows_this_image(item, 'tmdb', seriesPosterURL)
                            if pp_o is not None:
                                print_and_log(f"One of Plex' posters for {i_t}: {seriesPosterURL}")

                            if LOCAL_RESET_ARCHIVE:
                                if local_file is None or not os.path.exists(local_file):
                                    ext = pathlib.Path(pp).suffix
                                    local_file = os.path.join(tgt_dir, f"{i_rk}.{ext}")
                                    bar_and_log(bar, f"-> downloading poster: {i_t}")

                                if not os.path.exists(local_file):
                                    dl_URL = seriesPosterURL
                                    if pp_o is not None:
                                        dl_URL = pp_o.key

                                    bar_and_log(bar, f"-> requesting series: {dl_URL}")
                                    r = requests.get(
                                        dl_URL, allow_redirects=True
                                    )
                                    open(f"{local_file}", "wb").write(r.content)


                                if pp_o is not None:
                                    bar_and_log(bar, f"-> SETTING poster: {i_t}")
                                    item.setPoster(pp_o)
                                else:
                                    bar_and_log(bar, f"-> uploading poster: {i_t}")
                                    item.uploadPoster(filepath=local_file)
                            else:
                                bar_and_log(bar, f"-> setting series poster URL: {i_t}")
                                if pp_o is not None:
                                    bar_and_log(bar, f"-> SETTING poster: {i_t}")
                                    item.setPoster(pp_o)
                                else:
                                    bar_and_log(bar, f"-> uploading poster: {i_t}")
                                    item.uploadPoster(url=seriesPosterURL)

                            id_array.append(f"{i_rk}-top")

                            with open(status_file, "a", encoding="utf-8") as sf:
                                sf.write(f"{i_rk}-top{os.linesep}")

                    else:
                        bar_and_log(bar, f"Skipping {i_t}-{i_rk}: already reset")

                    if item.TYPE == "show" and tmdb_item is not None:

                        if RESET_SEASONS:
                            # get seasons
                            seasons = item.seasons()
                            tmdb_seasons = tmdb_item.seasons

                            # loop over all:
                            for s in seasons:
                                s_id = s.seasonNumber
                                s_rk = s.ratingKey
                                s_found = False

                                for ss in tmdb_seasons:
                                    ss.reload()

                                    if ss.season_number == s_id and not s_found:
                                        s_found = True

                                        if id_array.count(f"{s_rk}") == 0:
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
                                            logging.info(f"season posterURL: {posterURL}")

                                            bar_and_log(bar, f"-> checking if Plex knows about this image: {posterURL}")
                                            pp_o = plex_knows_this_image(s, 'tmdb', posterURL)
                                            if pp_o is not None:
                                                print_and_log(f"One of Plex' posters for {i_t}: {posterURL}")

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
                                                    dl_URL = posterURL
                                                    if pp_o is not None:
                                                        dl_URL = pp_o.key

                                                    bar_and_log(bar, f"-> requesting season: {dl_URL}")
                                                    r = requests.get(
                                                        dl_URL, allow_redirects=True
                                                    )
                                                    open(f"{local_file}", "wb").write(r.content)

                                                if pp_o is not None:
                                                    bar_and_log(bar, f"-> SETTING poster: {i_t} S{s_id}")
                                                    s.setPoster(pp_o)
                                                else:
                                                    bar_and_log(bar, f"-> uploading poster: {i_t} S{s_id}")
                                                    s.uploadPoster(filepath=local_file)
                                            else:
                                                if pp_o is not None:
                                                    bar_and_log(bar, f"-> SETTING poster: {i_t} S{s_id}")
                                                    s.setPoster(pp_o)
                                                else:
                                                    bar_and_log(bar, f"-> uploading poster: {i_t} S{s_id}")
                                                    s.uploadPoster(url=posterURL)
                                            
                                            id_array.append(f"{s_rk}")

                                            with open(status_file, "a", encoding="utf-8") as sf:
                                                sf.write(f"{s_rk}{os.linesep}")

                                        else:
                                            bar_and_log(bar, f"Skipping {i_t}-{i_rk} Season {s_id}-{s_rk}: already reset")


                                        if RESET_EPISODES:
                                            # get episodes
                                            bar_and_log(bar, f"getting TMDB episodes for season: {ss.season_number}")
                                            tmdb_episodes = ss.episodes
                                            bar_and_log(bar, f"getting Plex episodes for season: {s_id}")
                                            episodes = s.episodes()

                                            bar_and_log(bar, f"Looping over Plex episodes:")
                                            for plex_ep in episodes:
                                                e_id = plex_ep.episodeNumber
                                                e_rk = plex_ep.ratingKey
                                                e_found = False
                                                if id_array.count(f"{e_rk}") == 0:
                                                    for tmdb_ep in tmdb_episodes:
                                                        t_s_id = None
                                                        t_e_id = None
                                                        try:
                                                            t_s_id = tmdb_ep.season_number
                                                        except Exception as ex:
                                                            bar_and_log(bar, f"-> EXCEPTION getting episode season ID: {ex}")
                                                        try:
                                                            t_e_id = tmdb_ep.episode_number
                                                        except Exception as ex:
                                                            bar_and_log(bar, f"-> EXCEPTION getting episode ID: {ex}")

                                                        if t_s_id is not None and t_e_id is not None:
                                                            if not e_found and t_s_id == s_id and t_e_id == e_id:
                                                                bar_and_log(bar, f"Found episode S{s_id} E{e_id}")
                                                                #  that's the one
                                                                e_found = True
                                                                pp = tmdb_ep.still_path
                                                                bar_and_log(bar, f"-> poster_path: {pp}")

                                                                if pp is not None:
                                                                    posterURL = f"{base_url}{size_str}{pp}"
                                                                    local_file = localFilePath(
                                                                        tgt_dir,
                                                                        f"{i_rk}-S{s_id}E{e_id}",
                                                                    )

                                                                    bar_and_log(bar, f"-> checking if Plex knows about that image")
                                                                    pp_o = plex_knows_this_image(plex_ep, 'tmdb', posterURL)
                                                                    if pp_o is not None:
                                                                        logging.info(f"One of Plex' posters for {i_t}: {posterURL}")

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
                                                                            dl_URL = posterURL
                                                                            if pp_o is not None:
                                                                                dl_URL = pp_o.key

                                                                            bar_and_log(bar, f"-> requesting episode: {dl_URL}")
                                                                            r = requests.get(
                                                                                dl_URL, allow_redirects=True
                                                                            )
                                                                            open(f"{local_file}", "wb").write(r.content)

                                                                        if pp_o is not None:
                                                                            bar_and_log(bar, f"-> SETTING episode poster: {i_t} S{s_id}E{e_id}")
                                                                            s.setPoster(pp_o)
                                                                        else:
                                                                            bar_and_log(bar, f"-> uploading episode poster: {i_t} S{s_id}E{e_id}")
                                                                            s.uploadPoster(filepath=local_file)
                                                                    else:
                                                                        if pp_o is not None:
                                                                            bar_and_log(bar, f"-> setting episode poster URL: {i_t} S{s_id}E{e_id}")
                                                                            plex_ep.setPoster(pp_o)
                                                                        else:
                                                                            bar_and_log(bar, f"-> setting episode poster URL: {i_t} S{s_id}E{e_id}")
                                                                            plex_ep.uploadPoster(url=posterURL)

                                                                    id_array.append(f"{e_rk}")

                                                                    with open(status_file, "a", encoding="utf-8") as sf:
                                                                        sf.write(f"{e_rk}{os.linesep}")

                                                        else:
                                                            bar_and_log(bar, f"-> Couldn't get some episode details")
                                                else:
                                                    bar_and_log(bar, f"Skipping {i_t}-{i_rk} Season {s_id}-{s_rk} Episode {e_id}-{e_rk}: already reset")

                    if REMOVE_LABELS:
                        bar_and_log(bar, f"-> removing label {lbl}: {i_t}")
                        item.removeLabel(lbl, True)

                except Exception as ex:
                    print_and_log(f'Exception processing "{i_t}": {ex}')
                    # there's a 500 in the season poster upload

                bar()

    # delete the status file
    if CLEAR_RESET_STATUS:
        if status_file.is_file():
            os.remove(status_file)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processing complete in {elapsed:.2f} seconds.")
