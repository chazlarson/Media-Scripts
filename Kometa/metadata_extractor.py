""" Module exports Plex metadata for Kometa """
#!/usr/bin/env python
import logging
from datetime import datetime
import os
import sys
from pathlib import Path
from timeit import default_timer as timer
from helpers import get_ids, get_plex, load_and_upgrade_env, get_all_from_library
import yaml
from logs import setup_logger, plogger, blogger, logger
from alive_progress import alive_bar
from plexapi.utils import download
from tmdbapis import TMDbAPIs

# import tvdb_v4_official

start = timer()

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

# // TODO: improved error handling
# // TODO: TV Theme tunes
# // TODO: Process Music libraries
# // TODO: Process Photo libraries
# // TODO: Deal correctly with multi-line summaries

# DONE 0.2.0: complete implementation
# DONE 0.2.1: Use alivebar, support multiple libraries
# DONE 0.2.2: Actually fill in the show match attribute

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.2.2"

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

START_STR = f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}"
logging.info(START_STR)
print(START_STR)

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

def lib_type_supported(tgt_lib):
    """docstring placeholder"""
    return tgt_lib.type in ('movie', 'show')

plex = get_plex()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")

LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

CURRENT_LIBRARY = ""

if LIBRARY_NAMES:
    LIB_ARRAY = []
    LIB_LIST = LIBRARY_NAMES.split(",")
    for s in LIB_LIST:
        LIB_ARRAY.append(s.strip())
else:
    LIB_ARRAY = [LIBRARY_NAME]

ALL_LIBS = plex.library.sections()
ALL_LIB_NAMES = []

logger(f"{len(ALL_LIBS)} libraries found:", 'info', 'a')
for lib in ALL_LIBS:
    logger(f"{lib.title.strip()}: {lib.type} - supported: {lib_type_supported(lib)}", 'info', 'a')
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        if lib_type_supported(lib):
            LIB_ARRAY.append(lib.title.strip())

tmdb_key = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
REMOVE_LABELS = os.getenv("REMOVE_LABELS")
PLEXAPI_AUTH_SERVER_TOKEN = os.getenv("PLEXAPI_AUTH_SERVER_TOKEN")

if REMOVE_LABELS:
    lbl_array = REMOVE_LABELS.split(",")

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(tmdb_key, language="en")

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

local_dir = f"{os.getcwd()}/posters"

os.makedirs(local_dir, exist_ok=True)

SHOW_DIR = f"{local_dir}/shows"
MOVIE_DIR = f"{local_dir}/movies"

os.makedirs(SHOW_DIR, exist_ok=True)
os.makedirs(MOVIE_DIR, exist_ok=True)

print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
SIZE_STR = "original"

def get_movie_match(tgt_item):
    """docstring placeholder"""
    imdb_id, tmdb_id, tvdb_id = get_ids(tgt_item.guids) # pylint: disable=unused-variable

    mapping_id = imdb_id if imdb_id is not None else tmdb_id
    tmp_dict = {'mapping_id':mapping_id}

    match_title = tgt_item.title
    match_year = tgt_item.title

    if mapping_id is None:
        tmp_dict['title'] = match_title
        tmp_dict['year'] = match_year

    match_edition = tgt_item.editionTitle
    match_blank_edition = match_edition is None

    if match_blank_edition:
        tmp_dict['blank_edition'] = match_blank_edition
    else:
        tmp_dict['edition'] = match_edition

    return tmp_dict

def get_show_match(tgt_item):
    """docstring placeholder"""
    imdb_id, tmdb_id, tvdb_id = get_ids(tgt_item.guids) # pylint: disable=unused-variable

    mapping_id = imdb_id if imdb_id is not None else tvdb_id
    tmp_dict = {'mapping_id':mapping_id}

    match_title = tgt_item.title
    match_year = tgt_item.title

    if mapping_id is None:
        tmp_dict['title'] = match_title
        tmp_dict['year'] = match_year

    return tmp_dict

def get_csv(src_list):
    """docstring placeholder"""
    tmp_str = ', '.join([str(item) for item in src_list])

    return tmp_str

def get_list(src_list):
    """docstring placeholder"""
    list.append([str(item) for item in src_list])

def get_download_base_path():
    """docstring placeholder"""
    return f"metadata-items/{CURRENT_LIBRARY}"

