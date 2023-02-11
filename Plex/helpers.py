from pathlib import Path
from pathvalidate import is_valid_filename, sanitize_filename
import itertools
import plexapi
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from tmdbapis import TMDbAPIs



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
    
def get_plex(PLEX_URL, PLEX_TOKEN):
    print(f"connecting to {PLEX_URL}...")
    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN, timeout=360)
    except Unauthorized:
        print("Plex Error: Plex token is invalid")
        exit()
    except Exception as ex:
        print(f"Plex Error: {ex.args}")
        exit()
    return plex

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

def get_ids(theList, TMDB_KEY):
    imdbid = None
    tmid = None
    tvid = None
    for guid in theList:
        if imdb_str in guid.id:
            imdbid = guid.id.replace(imdb_str, "")
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str, "")
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str, "")

    return imdbid, tmid, tvid

def imdb_from_tmdb(tmdb_id, TMDB_KEY):
    tmdb = TMDbAPIs(TMDB_KEY, language="en")

    # https://api.themoviedb.org/3/movie/{movie_id}/external_ids?api_key=<<api_key>>


def validate_filename(filename):
    if is_valid_filename(filename):
        return filename, None
    else:
        mapping_name = sanitize_filename(filename)
        stat_string = f"Log Folder Name: {filename} is invalid using {mapping_name}"
        return mapping_name, stat_string

def getPath(library, item, season=False):
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

def get_all(plex, the_lib, tgt_class=None, filter=None):
    lib_size = the_lib.totalViewSize()
    lib_type = get_type(the_lib.type)
    item_class = the_lib.type
    
    if tgt_class is not None:
        item_class = tgt_class
        lib_size = the_lib.totalViewSize(libtype=tgt_class)
    
    key = f"/library/sections/{the_lib.key}/all?includeGuids=1&type={utils.searchType(the_lib.type)}"
    c_start = 0
    c_size = 500
    results = []
    while lib_size is None or c_start <= lib_size:
        if filter is not None:
            results.extend(the_lib.search(libtype=item_class, maxresults=c_size, container_start=c_start, container_size=c_size, filters=filter))
        else:
            results.extend(the_lib.search(libtype=item_class, maxresults=c_size, container_start=c_start, container_size=c_size))
        
        print(f"Loaded: {len(results)}/{lib_size}", end='\r')
        c_start += c_size
    print(f"Completed loading {len(results)} items from {the_lib.title}")
    return results

def get_all_watched(plex, the_lib):
    lib_size = the_lib.totalViewSize()
    results = the_lib.search(unwatched=False)
    return results



