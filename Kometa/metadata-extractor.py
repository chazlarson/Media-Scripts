#!/usr/bin/env python
import logging
from plexapi.utils import download
import os
import sys
import textwrap
import logging
from pathlib import Path
from datetime import datetime
from tmdbapis import TMDbAPIs
from pathlib import Path
from timeit import default_timer as timer
from helpers import get_ids, get_plex, load_and_upgrade_env
import yaml
from logs import setup_logger, plogger, blogger, logger
from alive_progress import alive_bar

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

setup_logger("activity_log", ACTIVITY_LOG)

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")
print(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")

if load_and_upgrade_env(env_file_path) < 0:
    exit()


def lib_type_supported(lib):
    return lib.type == "movie" or lib.type == "show"


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

logger(f"{len(ALL_LIBS)} libraries found:", "info", "a")
for lib in ALL_LIBS:
    logger(
        f"{lib.title.strip()}: {lib.type} - supported: {lib_type_supported(lib)}",
        "info",
        "a",
    )
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == "ALL_LIBRARIES":
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        if lib_type_supported(lib):
            LIB_ARRAY.append(lib.title.strip())

TMDB_KEY = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
REMOVE_LABELS = os.getenv("REMOVE_LABELS")
PLEXAPI_AUTH_SERVER_TOKEN = os.getenv("PLEXAPI_AUTH_SERVER_TOKEN")

if REMOVE_LABELS:
    lbl_array = REMOVE_LABELS.split(",")

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

local_dir = f"{os.getcwd()}/posters"

os.makedirs(local_dir, exist_ok=True)

show_dir = f"{local_dir}/shows"
movie_dir = f"{local_dir}/movies"

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(30)))
    sys.stdout.flush()


print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = "original"


def get_movie_match(item):
    imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)

    mapping_id = imdb_id if imdb_id is not None else tmdb_id
    tmpDict = {"mapping_id": mapping_id}

    match_title = item.title
    match_year = item.title

    if mapping_id is None:
        tmpDict["title"] = match_title
        tmpDict["year"] = match_year

    match_edition = item.editionTitle
    match_blank_edition = True if match_edition is None else False

    if match_blank_edition:
        tmpDict["blank_edition"] = match_blank_edition
    else:
        tmpDict["edition"] = match_edition

    return tmpDict


def get_show_match(item):
    imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)

    mapping_id = imdb_id if imdb_id is not None else tvdb_id
    tmpDict = {"mapping_id": mapping_id}

    match_title = item.title
    match_year = item.title

    if mapping_id is None:
        tmpDict["title"] = match_title
        tmpDict["year"] = match_year

    return tmpDict


def getCSV(list):
    tmpStr = ", ".join([str(item) for item in list])

    return tmpStr


def getList(list):
    list.append([str(item) for item in list])


def getDownloadBasePath():
    return f"metadata-items/{CURRENT_LIBRARY}"


def doDownload(url, savefile, savepath):
    file_path = download(
        url,
        PLEXAPI_AUTH_SERVER_TOKEN,
        filename=savefile,
        savepath=savepath,
    )

    return file_path


def getTheme(item):
    mp3Path = "TODO"
    imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)
    base_path = getDownloadBasePath()

    if imdb_id is not None:
        thm_path = f"{base_path}/imdb-{imdb_id}-{item.ratingKey}/"
    elif tmdb_id is not None:
        thm_path = f"{base_path}/tmdb-{tmdb_id}-{item.ratingKey}/"
    elif tvdb_id is not None:
        thm_path = f"{base_path}/tvdb-{imdb_id}-{item.ratingKey}/"
    else:
        thm_path = f"{base_path}/NO-MATCH-{item.ratingKey}/"

    Path(thm_path).mkdir(parents=True, exist_ok=True)

    mp3Path = doDownload(item.themeUrl, "theme.mp3", thm_path)

    # themeUrl ='http://192.168.1.11:32400/library/metadata/1262/theme/1723823327?X-Plex-Token=3rCte1jyCczPrzsAokwR'
    # save theme to /LIBRARY_NAME/IMDB-RATING/theme.mp3
    return mp3Path