def do_download(url, savefile, savepath):
    """docstring placeholder"""
    if url is not None:
        file_path = download(
            url,
            PLEXAPI_AUTH_SERVER_TOKEN,
            filename=savefile,
            savepath=savepath,
            )
    else:
        file_path = None

    return file_path

def get_theme(tgt_item):
    """docstring placeholder"""
    mp3_path = "TODO"
    imdb_id, tmdb_id, tvdb_id = get_ids(tgt_item.guids)
    base_path = get_download_base_path()

    if imdb_id is not None:
        thm_path = f"{base_path}/imdb-{imdb_id}-{tgt_item.ratingKey}/"
    elif tmdb_id is not None:
        thm_path = f"{base_path}/tmdb-{tmdb_id}-{tgt_item.ratingKey}/"
    elif tvdb_id is not None:
        thm_path = f"{base_path}/tvdb-{imdb_id}-{tgt_item.ratingKey}/"
    else:
        thm_path = f"{base_path}/NO-MATCH-{tgt_item.ratingKey}/"

    Path(thm_path).mkdir(parents=True, exist_ok=True)

    mp3_path = do_download(tgt_item.themeUrl, 'theme.mp3', thm_path)

    # themeUrl ='http://192.168.1.11:32400/library/metadata/1262/theme/1723823327?X-Plex-Token=3rCte1jyCczPrzsAokwR'
    # save theme to /LIBRARY_NAME/IMDB-RATING/theme.mp3
    return mp3_path

def get_poster(tgt_item):
    """docstring placeholder"""
    img_path = "TODO"
    imdb_id, tmdb_id, tvdb_id = get_ids(tgt_item.guids)
    base_path = get_download_base_path()

    if imdb_id is not None:
        img_path = f"{base_path}/imdb-{imdb_id}-{tgt_item.ratingKey}/"
    elif tmdb_id is not None:
        img_path = f"{base_path}/tmdb-{tmdb_id}-{tgt_item.ratingKey}/"
    elif tvdb_id is not None:
        img_path = f"{base_path}/tvdb-{imdb_id}-{tgt_item.ratingKey}/"
    else:
        img_path = f"{base_path}/NO-MATCH-{tgt_item.ratingKey}/"

    Path(img_path).mkdir(parents=True, exist_ok=True)

    img_path = do_download(tgt_item.posterUrl, 'poster.jpg', img_path)

    # posterUrl = 'http://192.168.1.11:32400/library/metadata/1262/thumb/1723823327?X-Plex-Token=3rCte1jyCczPrzsAokwR'
    # thumbUrl = 'http://192.168.1.11:32400/library/metadata/1262/thumb/1723823327?X-Plex-Token=3rCte1jyCczPrzsAokwR'
    # save image to /LIBRARY_NAME/IMDB-RATING/poster.jpg
    return img_path

def get_background(tgt_item):
    """docstring placeholder"""
    img_path = "TODO"
    imdb_id, tmdb_id, tvdb_id = get_ids(tgt_item.guids)
    base_path = get_download_base_path()

    if imdb_id is not None:
        img_path = f"{base_path}/imdb-{imdb_id}-{tgt_item.ratingKey}/"
    elif tmdb_id is not None:
        img_path = f"{base_path}/tmdb-{tmdb_id}-{tgt_item.ratingKey}/"
    elif tvdb_id is not None:
        img_path = f"{base_path}/tvdb-{imdb_id}-{tgt_item.ratingKey}/"
    else:
        img_path = f"{base_path}/NO-MATCH-{tgt_item.ratingKey}/"

    Path(img_path).mkdir(parents=True, exist_ok=True)

    img_path = do_download(tgt_item.artUrl, 'background.jpg', img_path)

    return img_path

