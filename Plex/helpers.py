import getpass
import hashlib
import itertools
import json
import os
import shutil
from pathlib import Path

import plexapi
import requests
from config import Config
from dotenv import load_dotenv, set_key, unset_key
from pathvalidate import is_valid_filename, sanitize_filename
from PIL import Image
from plexapi.exceptions import Unauthorized
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

# Your fixed client identifier
CLIENT_IDENTIFIER = 'MediaScripts-chazlarson'
# File to store token + server URL
AUTH_FILE = '.plex_auth.json'
# Default network timeout (seconds)
DEFAULT_TIMEOUT = 360

stock_md5 = {
    "plexapi.config.ini": '6209bb0c2ab877e6b74f757a004c84c9',
}

def file_has_changed(filepath):
    """
    Calculates the MD5 checksum of a file.

    Args:
        filepath: The path to the file.

    Returns:
        The MD5 checksum as a hexadecimal string.
    """
    if filepath.name not in stock_md5:
        print(f"File {filepath.name} not in stock_md5, returning True")
        return True
    old_hash = stock_md5.get(filepath.name)
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as file:
        # Read the file in chunks to handle large files efficiently
        for chunk in iter(lambda: file.read(4096), b""):
            md5_hash.update(chunk)
    new_hash = md5_hash.hexdigest()
    return new_hash != old_hash


def copy_file(source_path, destination_path):
    """Copies a file from source to destination using pathlib.

    Args:
        source_path (str or Path): Path to the source file.
        destination_path (str or Path): Path to the destination file.
    """
    source_path = Path(source_path)
    destination_path = Path(destination_path)

    if source_path.is_file():
        shutil.copy(source_path, destination_path)
        print(f"File copied from {source_path} to {destination_path}")
    else:
        print(f"Source path {source_path} is not a file.")

def has_overlay(image_path):
    kometa_overlay = False
    tcm_overlay = False

    with Image.open(image_path) as image:
        exif_tags = image.getexif()
        kometa_overlay = (
            exif_tags is not None
            and 0x04BC in exif_tags
            and exif_tags[0x04BC] == "overlay"
        )
        tcm_overlay = (
            exif_tags is not None
            and 0x4242 in exif_tags
            and exif_tags[0x4242] == "titlecard"
        )

    return kometa_overlay, tcm_overlay


def booler(thing):
    if type(thing) is str:
        thing = eval(thing)
    return bool(thing)


def redact(thing, badthing):
    return thing.replace(badthing, "(REDACTED)")


def redact(the_url, str_list):
    ret_val = the_url
    for thing in str_list:
        ret_val = ret_val.replace(thing, "[REDACTED]")
    return ret_val


