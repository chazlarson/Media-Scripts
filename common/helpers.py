from pathlib import Path
from pathvalidate import is_valid_filename, sanitize_filename
import itertools
import plexapi
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from tmdbapis import TMDbAPIs
import requests
import json
import os
from dotenv import load_dotenv, set_key, unset_key
import shutil
from PIL import Image

def has_overlay(image_path):
    kometa_overlay = False
    tcm_overlay = False

    with Image.open(image_path) as image:
        exif_tags = image.getexif()
        kometa_overlay = exif_tags is not None and 0x04bc in exif_tags and exif_tags[0x04bc] == "overlay"
        tcm_overlay = exif_tags is not None and 0x4242 in exif_tags and exif_tags[0x4242] == "titlecard"

    return kometa_overlay, tcm_overlay

def booler(thing):
    if type(thing) == str:
        thing = eval(thing)
    return bool(thing)

def redact(thing, badthing):
    return thing.replace(badthing, "(REDACTED)")

def redact(the_url, str_list):
    ret_val = the_url
    for thing in str_list:
        ret_val = ret_val.replace(thing, '[REDACTED]')
    return ret_val

def get_plex(user_token=None):
    print(f"connecting to {os.getenv('PLEXAPI_AUTH_SERVER_BASEURL')}...")
    plex = None
    try:
        if user_token is not None:
            plex = PlexServer(token=user_token)
        else:
            plex = PlexServer()
    except Unauthorized:
        print("Plex Error: Plex token is invalid")
        raise Unauthorized
    except Exception as ex: # pylint: disable=broad-exception-caught
        print(f"Plex Error: {ex.args}")
        raise ex

    return plex

IMDB_STR = "imdb://"
TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

def get_ids(the_list, TMDB_KEY):
    imdbid = None
    tmid = None
    tvid = None
    for guid in the_list:
        if IMDB_STR in guid.id:
            imdbid = guid.id.replace(IMDB_STR, "")
        if TMDB_STR in guid.id:
            tmid = guid.id.replace(TMDB_STR, "")
        if TVDB_STR in guid.id:
            tvid = guid.id.replace(TVDB_STR, "")

    return imdbid, tmid, tvid

def imdb_from_tmdb(tmdb_id, TMDB_KEY):
    tmdb = TMDbAPIs(TMDB_KEY, language="en")

    # https://api.themoviedb.org/3/movie/{movie_id}/external_ids?api_key=<<api_key>>

def validate_filename(filename):
    # return filename
    if is_valid_filename(filename):
        return filename, None
    else:
        mapping_name = sanitize_filename(filename)
        stat_string = f"Log Folder Name: {filename} is invalid using {mapping_name}"
        return mapping_name, stat_string

def get_path(library, item, season=False):
    if item.type == "collection":
        return "Collection", item.title
    else:
        if library.type == "movie":
            for media in item.media:
                for part in media.parts:
                    return Path(part.file).parent, Path(part.file).stem
        elif library.type == "show":
            for episode in item.episodes():
                for media in episode.media:
                    for part in media.parts:
                        if season:
                            return Path(part.file).parent, Path(part.file).stem
                        return (
                            Path(part.file).parent.parent,
                            Path(part.file).parent.parent.stem,
                        )

def normalise_environment(key_values):
    """Converts denormalised dict of (string -> string) pairs, where the first string
    is treated as a path into a nested list/dictionary structure
    {
        "FOO__1__BAR": "setting-1",
        "FOO__1__BAZ": "setting-2",
        "FOO__2__FOO": "setting-3",
        "FOO__2__BAR": "setting-4",
        "FIZZ": "setting-5",
    }
    to the nested structure that this represents
    {
        "FOO": [{
            "BAR": "setting-1",
            "BAZ": "setting-2",
        }, {
            "FOO": "setting-3",
            "BAR": "setting-4",
        }],
        "FIZZ": "setting-5",
    }
    If all the keys for that level parse as integers, then it's treated as a list
    with the actual keys only used for sorting
    This function is recursive, but it would be extremely difficult to hit a stack
    limit, and this function would typically by called once at the start of a
    program, so efficiency isn't too much of a concern.

    Copyright (c) 2018 Department for International Trade. All rights reserved.
    This work is licensed under the terms of the MIT license.
    For a copy, see https://opensource.org/licenses/MIT.
    """

    # Separator is chosen to
    # - show the structure of variables fairly easily;
    # - avoid problems, since underscores are usual in environment variables
    separator = "__"

    def get_first_component(key):
        return key.split(separator)[0]

    def get_later_components(key):
        return separator.join(key.split(separator)[1:])

    without_more_components = {
        key: value for key, value in key_values.items() if not get_later_components(key)
    }

    with_more_components = {
        key: value for key, value in key_values.items() if get_later_components(key)
    }

    def grouped_by_first_component(items):
        def by_first_component(item):
            return get_first_component(item[0])

        # groupby requires the items to be sorted by the grouping key
        return itertools.groupby(
            sorted(items, key=by_first_component),
            by_first_component,
        )

    def items_with_first_component(items, first_component):
        return {
            get_later_components(key): value
            for key, value in items
            if get_first_component(key) == first_component
        }

    nested_structured_dict = {
        **without_more_components,
        **{
            first_component: normalise_environment(
                items_with_first_component(items, first_component)
            )
            for first_component, items in grouped_by_first_component(
                with_more_components.items()
            )
        },
    }

    def all_keys_are_ints():
        def is_int(string):
            try:
                int(string)
                return True
            except ValueError:
                return False

        return all([is_int(key) for key, value in nested_structured_dict.items()])

    def list_sorted_by_int_key():
        return [
            value
            for key, value in sorted(
                nested_structured_dict.items(), key=lambda key_value: int(key_value[0])
            )
        ]

    return list_sorted_by_int_key() if all_keys_are_ints() else nested_structured_dict

