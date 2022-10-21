from pathlib import Path
from pathvalidate import is_valid_filename, sanitize_filename
import itertools


def booler(thing):
    if type(thing) == str:
        thing = eval(thing)
    return bool(thing)


def redact(thing, badthing):
    return thing.replace(badthing, "(REDACTED)")


imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"


def getTID(theList):
    imdbid = None
    tmid = None
    tvid = None
    for guid in theList:
        if imdb_str in guid.id:
            imdid = guid.id.replace(imdb_str, "")
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str, "")
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str, "")
    return imdbid, tmid, tvid


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