def get_common_video_info(tgt_item): # pylint: disable=too-many-branches, too-many-statements
    """docstring placeholder"""
    try:
        if tgt_item.type == 'movie':
            match_dict = get_movie_match(tgt_item)
        else:
            match_dict = get_show_match(tgt_item)

        tmp_dict = {'match':match_dict}

        tmp_dict['content_rating'] = tgt_item.contentRating
        tmp_dict['title'] = tgt_item.title
        if tgt_item.titleSort is not None:
            tmp_dict['sort_title'] = tgt_item.titleSort
        if tgt_item.originalTitle is not None:
            tmp_dict['original_title'] = tgt_item.originalTitle

        if tgt_item.originallyAvailableAt is not None:
            tmp_dict['originally_available'] = tgt_item.originallyAvailableAt.strftime("%Y-%m-%d")

        if tgt_item.userRating is not None:
            tmp_dict['user_rating'] = tgt_item.userRating
        if tgt_item.audienceRating is not None:
            tmp_dict['audience_rating'] = tgt_item.audienceRating
        if tgt_item.rating is not None:
            tmp_dict['critic_rating'] = tgt_item.rating
        if tgt_item.studio is not None:
            tmp_dict['studio'] = tgt_item.studio
        if tgt_item.tagline is not None:
            tmp_dict['tagline'] = tgt_item.tagline
        if tgt_item.summary is not None:
            tmp_dict['summary'] = tgt_item.summary
        poster_path = get_poster(tgt_item)
        if poster_path is not None:
            tmp_dict['file_poster'] = poster_path

        background_path = get_background(tgt_item)
        if background_path is not None:
            tmp_dict['file_background'] = background_path

        if tgt_item.type == 'movie':
            if tgt_item.editionTitle is not None:
                tmp_dict['edition'] = tgt_item.editionTitle
            if len(tgt_item.directors) > 0:
                tmp_dict['director'] = [str(s_item) for s_item in tgt_item.directors]
            if len(tgt_item.countries) > 0:
                tmp_dict['country'] = [str(s_item) for s_item in tgt_item.countries]
            if len(tgt_item.genres) > 0:
                tmp_dict['genre'] = [str(s_item) for s_item in tgt_item.genres]
            if len(tgt_item.writers) > 0:
                tmp_dict['writer'] = [str(s_item) for s_item in tgt_item.writers]
            if len(tgt_item.producers) > 0:
                tmp_dict['producer'] = [str(s_item) for s_item in tgt_item.producers]
            if len(tgt_item.collections) > 0:
                tmp_dict['collection'] = [str(s_item) for s_item in tgt_item.collections]
            if len(tgt_item.labels) > 0:
                tmp_dict['label'] = [str(s_item) for s_item in tgt_item.labels]

            # metadata_language1
            # default, ar-SA, ca-ES, cs-CZ, da-DK, de-DE, el-GR, en-AU,
            # en-CA, en-GB, en-US, es-ES, es-MX, et-EE, fa-IR, fi-FI, fr-CA,
            # fr-FR, he-IL, hi-IN, hu-HU, id-ID, it-IT, ja-JP, ko-KR, lt-LT,
            # lv-LV, nb-NO, nl-NL, pl-PL, pt-BR, pt-PT, ro-RO, ru-RU, sk-SK,
            # sv-SE, th-TH, tr-TR, uk-UA, vi-VN, zh-CN, zh-HK, zh-TW
            # Movies, Shows

            if tgt_item.useOriginalTitle > -1:
                tmp_dict['use_original_title'] = 'yes' if tgt_item.useOriginalTitle > 0 else 'no'

            if tgt_item.enableCreditsMarkerGeneration > -1:
                tmp_dict['credits_detection'] = 'yes' if tgt_item.enableCreditsMarkerGeneration > 0 else 'no'

        else:
            if len(tgt_item.genres) > 0:
                tmp_dict['genre'] = [str(s_item) for s_item in tgt_item.genres]
            if len(tgt_item.collections) > 0:
                tmp_dict['collection'] = [str(s_item) for s_item in tgt_item.collections]
            if len(tgt_item.labels) > 0:
                tmp_dict['label'] = [str(s_item) for s_item in tgt_item.labels]

            if tgt_item.episodeSort > -1:
                tmp_dict['episode_sorting'] = 'newest' if tgt_item.useOriginalTitle > 0 else 'oldest'

            episode_unwatched = tgt_item.autoDeletionItemPolicyUnwatchedLibrary
            if episode_unwatched != 0:
                if episode_unwatched == -30:
                    tmp_dict['keep_episodes'] = 'past_30'
                if episode_unwatched == -7:
                    tmp_dict['keep_episodes'] = 'past_7'
                if episode_unwatched == -3:
                    tmp_dict['keep_episodes'] = 'past_3'
                if episode_unwatched == 1:
                    tmp_dict['keep_episodes'] = 'latest'
                if episode_unwatched == 3:
                    tmp_dict['keep_episodes'] = '3_latest'
                if episode_unwatched == 5:
                    tmp_dict['keep_episodes'] = '5_latest'

            episode_watched = tgt_item.autoDeletionItemPolicyWatchedLibrary
            if episode_watched != 0:
                if episode_watched == 1:
                    tmp_dict['delete_episodes'] = 'day'
                if episode_watched == 7:
                    tmp_dict['keep_episodes'] = 'week'
                if episode_watched == 100:
                    tmp_dict['keep_episodes'] = 'refresh'

            season_display = tgt_item.flattenSeasons
            if season_display > -1:
                if season_display == 0:
                    tmp_dict['season_display'] = 'hide'
                if season_display == 1:
                    tmp_dict['season_display'] = 'show'

            episode_ordering = tgt_item.showOrdering
            if episode_ordering is not None:
                tmp_dict['episode_ordering'] = episode_ordering

            # metadata_language
            # default, ar-SA, ca-ES, cs-CZ, da-DK, de-DE, el-GR, en-AU,
            # en-CA, en-GB, en-US, es-ES, es-MX, et-EE, fa-IR, fi-FI, fr-CA,
            # fr-FR, he-IL, hi-IN, hu-HU, id-ID, it-IT, ja-JP, ko-KR, lt-LT,
            # lv-LV, nb-NO, nl-NL, pl-PL, pt-BR, pt-PT, ro-RO, ru-RU, sk-SK,
            # sv-SE, th-TH, tr-TR, uk-UA, vi-VN, zh-CN, zh-HK, zh-TW
            # Movies, Shows

            if tgt_item.useOriginalTitle > -1:
                tmp_dict['use_original_title'] = 'yes' if tgt_item.useOriginalTitle > 0 else 'no'

            if tgt_item.enableCreditsMarkerGeneration > -1:
                tmp_dict['credits_detection'] = 'yes' if tgt_item.enableCreditsMarkerGeneration > 0 else 'no'

            if tgt_item.audioLanguage != '':
                tmp_dict['audio_language'] = tgt_item.audioLanguage

            if tgt_item.subtitleLanguage != '':
                tmp_dict['subtitle_language'] = tgt_item.subtitleLanguage

            # subtitle mode. (-1 = Account default, 0 = Manually selected, 1 = Shown with foreign audio, 2 = Always enabled).

    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Exception {e}")
        tmp_dict = None

    return tmp_dict

