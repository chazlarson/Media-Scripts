from pathlib import Path, PurePath
from pathvalidate import is_valid_filename, sanitize_filename

def booler(thing):
    if type(thing) == str:
        thing = eval(thing)
    return bool(thing)

def redact(thing, badthing):
    return thing.replace(badthing, "(REDACTED)")

imdb_str = 'imdb://'
tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

def getTID(theList):
    imdbid = None
    tmid = None
    tvid = None
    for guid in theList:
        if imdb_str in guid.id:
            imdid = guid.id.replace(imdb_str,'')
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str,'')
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str,'')
    return imdbid, tmid, tvid

def validate_filename(filename):
    if is_valid_filename(filename):
        return filename, None
    else:
        mapping_name = sanitize_filename(filename)
        stat_string = f"Log Folder Name: {filename} is invalid using {mapping_name}"
        return mapping_name, stat_string

def getPath(library, item, season=False):
    if item.type == 'collection':
        return "Collection", item.title
    else:
        if library.type == 'movie':
            for media in item.media:
                for part in media.parts:
                    return Path(part.file).parent, Path(part.file).stem
        elif library.type == 'show':
            for episode in item.episodes():
                for media in episode.media:
                    for part in media.parts:
                        if season:
                            return Path(part.file).parent, Path(part.file).stem
                        return Path(part.file).parent.parent, Path(part.file).parent.parent.stem