def load_auth():
    """Return saved auth dict or None."""
    try:
        with open(AUTH_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_auth(data):
    """Save auth dict and lock down file permissions."""
    with open(AUTH_FILE, 'w') as f:
        json.dump(data, f)
    try:
        os.chmod(AUTH_FILE, 0o600)
    except Exception:
        pass

def choose_server(servers):
    """Prompt the user to choose one of the available Plex Media Server resources."""
    print("\nAvailable Plex Media Servers:")
    for idx, res in enumerate(servers, start=1):
        print(f"  [{idx}] {res.name} ({res.clientIdentifier})")
    while True:
        choice = input(f"Select server [1–{len(servers)}]: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(servers):
                return servers[idx-1]
        print("❌ Invalid selection; please enter a number from the list.")

def get_timeout():
    """Prompt user for network timeout value, with a safe default."""
    val = input(f"Network timeout in seconds [default {DEFAULT_TIMEOUT}]: ").strip()
    if not val:
        return DEFAULT_TIMEOUT
    try:
        t = float(val)
        if t <= 0:
            raise ValueError()
        return t
    except ValueError:
        print(f"⚠️  Invalid timeout '{val}', using default {DEFAULT_TIMEOUT}.")
        return DEFAULT_TIMEOUT

def get_skip_ssl():
    """Prompt user whether to skip SSL certificate verification."""
    val = input("Skip SSL certificate verification? [y/N]: ").strip().lower()
    return val in ('y', 'yes')

def make_session(skip_ssl):
    """Return a requests.Session configured for SSL verification or not."""
    if skip_ssl:
        sess = requests.Session()
        sess.verify = False
        return sess
    return None

def do_login(timeout, session):
    """Prompt for user/pass, let user pick server, connect & return PlexServer."""
    username = input('Plex Username: ')
    password = getpass.getpass('Plex Password: ')
    account = MyPlexAccount(username, password)
    print(f"✔ Logged in as {account.username}")

    servers = [r for r in account.resources() if r.product == 'Plex Media Server']
    if not servers:
        raise RuntimeError("No Plex Media Server found on your account.")

    resource = choose_server(servers)
    print(f"→ Connecting to server: {resource.name} (timeout={timeout}s)")

    # resource.connect accepts a `session` and `timeout` argument
    plex = resource.connect(timeout=timeout, session=session)
    print(f"✔ Connected to Plex server: {plex.friendlyName}")

    token = getattr(account, 'authenticationToken', None) or getattr(account, '_token')
    baseurl = getattr(plex, 'baseurl', None) or getattr(plex, '_baseurl')
    save_auth({'token': token, 'baseurl': baseurl})
    print(f"⚑ Saved auth to {AUTH_FILE}")
    return plex


def get_plex():
    plex = None
    config = Config('../config.yaml')
    os.environ['PLEXAPI_HEADER_IDENTIFIER'] = f"{config.get('plex_api.header_identifier')}"
    os.environ['PLEXAPI_PLEXAPI_TIMEOUT'] = f"{config.get('plex_api.timeout')}"
    os.environ['PLEXAPI_AUTH_SERVER_BASEURL'] = f"{config.get('plex_api.auth_server.base_url')}"
    os.environ['PLEXAPI_AUTH_SERVER_TOKEN'] = f"{config.get('plex_api.auth_server.token')}"
    os.environ['PLEXAPI_LOG_BACKUP_COUNT'] = f"{config.get('plex_api.log.backup_count')}"
    os.environ['PLEXAPI_LOG_FORMAT'] = f"{config.get('plex_api.log.format')}"
    os.environ['PLEXAPI_LOG_LEVEL'] = f"{config.get('plex_api.log.level')}"
    os.environ['PLEXAPI_LOG_PATH'] = f"{config.get('plex_api.log.path')}"
    os.environ['PLEXAPI_LOG_ROTATE_BYTES'] = f"{config.get('plex_api.log.rotate_bytes')}"
    os.environ['PLEXAPI_LOG_SHOW_SECRETS'] = f"{config.get('plex_api.log.show_secrets')}"
    os.environ['PLEXAPI_SKIP_VERIFYSSL'] = f"{config.get('plex_api.skip_verify_ssl')}"                     # ignore self signed certificate errors

    try:
        print("creating plex with plexapi config")
        plex = PlexServer()
        print(f"connected to {plex.friendlyName}")
    except Exception as ex:
        print(f"plexapi config failed: {ex}")
        auth = load_auth()
        if auth:
            try:
                print("creating plex with saved auth")
                plex = PlexServer(auth['url'], token=auth['token'])
                print(f"connected to {plex.friendlyName}")
            except Unauthorized:
                print("Saved auth is invalid. Please re-authenticate.")
                auth = None
        else:
            print("No saved auth found. Please authenticate.")
            timeout = get_timeout()
            skip_ssl = get_skip_ssl()
            session = make_session(skip_ssl)
            plex = do_login(timeout, session)

    return plex

def get_target_libraries(plex):
    if plex:
        ALL_LIBS = plex.library.sections()
    else:
        print(f"Plex connection failed")
        return None

    print(f"{len(ALL_LIBS)} libraries found")

    config = Config()

    LIBRARY_NAMES = config.get("general.library_names")

    if LIBRARY_NAMES and len(LIBRARY_NAMES) > 0:
        LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
    else:
        LIB_ARRAY = None
        print(f"No libraries specified in config")
        print(f"Processing all {len(ALL_LIBS)} libraries")

    if LIB_ARRAY is None:
        LIB_ARRAY = []
        for lib in ALL_LIBS:
            LIB_ARRAY.append(f"{lib.title.strip()}")

    return LIB_ARRAY

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"


def get_ids(theList):
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


def validate_filename(filename):
    # return filename
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
    if type == "movie":
        return plexapi.video.Movie
    if type == "show":
        return plexapi.video.Show
    if type == "episode":
        return plexapi.video.Episode
    return None


def get_size(the_lib, tgt_class=None, filter=None):
    lib_size = 0
    foo = []

    if filter is not None:
        foo = the_lib.search(libtype=tgt_class, filters=filter)
    else:
        foo = the_lib.search(libtype=tgt_class)

    lib_size = len(foo)

    return lib_size


def get_all_from_library(the_lib, tgt_class=None, filter=None):
    if tgt_class is None:
        tgt_class = the_lib.type

    lib_size = get_size(the_lib, tgt_class, filter)

    c_start = 0
    c_size = 500
    results = []
    while lib_size is None or c_start <= lib_size:
        if filter is not None:
            results.extend(
                the_lib.search(
                    libtype=tgt_class,
                    maxresults=c_size,
                    container_start=c_start,
                    container_size=lib_size,
                    filters=filter,
                )
            )
        else:
            results.extend(
                the_lib.search(
                    libtype=tgt_class,
                    maxresults=c_size,
                    container_start=c_start,
                    container_size=lib_size,
                )
            )

        print(f"Loaded: {len(results)}/{lib_size}", end="\r")
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
    ssn.headers.update({"Accept": "application/json"})
    ssn.params.update({"X-Plex-Token": plex_token})
    media_output = ssn.get(f"{plex_url}/library/sections/{lib_index}/all").json()
    return media_output


def get_xml_libraries(plex_url, plex_token):
    media_output = None
    try:
        ssn = requests.Session()
        ssn.headers.update({"Accept": "application/json"})
        ssn.params.update({"X-Plex-Token": plex_token})
        print("- making request")
        raw_output = ssn.get(f"{plex_url}/library/sections/")
        if raw_output.status_code == 200:
            print("- success")
            media_output = raw_output.json()
    except Exception as ex:
        print(f"- problem getting libraries: {ex}")

    return media_output


def get_xml_watched(plex_url, plex_token, lib_index, lib_type="movie"):
    output_array = []

    ssn = requests.Session()
    ssn.headers.update({"Accept": "application/json"})
    ssn.params.update({"X-Plex-Token": plex_token})
    media_output = ssn.get(
        f"{plex_url}/library/sections/{lib_index}/all?viewCount>=1"
    ).json()

    if "Metadata" in media_output["MediaContainer"].keys():
        if lib_type == "movie":
            # library is a movie lib; loop through every movie
            movie_count = len(media_output["MediaContainer"]["Metadata"])
            movie_idx = 1
            for movie in media_output["MediaContainer"]["Metadata"]:
                print(f"> {movie_idx:05}/{movie_count:05}", end="\r")
                if "viewCount" in movie.keys():
                    output_array.append(movie)
                movie_idx += 1
        elif lib_type == "show":
            # library is show lib; loop through every show
            show_count = len(media_output["MediaContainer"]["Metadata"])
            show_idx = 1
            for show in media_output["MediaContainer"]["Metadata"]:
                print(f"> {show_idx:05}/{show_count:05}            ", end="\r")
                if "viewedLeafCount" in show.keys() and show["viewedLeafCount"] > 0:
                    show_output = ssn.get(
                        f"{plex_url}/library/metadata/{show['ratingKey']}/allLeaves?viewCount>=1"
                    ).json()
                    # loop through episodes of show to check if targeted season exists
                    # loop through episodes of show
                    if "Metadata" in show_output["MediaContainer"].keys():
                        episode_list = show_output["MediaContainer"]["Metadata"]
                        episode_count = len(episode_list)
                        episode_idx = 1
                        for episode in episode_list:
                            print(
                                f"> {show_idx:05}/{show_count:05} {episode_idx:05}/{episode_count:05}",
                                end="\r",
                            )
                            if "viewCount" in episode.keys():
                                output_array.append(episode)
                            episode_idx += 1
                show_idx += 1

    return output_array


def get_media_details(plex_url, plex_token, rating_key):
    ssn = requests.Session()
    ssn.headers.update({"Accept": "application/json"})
    ssn.params.update({"X-Plex-Token": plex_token})
    media_output = ssn.get(f"{plex_url}/library/metadata/{rating_key}").json()

    return media_output


def get_all_watched(plex, the_lib):
    results = the_lib.search(unwatched=False)
    return results


def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2) + 1):
        yield chr(c)