def get_season_info(tgt_season):
    """docstring placeholder"""
    try:
        tmp_dict = {'title':tgt_season.title}

        if tgt_season.userRating is not None:
            tmp_dict['user_rating'] = tgt_season.userRating

        if tgt_season.summary != '':
            tmp_dict['summary'] = tgt_season.summary

        if len(tgt_season.collections) > 0:
            tmp_dict['collection'] = [str(sub_item) for sub_item in tgt_season.collections]

        if len(tgt_season.labels) > 0:
            tmp_dict['label'] = [str(sub_item) for sub_item in tgt_season.labels]

        poster_path = get_poster(tgt_season)
        if poster_path is not None:
            tmp_dict['file_poster'] = poster_path

        background_path = get_background(tgt_season)
        if background_path is not None:
            tmp_dict['file_background'] = background_path

        if tgt_season.audioLanguage != '':
            tmp_dict['audio_language'] = tgt_season.audioLanguage

        if tgt_season.subtitleLanguage != '':
            tmp_dict['subtitle_language'] = tgt_season.subtitleLanguage

        # subtitle mode. (-1 = Account default, 0 = Manually selected, 1 = Shown with foreign audio, 2 = Always enabled).

    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Exception {e}")
        tmp_dict = None

    return tmp_dict

def get_episode_info(tgt_episode): # pylint: disable=too-many-branches
    """docstring placeholder"""
    try:
        tmp_dict = {'title':tgt_episode.title}

        if tgt_episode.titleSort is not None:
            tmp_dict['sort_title'] = tgt_episode.titleSort

        if tgt_episode.originallyAvailableAt is not None:
            tmp_dict['originally_available'] = tgt_episode.originallyAvailableAt.strftime("%Y-%m-%d")