def get_type(type):
    if type == 'movie':
        return plexapi.video.Movie
    if type == 'show':
        return plexapi.video.Show
    if type == 'episode':
        return plexapi.video.Episode
    return None

def get_size(the_lib, tgt_class=None, filter=None):
    lib_size = 0
    temp_var = []

    if filter is not None:
        temp_var = the_lib.search(libtype=tgt_class, filters=filter)
    else:
        temp_var = the_lib.search(libtype=tgt_class)

    lib_size = len(temp_var)

    return lib_size

def get_all_from_library(the_lib, tgt_class=None, filter=None):
    if tgt_class is None:
        tgt_class = the_lib.type

    lib_size = get_size(the_lib, tgt_class, filter)

    key = f"/library/sections/{the_lib.key}/all?includeGuids=1&type={utils.searchType(the_lib.type)}"
    c_start = 0
    c_size = 500
    results = []
    while lib_size is None or c_start <= lib_size:
        if filter is not None:
            results.extend(the_lib.search(libtype=tgt_class, maxresults=c_size, container_start=c_start, container_size=lib_size, filters=filter))
        else:
            results.extend(the_lib.search(libtype=tgt_class, maxresults=c_size, container_start=c_start, container_size=lib_size))

        print(f"Loaded: {len(results)}/{lib_size}", end='\r')
        c_start += c_size
        if len(results) < c_start:
            c_start = lib_size + 1
    return lib_size, results

def get_overlay_status(the_lib):
    overlay_items = the_lib.search(label="Overlay")

    ret_val = len(overlay_items) > 0

    return ret_val

def get_xml(plex_url, plex_token, lib_index):
    ssn = requests.Session()
    ssn.headers.update({'Accept': 'application/json'})
    ssn.params.update({'X-Plex-Token': plex_token})
    media_output = ssn.get(f'{plex_url}/library/sections/{lib_index}/all').json()
    return media_output

def get_xml_libraries(plex_url, plex_token):
    media_output = None
    try:
        ssn = requests.Session()
        ssn.headers.update({'Accept': 'application/json'})
        ssn.params.update({'X-Plex-Token': plex_token})
        print(f"- making request")
        raw_output = ssn.get(f'{plex_url}/library/sections/')
        if raw_output.status_code == 200:
            print(f"- success")
            media_output = raw_output.json()
    except Exception as ex: # pylint: disable=broad-exception-caught
        print(f"- problem getting libraries: {ex}")

    return media_output