ALPHABET = []
NUMBERS = []

for c in char_range("a", "z"):
    ALPHABET.append(c)

for c in char_range("0", "9"):
    NUMBERS.append(c)


def remove_articles(thing):
    if thing.startswith("The "):
        thing = thing.replace("The ", "")
    if thing.startswith("A "):
        thing = thing.replace("A ", "")
    if thing.startswith("An "):
        thing = thing.replace("An ", "")
    if thing.startswith("El "):
        thing = thing.replace("El ", "")

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
        print("No environment [.env] file.  Creating base file.")
        if os.path.exists(".env.example"):
            src_file = os.path.join(".", ".env.example")
            tgt_file = os.path.join(".", ".env")
            shutil.copyfile(src_file, tgt_file)
            print("Please edit config.yaml to suit and rerun script.")
        else:
            print("No example [.env.example] file.  Cannot create base file.")
        status = -1

    PLEX_URL = os.getenv("PLEX_URL")
    PLEX_TOKEN = os.getenv("PLEX_TOKEN")

    if PLEX_URL is not None:
        # Add the PLEXAPI env vars
        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_PLEXAPI_TIMEOUT",
            value_to_set="360",
        )

        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_AUTH_SERVER_BASEURL",
            value_to_set=PLEX_URL,
        )
        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_AUTH_SERVER_TOKEN",
            value_to_set=PLEX_TOKEN,
        )
        unset_key(
            dotenv_path=file_path,
            key_to_unset="PLEX_URL",
            quote_mode="always",
            encoding="utf-8",
        )
        unset_key(
            dotenv_path=file_path,
            key_to_unset="PLEX_TOKEN",
            quote_mode="always",
            encoding="utf-8",
        )

        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_LOG_BACKUP_COUNT",
            value_to_set="3",
        )
        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_LOG_FORMAT",
            value_to_set="%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s",
        )
        set_key(
            dotenv_path=file_path, key_to_set="PLEXAPI_LOG_LEVEL", value_to_set="INFO"
        )
        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_LOG_PATH",
            value_to_set="plexapi.log",
        )
        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_LOG_ROTATE_BYTES",
            value_to_set="512000",
        )
        set_key(
            dotenv_path=file_path,
            key_to_set="PLEXAPI_LOG_SHOW_SECRETS",
            value_to_set="false",
        )

        # and load the new file
        load_dotenv(dotenv_path=file_path)
        status = 1

    if (
        os.getenv("PLEXAPI_AUTH_SERVER_BASEURL") is None
        or os.getenv("PLEXAPI_AUTH_SERVER_BASEURL") == "https://plex.domain.tld"
    ):
        print("You must specify PLEXAPI_AUTH_SERVER_BASEURL in the config.yaml.")
        # status = -1

    if (
        os.getenv("PLEXAPI_AUTH_SERVER_TOKEN") is None
        or os.getenv("PLEXAPI_AUTH_SERVER_TOKEN") == "PLEX-TOKEN"
    ):
        print("You must specify PLEXAPI_AUTH_SERVER_TOKEN in the config.yaml.")
        # status = -1

    return status


def check_for_images(file_path):
    jpg_path = file_path.replace(".dat", ".jpg")
    png_path = file_path.replace(".dat", ".png")

    dat_file = Path(file_path)
    jpg_file = Path(jpg_path)
    png_file = Path(png_path)

    dat_here = dat_file.is_file()
    jpg_here = jpg_file.is_file()
    png_here = png_file.is_file()

    if dat_here:
        os.remove(file_path)

    if jpg_here and png_here:
        os.remove(jpg_path)

        os.remove(png_path)

    if jpg_here or png_here:
        return True

    return False