def getPoster(item):
    imgPath = "TODO"
    imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)
    base_path = getDownloadBasePath()

    if imdb_id is not None:
        img_path = f"{base_path}/imdb-{imdb_id}-{item.ratingKey}/"
    elif tmdb_id is not None:
        img_path = f"{base_path}/tmdb-{tmdb_id}-{item.ratingKey}/"
    elif tvdb_id is not None:
        img_path = f"{base_path}/tvdb-{imdb_id}-{item.ratingKey}/"
    else:
        img_path = f"{base_path}/NO-MATCH-{item.ratingKey}/"

    Path(img_path).mkdir(parents=True, exist_ok=True)

    imgPath = doDownload(item.posterUrl, "poster.jpg", img_path)

    # posterUrl = 'http://192.168.1.11:32400/library/metadata/1262/thumb/1723823327?X-Plex-Token=3rCte1jyCczPrzsAokwR'
    # thumbUrl = 'http://192.168.1.11:32400/library/metadata/1262/thumb/1723823327?X-Plex-Token=3rCte1jyCczPrzsAokwR'
    # save image to /LIBRARY_NAME/IMDB-RATING/poster.jpg
    return imgPath


def getBackground(item):
    imgPath = "TODO"
    imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)
    base_path = getDownloadBasePath()

    if imdb_id is not None:
        img_path = f"{base_path}/imdb-{imdb_id}-{item.ratingKey}/"
    elif tmdb_id is not None:
        img_path = f"{base_path}/tmdb-{tmdb_id}-{item.ratingKey}/"
    elif tvdb_id is not None:
        img_path = f"{base_path}/tvdb-{imdb_id}-{item.ratingKey}/"
    else:
        img_path = f"{base_path}/NO-MATCH-{item.ratingKey}/"

    Path(img_path).mkdir(parents=True, exist_ok=True)

    imgPath = doDownload(item.artUrl, "background.jpg", img_path)

    return imgPath