def get_xml_watched(plex_url, plex_token, lib_index, lib_type='movie'):
    output_array =[]

    ssn = requests.Session()
    ssn.headers.update({'Accept': 'application/json'})
    ssn.params.update({'X-Plex-Token': plex_token})
    media_output = ssn.get(f'{plex_url}/library/sections/{lib_index}/all?viewCount>=1').json()

    if 'Metadata' in media_output['MediaContainer'].keys():
        if lib_type == 'movie':
            #library is a movie lib; loop through every movie
            movie_count = len(media_output['MediaContainer']['Metadata'])
            movie_idx = 1
            for movie in media_output['MediaContainer']['Metadata']:
                print(f"> {movie_idx:05}/{movie_count:05}", end='\r')
                if 'viewCount' in movie.keys():
                    output_array.append(movie)
                movie_idx += 1
        elif lib_type == 'show':
            #library is show lib; loop through every show
            show_count = len(media_output['MediaContainer']['Metadata'])
            show_idx = 1
            for show in media_output['MediaContainer']['Metadata']:
                print(f"> {show_idx:05}/{show_count:05}            ", end='\r')
                if 'viewedLeafCount' in show.keys() and show['viewedLeafCount'] > 0:
                    show_output = ssn.get(f'{plex_url}/library/metadata/{show["ratingKey"]}/allLeaves?viewCount>=1').json()
                    #loop through episodes of show to check if targeted season exists
                    #loop through episodes of show
                    if 'Metadata' in show_output['MediaContainer'].keys():
                        episode_list = show_output['MediaContainer']['Metadata']
                        episode_count = len(episode_list)
                        episode_idx = 1
                        for episode in episode_list:
                            print(f"> {show_idx:05}/{show_count:05} {episode_idx:05}/{episode_count:05}", end='\r')
                            if 'viewCount' in episode.keys():
                                output_array.append(episode)
                            episode_idx += 1
                show_idx += 1

    return output_array

def get_media_details(plex_url, plex_token, rating_key):
    output_array =[]

    ssn = requests.Session()
    ssn.headers.update({'Accept': 'application/json'})
    ssn.params.update({'X-Plex-Token': plex_token})
    media_output = ssn.get(f'{plex_url}/library/metadata/{rating_key}').json()

    return media_output

def get_all_watched(plex, the_lib):
    results = the_lib.search(unwatched=False)
    return results

def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)

ALPHABET = []
NUMBERS = []

for c in char_range('a', 'z'):
    ALPHABET.append(c)

for c in char_range('0', '9'):
    NUMBERS.append(c)

def remove_articles(thing):
    if thing.startswith('The '):
        thing = thing.replace('The ','')
    if thing.startswith('A '):
        thing = thing.replace('A ','')
    if thing.startswith('An '):
        thing = thing.replace('An ','')
    if thing.startswith('El '):
        thing = thing.replace('El ','')

    return thing

def get_letter_dir(thing):
    ret_val = "Other"

    thing = remove_articles(thing)

    first_char = thing[0]

    if first_char.lower() in ALPHABET:
        ret_val = first_char.upper()
    else:
        if first_char in NUMBERS:
            ret_val = first_char

    return ret_val

def load_and_upgrade_env(file_path):
    status = 0

    if os.path.exists(file_path):
        load_dotenv(dotenv_path=file_path, override=True)
    else:
        print(f"No environment [.env] file.  Creating base file.")
        if os.path.exists('.env.example'):
            src_file = os.path.join('.', '.env.example')
            tgt_file = os.path.join('.','.env')
            shutil.copyfile(src_file, tgt_file)
            print(f"Please edit .env file to suit and rerun script.")
        else:
            print(f"No example [.env.example] file.  Cannot create base file.")
        status = -1

    plex_url = os.getenv("PLEX_URL")
    plex_token = os.getenv("PLEX_TOKEN")

    if plex_url is not None:
        # Add the PLEXAPI env vars
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_PLEXAPI_TIMEOUT", value_to_set="360")

        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_AUTH_SERVER_BASEURL", value_to_set=PLEX_URL)
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_AUTH_SERVER_TOKEN", value_to_set=PLEX_TOKEN)
        unset_key(dotenv_path=file_path, key_to_unset="PLEX_URL", quote_mode='always', encoding='utf-8')
        unset_key(dotenv_path=file_path, key_to_unset="PLEX_TOKEN", quote_mode='always', encoding='utf-8')

        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_LOG_BACKUP_COUNT", value_to_set='3')
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_LOG_FORMAT", value_to_set="%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s")
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_LOG_LEVEL", value_to_set="INFO")
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_LOG_PATH", value_to_set="plexapi.log")
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_LOG_ROTATE_BYTES", value_to_set='512000')
        set_key(dotenv_path=file_path, key_to_set="PLEXAPI_LOG_SHOW_SECRETS", value_to_set="false")

        # and load the new file
        load_dotenv(dotenv_path=file_path)
        status = 1

    if os.getenv("PLEXAPI_AUTH_SERVER_BASEURL") is None or os.getenv("PLEXAPI_AUTH_SERVER_BASEURL") == 'https://plex.domain.tld':
        print(f"You must specify PLEXAPI_AUTH_SERVER_BASEURL in the .env file.")
        status = -1

    if os.getenv("PLEXAPI_AUTH_SERVER_TOKEN") is None or os.getenv("PLEXAPI_AUTH_SERVER_TOKEN") == 'PLEX-TOKEN':
        print(f"You must specify PLEXAPI_AUTH_SERVER_TOKEN in the .env file.")
        status = -1

    return status