# content_rating	Text to change Content Rating.	Movies, Shows, Episodes

        if tgt_episode.userRating is not None:
            tmp_dict['user_rating'] = tgt_episode.userRating
        if tgt_episode.audienceRating is not None:
            tmp_dict['audience_rating'] = tgt_episode.audienceRating
        if tgt_episode.rating is not None:
            tmp_dict['critic_rating'] = tgt_episode.rating

        if tgt_episode.summary  != '':
            tmp_dict['summary'] = tgt_episode.summary

        if len(tgt_episode.directors) > 0:
            tmp_dict['director'] = [str(item) for item in tgt_episode.directors]
        if len(tgt_episode.writers) > 0:
            tmp_dict['writer'] = [str(item) for item in tgt_episode.writers]
        if len(tgt_episode.collections) > 0:
            tmp_dict['collection'] = [str(item) for item in tgt_episode.collections]
        if len(tgt_episode.labels) > 0:
            tmp_dict['label'] = [str(item) for item in tgt_episode.labels]

        if len(tgt_episode.producers) > 0:
            tmp_dict['producer'] = [str(item) for item in tgt_episode.producers]

        poster_path = get_poster(tgt_episode)
        if poster_path is not None:
            tmp_dict['file_poster'] = poster_path

        background_path = get_background(tgt_episode)
        if background_path is not None:
            tmp_dict['file_background'] = background_path

    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Exception {e}")
        tmp_dict = None

    return tmp_dict

ITEM_COUNT = 1

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        CURRENT_LIBRARY = lib
        try:
            print(f"getting items from [{lib}]...")
            the_lib = plex.library.section(lib)
            ITEM_COUNT, items = get_all_from_library(the_lib, None, None)
            # item_total = len(items)
            print(f"looping over {ITEM_COUNT} items...")
            metadataDict = {'metadata':{}}
            with alive_bar(ITEM_COUNT, dual_line=True, title=f"Extracting metadata from {lib}") as bar:
                for item in items:
                    ITEM_COUNT = ITEM_COUNT + 1
                    try:
                        ITEM_KEY = f"{item.title} ({item.year})"
                        blogger(f"Starting {ITEM_KEY}", 'info', 'a', bar)
                        itemDict = get_common_video_info(item)

                        ITEM_DICT = None
                        if item.TYPE == "show":
                            ITEM_DICT = get_common_video_info(item)
                            # loop through seasons and then episodes
                            all_seasons_dict = {}
                            show_seasons = item.seasons()

                            for season in show_seasons:
                                seasonNumber = season.seasonNumber

                                blogger(f"Processing {ITEM_KEY} season {seasonNumber}", 'info', 'a', bar)

                                this_season_dict = get_season_info(season)

                                season_episodes = season.episodes()

                                all_episodes_dict = {}

                                for episode in season_episodes:
                                    episodeNumber = episode.episodeNumber

                                    blogger(f"Processing {ITEM_KEY} S{seasonNumber}E{episodeNumber}", 'info', 'a', bar)

                                    this_episode_dict = get_episode_info(episode)

                                    all_episodes_dict[episodeNumber] = this_episode_dict

                                this_season_dict['episodes'] = all_episodes_dict

                                all_seasons_dict[seasonNumber] = this_season_dict

                            ITEM_DICT['seasons'] = all_seasons_dict
                        else:
                            ITEM_DICT = get_common_video_info(item)

                        # get image data

                        if ITEM_DICT is not None:
                            metadataDict['metadata'][ITEM_KEY] = ITEM_DICT

                    except Exception as ex: # pylint: disable=broad-exception-caught
                        print(ex)

                    bar() # pylint: disable=not-callable

            with open(f"metadata-{lib}.yml", 'w', encoding="utf-8") as yaml_file:
                yaml.dump(metadataDict, yaml_file, default_flow_style=False, width=float("inf"))

        except Exception as ex: # pylint: disable=broad-exception-caught
            PROGRESS_STR = f"Problem processing {lib}; {ex}"
            plogger(PROGRESS_STR, 'info', 'a')

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {ITEM_COUNT - 1} items in {elapsed:0.2f} seconds.")