def get_common_video_info(item):
    try:
        if item.type == "movie":
            matchDict = get_movie_match(item)
        else:
            matchDict = get_show_match(item)

        tmpDict = {"match": matchDict}

        tmpDict["content_rating"] = item.contentRating
        tmpDict["title"] = item.title
        if item.titleSort is not None:
            tmpDict["sort_title"] = item.titleSort
        if item.originalTitle is not None:
            tmpDict["original_title"] = item.originalTitle

        if item.originallyAvailableAt is not None:
            tmpDict["originally_available"] = item.originallyAvailableAt.strftime(
                "%Y-%m-%d"
            )

        if item.userRating is not None:
            tmpDict["user_rating"] = item.userRating
        if item.audienceRating is not None:
            tmpDict["audience_rating"] = item.audienceRating
        if item.rating is not None:
            tmpDict["critic_rating"] = item.rating
        if item.studio is not None:
            tmpDict["studio"] = item.studio
        if item.tagline is not None:
            tmpDict["tagline"] = item.tagline
        if item.summary is not None:
            tmpDict["summary"] = item.summary
        poster_path = getPoster(item)
        if poster_path is not None:
            tmpDict["file_poster"] = poster_path

        background_path = getBackground(item)
        if background_path is not None:
            tmpDict["file_background"] = background_path

        if item.type == "movie":
            if item.editionTitle is not None:
                tmpDict["edition"] = item.editionTitle
            if len(item.directors) > 0:
                tmpDict["director"] = [str(item) for item in item.directors]
            if len(item.countries) > 0:
                tmpDict["country"] = [str(item) for item in item.countries]
            if len(item.genres) > 0:
                tmpDict["genre"] = [str(item) for item in item.genres]
            if len(item.writers) > 0:
                tmpDict["writer"] = [str(item) for item in item.writers]
            if len(item.producers) > 0:
                tmpDict["producer"] = [str(item) for item in item.producers]
            if len(item.collections) > 0:
                tmpDict["collection"] = [str(item) for item in item.collections]
            if len(item.labels) > 0:
                tmpDict["label"] = [str(item) for item in item.labels]

            # metadata_language1	default, ar-SA, ca-ES, cs-CZ, da-DK, de-DE, el-GR, en-AU, en-CA, en-GB, en-US, es-ES, es-MX, et-EE, fa-IR, fi-FI, fr-CA, fr-FR, he-IL, hi-IN, hu-HU, id-ID, it-IT, ja-JP, ko-KR, lt-LT, lv-LV, nb-NO, nl-NL, pl-PL, pt-BR, pt-PT, ro-RO, ru-RU, sk-SK, sv-SE, th-TH, tr-TR, uk-UA, vi-VN, zh-CN, zh-HK, zh-TW	Movies, Shows

            if item.useOriginalTitle > -1:
                tmpDict["use_original_title"] = (
                    "yes" if item.useOriginalTitle > 0 else "no"
                )

            if item.enableCreditsMarkerGeneration > -1:
                tmpDict["credits_detection"] = (
                    "yes" if item.enableCreditsMarkerGeneration > 0 else "no"
                )

        else:
            if len(item.genres) > 0:
                tmpDict["genre"] = [str(item) for item in item.genres]
            if len(item.collections) > 0:
                tmpDict["collection"] = [str(item) for item in item.collections]
            if len(item.labels) > 0:
                tmpDict["label"] = [str(item) for item in item.labels]

            if item.episodeSort > -1:
                tmpDict["episode_sorting"] = (
                    "newest" if item.useOriginalTitle > 0 else "oldest"
                )

            episodeUnwatched = item.autoDeletionItemPolicyUnwatchedLibrary
            if episodeUnwatched != 0:
                if episodeUnwatched == -30:
                    tmpDict["keep_episodes"] = "past_30"
                if episodeUnwatched == -7:
                    tmpDict["keep_episodes"] = "past_7"
                if episodeUnwatched == -3:
                    tmpDict["keep_episodes"] = "past_3"
                if episodeUnwatched == 1:
                    tmpDict["keep_episodes"] = "latest"
                if episodeUnwatched == 3:
                    tmpDict["keep_episodes"] = "3_latest"
                if episodeUnwatched == 5:
                    tmpDict["keep_episodes"] = "5_latest"

            episodeWatched = item.autoDeletionItemPolicyWatchedLibrary
            if episodeWatched != 0:
                if episodeWatched == 1:
                    tmpDict["delete_episodes"] = "day"
                if episodeWatched == 7:
                    tmpDict["keep_episodes"] = "week"
                if episodeWatched == 100:
                    tmpDict["keep_episodes"] = "refresh"

            season_display = item.flattenSeasons
            if season_display > -1:
                if season_display == 0:
                    tmpDict["season_display"] = "hide"
                if season_display == 1:
                    tmpDict["season_display"] = "show"

            episode_ordering = item.showOrdering
            if episode_ordering is not None:
                tmpDict["episode_ordering"] = episode_ordering

            # metadata_language default, ar-SA, ca-ES, cs-CZ, da-DK, de-DE, el-GR, en-AU, en-CA, en-GB, en-US, es-ES, es-MX, et-EE, fa-IR, fi-FI, fr-CA, fr-FR, he-IL, hi-IN, hu-HU, id-ID, it-IT, ja-JP, ko-KR, lt-LT, lv-LV, nb-NO, nl-NL, pl-PL, pt-BR, pt-PT, ro-RO, ru-RU, sk-SK, sv-SE, th-TH, tr-TR, uk-UA, vi-VN, zh-CN, zh-HK, zh-TW	Movies, Shows

            if item.useOriginalTitle > -1:
                tmpDict["use_original_title"] = (
                    "yes" if item.useOriginalTitle > 0 else "no"
                )

            if item.enableCreditsMarkerGeneration > -1:
                tmpDict["credits_detection"] = (
                    "yes" if item.enableCreditsMarkerGeneration > 0 else "no"
                )

            if item.audioLanguage != "":
                tmpDict["audio_language"] = item.audioLanguage

            if item.subtitleLanguage != "":
                tmpDict["subtitle_language"] = item.subtitleLanguage

            # subtitle mode. (-1 = Account default, 0 = Manually selected, 1 = Shown with foreign audio, 2 = Always enabled).

    except Exception as e:
        print(f"Exception {e}")
        tmpDict = None

    return tmpDict


