# You're getting started with Plex-Meta-Manager and you want to export your existing collections
# Here is a quick and dirty [emphasis on "quick" and "dirty"] way to do that.
# Copy this into your PMM directory [I'm assuming you have those requirements installed]
# update the three fields in ALL_UPPER_CASE just below
# then run it with: python get_collections.py
# script will grab some details from each collection and write a metadata file that you could use with PMM
# Also grabs artwork and background.
# This is extremely naive; it doesn't recreate filters, just grabs a list of everything in each collection.
#  For example, you'll end up with something like this for each collection:
# 
#  Yvonne Strahovski:
#     sort_title: z171
#     url_poster: ./config/artwork/Yvonne Strahovski.png
#     summary: Yvonne Strahovski (born Strzechowski on 30 July 1982) is ...
#     collection_order: release
#     plex_search:
#       any:
#         title:
#           - Killer Elite
#           - I, Frankenstein
#           - 'Batman: Bad Blood'
#           - The Predator
#           - Angel of Mine

from plexapi.server import PlexServer
from plexapi.utils import download
from ruamel import yaml
from pathlib import Path, PurePath

baseurl = 'YOUR_PLEX_URL'
token = 'YOUR_PLEX_TOKEN'
library = 'LIBRARY_NAME_TO_TARGET'

artwork_dir = "artwork"
background_dir = "background"
config_dir = 'config'
 

plex = PlexServer(baseurl, token)

coll_obj = {}
coll_obj['collections'] = {}

def get_sort_text(argument):
    switcher = {
        0: "release",
        1: "alpha",
        2: "custom"
    }
    return switcher.get(argument, "invalid-sort")

movies = plex.library.section(library)
collections = movies.collections()
for collection in collections:

    title = collection.title

    print(f"title - {title}")

    artwork_path = Path('.', config_dir, f"{library}-{artwork_dir}")
    artwork_path.mkdir(mode=511, parents=True, exist_ok=True)

    background_path = Path('.', config_dir, f"{library}-{background_dir}")
    background_path.mkdir(mode=511, parents=True, exist_ok=True)

    thumbPath = download(f"{baseurl}{collection.thumb}", token, filename=f"{collection.title}.png", savepath=artwork_path)

    if collection.art is not None:
        artPath = download(f"{baseurl}{collection.art}", token, filename=f"{collection.title}.png", savepath=background_path)
    else:
        artPath = None

    this_coll = {}
    this_coll["sort_title"] = collection.titleSort
    this_coll["url_poster"] = f"./{thumbPath}"
    if artPath is not None:
        this_coll["url_background"] = f"./{artPath}"
       
    if len(collection.summary) > 0:
        this_coll["summary"] = collection.summary

    this_coll["collection_order"] = get_sort_text(collection.collectionSort)

    this_coll["plex_search"] = {}
    this_coll["plex_search"]["any"] = {}
    titlearray = []
    items = collection.items()
    for item in items:
        titlearray.append(item.title)
    this_coll["plex_search"]["any"]["title"] = titlearray

    if len(this_coll) > 0:
        coll_obj['collections'][collection.title] = this_coll

metadatafile_path = Path('.', config_dir, f"{library}-existing.yml")

yaml.round_trip_dump(coll_obj, open(metadatafile_path, "w", encoding="utf-8"), indent=None, block_seq_indent=2)