def get_season_info(season):
    try:
        tmpDict = {"title": season.title}

        if season.userRating is not None:
            tmpDict["user_rating"] = season.userRating

        if season.summary != "":
            tmpDict["summary"] = season.summary

        if len(season.collections) > 0:
            tmpDict["collection"] = [str(item) for item in season.collections]

        if len(season.labels) > 0:
            tmpDict["label"] = [str(item) for item in season.labels]

        poster_path = getPoster(season)
        if poster_path is not None:
            tmpDict["file_poster"] = poster_path

        background_path = getBackground(season)
        if background_path is not None:
            tmpDict["file_background"] = background_path

        if season.audioLanguage != "":
            tmpDict["audio_language"] = season.audioLanguage

        if season.subtitleLanguage != "":
            tmpDict["subtitle_language"] = season.subtitleLanguage

        # subtitle mode. (-1 = Account default, 0 = Manually selected, 1 = Shown with foreign audio, 2 = Always enabled).

    except Exception as e:
        print(f"Exception {e}")
        tmpDict = None

    return tmpDict


def get_episode_info(episode):
    try:
        tmpDict = {"title": episode.title}

        if episode.titleSort is not None:
            tmpDict["sort_title"] = episode.titleSort

        if episode.originallyAvailableAt is not None:
            tmpDict["originally_available"] = episode.originallyAvailableAt.strftime(
                "%Y-%m-%d"
            )

        # content_rating	Text to change Content Rating.	Movies, Shows, Episodes

        if episode.userRating is not None:
            tmpDict["user_rating"] = episode.userRating
        if episode.audienceRating is not None:
            tmpDict["audience_rating"] = episode.audienceRating
        if episode.rating is not None:
            tmpDict["critic_rating"] = episode.rating

        if season.summary != "":
            tmpDict["summary"] = season.summary

        if len(episode.directors) > 0:
            tmpDict["director"] = [str(item) for item in episode.directors]
        if len(episode.writers) > 0:
            tmpDict["writer"] = [str(item) for item in episode.writers]
        if len(episode.collections) > 0:
            tmpDict["collection"] = [str(item) for item in episode.collections]
        if len(episode.labels) > 0:
            tmpDict["label"] = [str(item) for item in episode.labels]

        if len(episode.producers) > 0:
            tmpDict["producer"] = [str(item) for item in episode.producers]

        poster_path = getPoster(item)
        if poster_path is not None:
            tmpDict["file_poster"] = poster_path

        background_path = getBackground(item)
        if background_path is not None:
            tmpDict["file_background"] = background_path

    except Exception as e:
        print(f"Exception {e}")
        tmpDict = None

    return tmpDict


item_count = 1

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        CURRENT_LIBRARY = lib
        try:
            print(f"getting items from [{lib}]...")
            items = plex.library.section(lib).all()
            item_total = len(items)
            print(f"looping over {item_total} items...")
            metadataDict = {"metadata": {}}
            with alive_bar(
                item_total, dual_line=True, title=f"Extracting metadata from {lib}"
            ) as bar:
                for item in items:
                    item_count = item_count + 1
                    try:
                        itemKey = f"{item.title} ({item.year})"
                        blogger(f"Starting {itemKey}", "info", "a", bar)
                        itemDict = get_common_video_info(item)

                        itemDict = None
                        if item.TYPE == "show":
                            itemDict = get_common_video_info(item)
                            # loop through seasons and then episodes
                            all_seasons_dict = {}
                            show_seasons = item.seasons()

                            for season in show_seasons:
                                seasonNumber = season.seasonNumber

                                this_season_dict = get_season_info(season)

                                season_episodes = season.episodes()

                                all_episodes_dict = {}

                                for episode in season_episodes:
                                    episodeNumber = episode.episodeNumber

                                    this_episode_dict = get_episode_info(episode)

                                    all_episodes_dict[episodeNumber] = this_episode_dict

                                this_season_dict["episodes"] = all_episodes_dict

                                all_seasons_dict[seasonNumber] = this_season_dict

                            itemDict["seasons"] = all_seasons_dict
                        else:
                            itemDict = get_common_video_info(item)

                        # get image data

                        if itemDict is not None:
                            metadataDict["metadata"][itemKey] = itemDict

                    except Exception as ex:
                        print(ex)

                    bar()

            with open(f"metadata-{lib}.yml", "w") as yaml_file:
                yaml.dump(
                    metadataDict,
                    yaml_file,
                    default_flow_style=False,
                    width=float("inf"),
                )

        except Exception as ex:
            progress_str = f"Problem processing {lib}; {ex}"
            plogger(progress_str, "info", "a")

end = timer()
elapsed = "{:.2f}".format(end - start)
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
