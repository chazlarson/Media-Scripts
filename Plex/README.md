# Plex scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Setup

1. clone repo
1. Install requirements with `pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
1. Copy `.env.example` to `.env`
1. Edit .env to suit

All these scripts use the same `.env` and requirements.

NOTE: on 06-29 these scripts have changed to using ENV vars to set up the Plex API details.  This was done primarily to enable the timeout to apply to all Plex interactions.

If your `.env` file contains the original `PLEX_URL` and `PLEX_TOKEN` entires those will be silently changed for you.

### `.env` contents

```
TMDB_KEY=TMDB_API_KEY                        # https://developers.themoviedb.org/3/getting-started/introduction
TVDB_KEY=TVDB_V4_API_KEY                     # currently not used; https://thetvdb.com/api-information
PLEXAPI_PLEXAPI_TIMEOUT='360'
PLEXAPI_AUTH_SERVER_BASEURL=https://plex.domain.tld
PLEXAPI_AUTH_SERVER_TOKEN=PLEX-TOKEN
PLEXAPI_LOG_BACKUP_COUNT='3'
PLEXAPI_LOG_FORMAT='%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s'
PLEXAPI_LOG_LEVEL='INFO'
PLEXAPI_LOG_PATH='plexapi.log'
PLEXAPI_LOG_ROTATE_BYTES='512000'
PLEXAPI_LOG_SHOW_SECRETS='false'
PLEX_OWNER=yournamehere                      # account name of the server owner
TARGET_PLEX_URL=https://plex.domain2.tld     # As above, the target of apply_all_status
TARGET_PLEX_TOKEN=PLEX-TOKEN-TWO             # As above, the target of apply_all_status
TARGET_PLEX_OWNER=yournamehere               # As above, the target of apply_all_status
LIBRARY_MAP={"LIBRARY_ON_PLEX":"LIBRARY_ON_TARGET_PLEX", ...}
                                             # In apply_all_status, map libraries according to this JSON.
LIBRARY_NAMES=Movies,TV Shows,Movies 4K      # comma-separated list of libraries to act on
CAST_DEPTH=20                                # how deep to go into the cast for actor collections
TOP_COUNT=10                                 # how many actors to export
TARGET_LABELS=this label, that label         # comma-separated list of labels to remove posters from
REMOVE_LABELS=True                           # attempt to remove the TARGET_LABELs from items after resetting the poster
DELAY=1                                      # optional delay between items
CURRENT_POSTER_DIR=current_posters           # put downloaded current posters and artwork here
POSTER_DIR=extracted_posters                 # put downloaded posters here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=False                        # generate a script rather than downloading
POSTER_CONSOLIDATE=True                      # posters are separated into folders by library
TRACK_URLS=1                                 # If set to 1, URLS are tracked and won't be downloaded twice
TRACK_COMPLETION=1                           # If set to 1, movies/shows are tracked as complete by rating id
TRACK_RESET_STATUS=True                      # reset-posters-* keeps track of status and picks up where it left off
ARTWORK=True                                 # current background is downloaded with current poster
PLEX_PATHS=False
NAME_IN_TITLE=True
POSTER_NAME=poster
BACKGROUND_NAME=background
RESET_SEASONS=True                           # reset-posters-plex resets season artwork as well in TV libraries
RESET_EPISODES=True                          # reset-posters-plex resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
KEEP_COLLECTIONS=bing,bang                   # List of collections to keep
INCLUDE_COLLECTION_ARTWORK=1                 # should get-all-posters retrieve collection posters?
ONLY_COLLECTION_ARTWORK=0                    # should get-all-posters retrieve ONLY collection posters?
GRAB_SEASONS=1                               # should get-all-posters retrieve season posters?
GRAB_EPISODES=1                              # should get-all-posters retrieve episode posters? [requires GRAB_SEASONS]
GRAB_BACKGROUNDS=1                           # should get-all-posters retrieve backgrounds?
ONLY_CURRENT=0                               # should get-all-posters retrieve ONLY current artwork?
LOCAL_RESET_ARCHIVE=1                        # should reset-posters-tmdb keep a local archive of posters?
USE_ASSET_NAMING=1                           # should grab-all-posters name images to match PMM's Asset Directory requirements?
USE_ASSET_FOLDERS=1                          # should those PMM-Asset-Directory names use asset folders?
ASSETS_BY_LIBRARIES=1                        # should those PMM-Asset-Directory images be sorted into library folders?
ASSET_DIR=assets                             # top-level directory for those PMM-Asset-Directory images

KEEP_JUNK=0                                  # keep files that script would normally delete [incorrect filetypes, mainly]
ADD_SOURCE_EXIF_COMMENT=1                    # add the source URL to the image EXIF tags
TRACK_IMAGE_SOURCES=1                        # keep a file containing file names and source URLs
USE_ASSET_SUBFOLDERS=0                       # create asset folders in subfolders ["Collections", "Other", or [0-9, A-Z]] ]
FOLDERS_ONLY=0                               # Just build out the folder hierarchy; no image downloading
ONLY_THESE_COLLECTIONS=Bing|Bang|Boing       # only grab artwork for these collections and items in them
RESET_LIBRARIES=Bing,Bang,Boing              # reset "last time" count to 0 for these libraries
RETAIN_RESET_STATUS_FILE=0                   # Don't delete the reset progress file at the end
DRY_RUN=0                                    # [currently only works with reset-posters-*]; don't actually do anything, just log
FLUSH_STATUS_AT_START=0                      # Delete the reset progress file at the start instead of reading them
RESET_SEASONS_WITH_SERIES=0                  # If there isn't a season poster, use the series poster
```

## Scripts:
1. [user-emails.py](#user-emailspy) - extract user emails from your shares
1. [reset-posters-tmdb.py](#reset-posters-tmdbpy) - reset all artwork in a library to TMDB default
1. [reset-posters-plex.py](#reset-posters-plexpy) - reset all artwork in a library to Plex default
1. [grab-all-IDs.py](#grab-all-IDspy) - grab [into a sqlite DB] ratingKey, IMDB ID, TMDB ID, TVDB ID for everything in a library from plex
1. [grab-all-posters.py](#grab-all-posterspy) - grab some or all of the artwork for a library from plex
1. [grab-all-status.py](#grab-all-statuspy) - grab watch status for all users all libraries from plex
1. [apply-all-status.py](#apply-all-statuspy) - apply watch status for all users all libraries to plex from the file emitted by the previous script
1. [show-all-playlists.py](#show-all-playlistspy) - Show contents of all user playlists
1. [delete-collections.py](#delete-collectionspy) - delete most or all collections from one or more libraries
1. [refresh-metadata.py](#refresh-metadatapy) - Refresh metadata individually on items in a library
1. [actor-count.py](#actor-countpy) - Generate a list of actor credit counts

## user-emails.py

You want a list of email addresses for all the people you share with.

Here is a quick and dirty [emphasis on "quick" and "dirty"] way to do that.

### Usage
1. setup as above
2. Run with `python user-emails.py`

The script will loop through all the shared users on your acount and spit out username and email address.

```shell
connecting...
getting users...
looping over 26 users...
binguser - bing@gmail.com
mrbang - bang@gmail.com
boingster - boing@gmail.com
...
```

## reset-posters-tmdb.py

Perhaps you want to reset all the posters in a library

This script will set the poster for every series or movie to the default poster from TMDB/TVDB.  It also saves that poster under `./posters/[movies|shows]/<rating_key>.ext` in case you want to use them with PMM's overlay resets.

If there is a file already located at `./posters/[movies|shows]/<rating_key>.ext`, the script will use *that image* instead of retrieving a new one, so if you replace that local one with a poster of your choice, the script will use the custom one rather than the TMDB/TVDB default.

Script-specific variables in .env:
```
TRACK_RESET_STATUS=True                         # pick up where the script left off
TARGET_LABELS = Bing, Bang, Boing               # reset artwork on items with these labels
REMOVE_LABELS=True                              # remove labels when done [NOT RECOMMENDED]
RESET_SEASONS=True                              # reset-posters-plex resets season artwork as well in TV libraries
RESET_EPISODES=True                             # reset-posters-plex resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
LOCAL_RESET_ARCHIVE=True                        # keep a local archive of posters
RETAIN_RESET_STATUS_FILE=0                      # Don't delete the reset progress file at the end
DRY_RUN=0                                       # [currently only works with reset-posters-*]; don't actually do anything, just log
FLUSH_STATUS_AT_START=0                         # Delete the reset progress file at the start instead of reading them
RESET_SEASONS_WITH_SERIES=0                     # If there isn't a season poster, use the series poster
```

If you set:
```
TRACK_RESET_STATUS=True
```
The script will keep track of where it is and will pick up at that point on subsequent runs.  This is useful in the event of a lost connection to Plex.

Once it gets to the end of the library successfully, the tracking file is deleted.  If you want to disable that for some reason, set `RETAIN_RESET_STATUS_FILE` to 1

If you want to reset any existing progress tracking and start from the beginning for some reason, set `FLUSH_STATUS_AT_START` to 1.

If you specify a comma-separated list of labels in the env file:
```
TARGET_LABELS = This label, That label, Another label
```
The script will reset posters only on movies with those labels assigned.

If you also set:
```
REMOVE_LABELS=True
```
The script will *attempt* to remove those labels after resetting the poster.  I say "attempt" since in testing I have experienced an odd situation where no error occurs but the label is not removed.  My test library of 230 4K-Dolby Movies contains 47 that fail in this way; every run it goes through the 47 movies "removing labels" without error yet they still have the labels on the next run.

Besides that Heisenbug, I don't recommend using this [`REMOVE_LABELS`] since the label removal takes a long time [dozens of seconds per item].  Doing this through the Plex UI is much faster.

If you set:
```
LOCAL_RESET_ARCHIVE=False
```
The script will set the artwork by sending the TMDB URL to Plex, without downloading the file locally first.  This means a faster run compared to the initial run when downloading.

Example timings on a test library of 1140 TV Shows, resetting artwork for Show-Season-Episode level:

1. No downloading: 1 hour 25 minutes
1. With downloading: 2 hours 30 minutes
2. Second run with downloaded archive: 1 hours 10 minutes

That is on a system with a 1G connection up and down, so values are just relative to each other.

The value of the local archive is that if you want to replace some of those images with your own, it provides a simple way to update all the posters in a library to custom posters of your own.  When the script runs, it looks at that archive first, only downloading an image if one doesn't exist in the archive.

In that way it's sort of like PMM's Asset Directory.

If you're just looking to reset as a one-off, that may not have value.

If no artwork is found at TMDB for a thing, no action is taken.

### Usage
1. setup as above
2. Run with `python reset-posters-tmdb.py`

```
tmdb config...
connecting to https://stream.BING.BANG...
getting items from [TV Shows - 4K]...
looping over 876 items...
[=---------------------------------------] 2.7% ... Age of Big Cats
```

At this time, there is no configuration aside from library name; it replaces all posters.  It does not delete any posters from Plex, just grabs a URL and uses the API to set the poster to the URL.

## reset-posters-plex.py

Script-specific variables in .env:
```
RESET_SEASONS=True                           # reset-posters-plex resets season artwork as well in TV libraries
RESET_EPISODES=True                          # reset-posters-plex resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
RETAIN_RESET_STATUS_FILE=0                   # Don't delete the reset progress file at the end
DRY_RUN=0                                    # [currently only works with reset-posters-*]; don't actually do anything, just log
FLUSH_STATUS_AT_START=0                      # Delete the reset progress file at the start instead of reading them
RESET_SEASONS_WITH_SERIES=0                  # If there isn't a season poster, use the series poster
```

Same as `reset-posters-tmdb.py`, but it resets the artwork to the first item in Plex's own list of artwork, rather than downloading a new image from TMDB.

With `RESET_SEASONS=True`, if the season doesn't have artwork the series artwork will be used instead.

## grab-all-IDs.py

Perhaps you want to gather all the IDs for everything in a library.

This script will go through a library and grab PLex RatingKey [which may be unique], IMDB ID, TMDB ID, and TVDB ID for everything in the list of libraries specified in the `.env`.  It stores the data in a sqlite database called `ids.sqlite`; the repo copy of this file contains that data for 105871 movies and 26699 TV Shows.


## grab-all-posters.py

Perhaps you want to get local copies of some or all the posters Plex knows about for everything in a library.

Maybe you find it easier to look through a bunch of options in CoverFlow or something.

This script will download some or all the posters for every item in a given set of libraries.  It (probably) won't download the same thing more than once, so you can cancel it and restart it if need be.  I say "probably" because the script is assuming that the list of posters retireved from Plex is always in the same order [i.e. that new posters get appended to the end of the list].  On subsequent runs, the script checks only that a file exists at, for example, `extracted_posters/Movies - 4K DV/10 Cloverfield Lane/2273074-001.png`.  It doesn't pay any attention to whether the two [the one on disk vs. the one coming from Plex] are the same image.  I'll probably add a check to look at the image URL to attempt to ameliorate this at some point.

The script can name these files so that they are ready for use with [Plex-Meta-Manager's Asset Directory](https://metamanager.wiki/en/latest/home/guides/assets.html).  Currently this only works with `ONLY_CURRENT` set.

The script queues downlaods so they happen in the background in multiple threads.  Once it's gone through the libraries listed in the config, it will then wait until the queue is drained before exiting.  If you want to drop out of the library-scanning loop early, create a file `stop.dat` next to the script, and the library loop will exit at the end of the current show or movie, then go to the "waiting for the downloads" section.  This allows you to get out early without flushing the queue [as control-C would do].

You can also skip the current library by creating `skip.dat`.

Script-specific variables in .env:
```
POSTER_DIR=extracted_posters                 # put downloaded posters here
CURRENT_POSTER_DIR=current_posters           # put downloaded current posters and artwork here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=0                            # if set to 0, generate a script rather than downloading
POSTER_CONSOLIDATE=1                         # if set to 0, posters are separated into folders by library
INCLUDE_COLLECTION_ARTWORK=1                 # If set to 1, collection posters are retrieved
ONLY_COLLECTION_ARTWORK=0                    # If set to 1, ONLY collection posters are retrieved
GRAB_SEASONS=1                               # grab season posters
GRAB_EPISODES=1                              # grab episode posters [requires GRAB_SEASONS]
GRAB_BACKGROUNDS=1                           # If set to 1, backgrounds are retrieved [into a folder `backgrounds`]
ONLY_CURRENT=0                               # if set to 1, only current artwork is retrieved; also CURRENT_POSTER_DIR is used
TRACK_URLS=1                                 # If set to 1, URLS are tracked and won't be downloaded twice
TRACK_COMPLETION=1                           # If set to 1, movies/shows are tracked as complete by rating id
USE_ASSET_NAMING=1                           # If set to 1, images are stored and named per PMM's Asset Directory rules
USE_ASSET_FOLDERS=1                          # If set to 1, images are stored and named assuming `asset_folders: true` in PMM
ASSETS_BY_LIBRARIES=1                        # If set to 1, images are stored in separate asset dirs per library
ASSET_DIR=assets                             # top-level directory for those PMM-Asset-Directory images
KEEP_JUNK=0                                  # If set to 1, keep files that script would normally delete [incorrect filetypes, mainly]
ADD_SOURCE_EXIF_COMMENT=1                    # If set to 1, add the source URL to the image EXIF tags
TRACK_IMAGE_SOURCES=1                        # If set to 1, keep a file containing file names and source URLs
USE_ASSET_SUBFOLDERS=0                       # If set to 1, create asset folders in subfolders ["Collections", "Other", or [0-9, A-Z]] ]
FOLDERS_ONLY=0                               # If set to 1, just build out the folder hierarchy; no image downloading
ONLY_THESE_COLLECTIONS=Bing|Bang|Boing       # only grab artwork for these collections and items in them; if empty, no filter
RESET_LIBRARIES=Bing,Bang,Boing              # reset "last time" count to 0 for these libraries
DEFAULT_YEARS_BACK=2                         # If there is no "last run date" stored, go this many years back [integer; negative values will be made positive]
```

The point of "POSTER_DEPTH" is that sometimes movies have an insane number of posters, and maybe you don't want all 257 Endgame posters or whatever.  Or maybe you want to download them in batches.

If "POSTER_DOWNLOAD" is `0`, the script will build a shell script for each library to download the images at your convenience instead of downloading them as it runs, so you can run the downloads overnight or on a different machine with ALL THE DISK SPACE or something.

If "POSTER_CONSOLIDATE" is `1`, the script will store all the images in one directory rather than separating them by library name.  The idea is that Plex shows the same set of posters for "Star Wars" whether it's in your "Movies" or "Movies - 4K" or whatever other libraries, so there's no reason to pull the same set of posters multiple times.  There is an example below.

If "INCLUDE_COLLECTION_ARTWORK" is `1`, the script will grab artwork for all the collections in the target library.

If "ONLY_COLLECTION_ARTWORK" is `1`, the script will grab artwork for ONLY the collections in the target library; artwork for individual items [movies, shows] will not be grabbed.

If "ONLY_THESE_COLLECTIONS" is not empty, the script will grab artwork for ONLY the collections listed and items contained in those collections.  This doesn't affect the sorting or naming, just the filter applied when asking Plex for the items.  IF YOU DON'T CHANGE THIS SETTING, NOTHING WILL BE DOWNLOADED.

If "TRACK_URLS" is `1`, the script will track every URL it downloads in a sqlite database.  On future runs, if a given URL is found in that database it won't be downloaded a second time.  This may save time if the same URL appears multiple times in the list of posters from Plex.

If "TRACK_COMPLETION" is `1`, the script record movies/shows by rating key in a sqlite database.  On future runs, if a given rating key is found in that database the show/movie is considered complete and it will be skipped.  This will save time in subsequent runs as the script will not look through all 2000 episodes of some show only to determine that it's already downloaded all the images.  HOWEVER, this also means that future episodes won't be picked up when you run the script again.

If you delete the directory of extracted posters intending to download them again, be sure to delete these files, or nothing will be downloaded on that second pass.

Files are named following the pattern `S00E00-TITLE-PROVIDER-SOURCE.EXT`, with missing parts absent as seen in the lists below.

The "provider" is the original source of the image [tmdb, fanarttv, etc] and "source" will be "local" [downloaded from the plex server] or "remote" [downloaded from somewhere else].  A source of "none" means the image was uploaded to plex by a tool like PMM.  The remote URL can be found in the log.

The script keeps track of the last date it retrieved items from a library [for show libraries it also tracks seasons and episodes separately], and on each run will only retrieve items added since that date.  If there is no "last run date" for a given thing, the script assumes a last run date of today - `DEFAULT_YEARS_BACK`.

You can use `RESET_LIBRARIES` to force the "last run date" to that fallback date for a given library.  If you want to reset the whole thing, delete `mediascripts.sqlite`.

### Usage
1. setup as above
2. Run with `python grab-all-posters.py`

The posters will be sorted by library [if enabled] with each poster getting an incremented number, like this:

The image names are: `title-source-location-INCREMENT.ext`

`source` is where plex reports it got the image: tmdb, fanarttv, gracenote, etc. This will alaways be "None" for collection images since they are provided by the user or generated [the four-poster ones] by Plex.

`location` will be `local` or `remote` depending whether the URL pointed to the plex server or to some other site like tmdb.

The folder structure in which the images are saved is controlled by a combination of settings; please review the examples below to find the format you want and the settings that you need to generate it.

All movies and TV shows in a single folder:
```
POSTER_CONSOLIDATE=1:

extracted_posters/
└── all_libraries
    ├── 3 12 Hours-847208
    │   ├── 3 12 Hours-tmdb-local-001.jpg
    │   ├── 3 12 Hours-tmdb-remote-002.jpg
    │   └── backgrounds
    │       ├── background-tmdb-local-001.jpg
    │       └── background-tmdb-remote-002.jpg
    ├── 9-1-1 Lone Star-89393
    │   ├── 9-1-1 Lone Star-local-local-001.jpg
    │   ├── 9-1-1 Lone Star-tmdb-local-002.jpg
    │   ├── S01-Season 1
    │   │   ├── S01-Season 1-local-local-001.jpg
    │   │   ├── S01-Season 1-tmdb-local-002.jpg
    │   │   ├── S01E01-Pilot
    │   │   │   ├── S01E01-Pilot-local-local-001.jpg
    │   │   │   └── S01E01-Pilot-tmdb-remote-002.jpg
    │   │   └── backgrounds
    │   │       ├── background-fanarttv-remote-001.jpg
    │   │       └── background-fanarttv-remote-002.jpg
    │   └── backgrounds
    │       ├── background-local-local-001.jpg
    │       └── background-tmdb-remote-002.jpg
    ├── collection-ABC
    │   ├── ABC-None-local-001.jpg
    │   └── ABC-None-local-002.jpg
    └── collection-IMDb Top 250
        ├── IMDb Top 250-None-local-001.jpg
        └── IMDb Top 250-None-local-002.png
```

Split by Plex library name:
```
POSTER_CONSOLIDATE=0:

extracted_posters/
├── Movies
│   ├── 3 12 Hours-847208
│   │   ├── 3 12 Hours-tmdb-local-001.jpg
│   │   ├── 3 12 Hours-tmdb-remote-002.jpg
│   │   └── backgrounds
│   │       ├── background-tmdb-local-001.jpg
│   │       └── background-tmdb-remote-002.jpg
│   └── collection-IMDb Top 250
│       ├── IMDb Top 250-None-local-001.jpg
│       └── IMDb Top 250-None-local-002.png
└── TV Shows
    ├── 9-1-1 Lone Star-89393
    │   ├── 9-1-1 Lone Star-local-local-001.jpg
    │   ├── 9-1-1 Lone Star-tmdb-local-002.jpg
    │   ├── S01-Season 1
    │   │   ├── S01-Season 1-local-local-001.jpg
    │   │   ├── S01-Season 1-tmdb-local-002.jpg
    │   │   ├── S01E01-Pilot
    │   │   │   ├── S01E01-Pilot-local-local-001.jpg
    │   │   │   └── S01E01-Pilot-tmdb-remote-002.jpg
    │   │   └── backgrounds
    │   │       ├── background-fanarttv-remote-001.jpg
    │   │       └── background-fanarttv-remote-002.jpg
    │   └── backgrounds
    │       ├── background-local-local-001.jpg
    │       └── background-tmdb-remote-002.jpg
    └── collection-ABC
        ├── ABC-None-local-001.jpg
        └── ABC-None-local-002.jpg
```

Use PMM Asset-directory naming, flat:
```
USE_ASSET_NAMING=1
USE_ASSET_FOLDERS=0
ASSETS_BY_LIBRARIES=0
ONLY_CURRENT=1

assets
├── Adam-12 (1968) {tvdb-78686}.jpg
├── Adam-12 (1968) {tvdb-78686}_S01E01.jpg
├── Adam-12 (1968) {tvdb-78686}_S01E02.jpg
...
├── Adam-12 (1968) {tvdb-78686}_Season01.jpg
├── Adam-12 (1968) {tvdb-78686}_background.jpg
├── Adam-12 Collection.jpg
├── Star Wars (1977) {imdb-tt0076759} {tmdb-11}.jpg
└── Star Wars (1977) {imdb-tt0076759} {tmdb-11}_background.jpg
```

Use PMM Asset-directory naming, movies and TV in a single directory, split by item name:
```
USE_ASSET_NAMING=1
USE_ASSET_FOLDERS=1
ASSETS_BY_LIBRARIES=0
ONLY_CURRENT=1

assets
├── Adam-12 (1968) {tvdb-78686}
│   ├── S01E01.jpg
│   ├── S01E02.jpg
...
│   ├── Season01.jpg
│   ├── background.jpg
│   └── poster.jpg
├── Adam-12 Collection
│   └── poster.jpg
└── Star Wars (1977) {imdb-tt0076759} {tmdb-11}
    ├── background.jpg
    └── poster.jpg
```

Use PMM Asset-directory naming, split by Plex library name, flat folder:
```
USE_ASSET_NAMING=1
USE_ASSET_FOLDERS=0
ASSETS_BY_LIBRARIES=1
ONLY_CURRENT=1

assets
├── One Movie
│   ├── Star Wars (1977) {imdb-tt0076759} {tmdb-11}.jpg
│   └── Star Wars (1977) {imdb-tt0076759} {tmdb-11}_background.jpg
└── One Show
    ├── Adam-12 (1968) {tvdb-78686}.jpg
    ├── Adam-12 (1968) {tvdb-78686}_S01E01.jpg
    ├── Adam-12 (1968) {tvdb-78686}_S01E02.jpg
...
    ├── Adam-12 (1968) {tvdb-78686}_Season01.jpg
    ├── Adam-12 (1968) {tvdb-78686}_background.jpg
    └── Adam-12 Collection.jpg
```

Use PMM Asset-directory naming, split by Plex library name, split by item name:
```
USE_ASSET_NAMING=1
USE_ASSET_FOLDERS=1
ASSETS_BY_LIBRARIES=1
ONLY_CURRENT=1

assets
├── One Movie
│   └── Star Wars (1977) {imdb-tt0076759} {tmdb-11}
│       ├── background.jpg
│       └── poster.jpg
└── One Show
    ├── Adam-12 (1968) {tvdb-78686}
    │   ├── S01E01.jpg
    │   ├── S01E02.jpg
...
    │   ├── Season01.jpg
    │   ├── background.jpg
    │   └── poster.jpg
    └── Adam-12 Collection
        └── poster.jpg
```

Use PMM Asset-directory naming, split by Plex library name, split by first letter, split by item name:
```
USE_ASSET_NAMING=1
USE_ASSET_FOLDERS=1
ASSETS_BY_LIBRARIES=1
ONLY_CURRENT=1
USE_ASSET_SUBFOLDERS=1

assets
├── One Movie
│   └── S
│       └── Star Wars (1977) {imdb-tt0076759} {tmdb-11}
│           ├── background.jpg
│           └── poster.jpg
└── One Show
    ├── A
    │   ├── Adam-12 (1968) {tvdb-78686}
    │   │   ├── S01E01.jpg
    │   │   ├── S01E02.jpg
...
    │   │   ├── Season01.jpg
    │   │   ├── background.jpg
    │   │   └── poster.jpg
    └── Collections
        └── Adam-12 Collection
            └── poster.jpg
```

## grab-all-status.py

Perhaps you want to move or restore watch status from one server to another [or to a rebuild]

This script will retrieve all watched items for all libraries on a given plex server.  It stores them in a tab-delimited file.

Script-specific variables in .env:
```
PLEX_OWNER=yournamehere                      # account name of the server owner
```

### Usage
1. setup as above
2. Run with `python grab-all-status.py`

```
Connecting to https://cp1.DOMAIN.TLD...
------------ chazlarson ------------
------------ Movies - 4K ------------
chazlarson      movie   Movies - 4K     It Comes at Night       2017    R
chazlarson      movie   Movies - 4K     Mad Max: Fury Road      2015    R
chazlarson      movie   Movies - 4K     Rio     2011    G
chazlarson      movie   Movies - 4K     Rocky   1976    PG
chazlarson      movie   Movies - 4K     The Witch       2015    R
------------ Movies - 4K DV ------------
chazlarson      movie   Movies - 4K DV  It Comes at Night       2017    R
chazlarson      movie   Movies - 4K DV  Mad Max: Fury Road      2015    R
...
```

The file contains one row per user/library/item:

```
chazlarson      movie   Movies - 4K     It Comes at Night       2017    R
chazlarson      movie   Movies - 4K     Mad Max: Fury Road      2015    R
chazlarson      movie   Movies - 4K     Rio     2011    G
chazlarson      movie   Movies - 4K     Rocky   1976    PG
chazlarson      movie   Movies - 4K     The Witch       2015    R
chazlarson      movie   Movies - 4K DV  It Comes at Night       2017    R
chazlarson      movie   Movies - 4K DV  Mad Max: Fury Road      2015    R
...
```

## apply-all-status.py

This script reads the file produces by the previous script and applies the watched status for each user/library/item

Script-specific variables in .env:
```
TARGET_PLEX_URL=https://plex.domain2.tld
TARGET_PLEX_TOKEN=PLEX-TOKEN-TWO
TARGET_PLEX_OWNER=yournamehere
LIBRARY_MAP={"LIBRARY_ON_PLEX":"LIBRARY_ON_TARGET_PLEX", ...}
```

These values are for the TARGET of this script; this is easier than requiring you to edit the PLEX_URL, etc, when running the script.

If the target Plex has different library names, you can map one to the other in LIBRARY_MAP.

For example, if the TV library on the source Plex is called "TV - 1080p" and on the target Plex it's "TV Shows on SpoonFlix", you'd map that with:

```
LIBRARY_MAP={"TV - 1080p":"TV Shows on SpoonFlix"}
```
And any records from the status.txt file that came from the "TV - 1080p" library on the source Plex would get applied to the "TV Shows on SpoonFlix" library on the target.

### Usage
1. setup as above
2. Run with `python apply-all-status.py`

```
connecting to https://cp1.DOMAIN.TLD...

------------ Movies - 4K ------------
Searching for It Comes at Night                                                      Marked watched for chazlarson
...
```

There might be a problem with special characters in titles.


## show-all-playlists.py

Perhaps you want to creep on your users and see what they have on their playlists

This script will list the contents of all playlists users have created [except the owner's, since you already have access to those].

Script-specific variables in .env:
```
NONE
```

****
### Usage
1. setup as above
2. Run with `python show-all-playlists.py`

```
connecting to https://cp1.DOMAIN.TLD...

------------ ozzy ------------
------------ ozzy playlist: Abbott Elementary ------------
episode - Abbott Elementary s01e01 Pilot
episode - Abbott Elementary s01e02 Light Bulb
episode - Abbott Elementary s01e03 Wishlist
episode - Abbott Elementary s01e04 New Tech
episode - Abbott Elementary s01e05 Student Transfer
episode - Abbott Elementary s01e06 Gifted Program
episode - Abbott Elementary s01e07 Art Teacher
------------ ozzy playlist: The Bear ------------
episode - The Bear s01e01 System
episode - The Bear s01e02 Hands
...
------------ tony ------------
------------ tony playlist: Specials ------------
movie   - Comedy Central Roast of James Franco
movie   - Comedy Central Roast of Justin Bieber
movie   - Comedy Central Roast of Bruce Willis
------------ tony playlist: Ted ------------
movie   - Ted
movie   - The Invisible Man
movie   - Ace Ventura: When Nature Calls
...
```

## delete_collections.py

Perhaps you want to delete all the collections in one or more libraries

This script will simply delete all collections from the libraries specified in the config, except those listed.

Script-specific variables in .env:
```
KEEP_COLLECTIONS=bing,bang                      # comma-separated list of collections to keep
```
****
### Usage
1. setup as above
2. Run with `python delete_collections.py`

```
39 collection(s) retrieved...****
Collection delete - Plex |█████████▎                              | ▂▄▆ 9/39 [23%] in 14s (0.6/s, eta: 27s)
-> deleting: 98 Best Action Movies Of All Time
```

## refresh-metadata.py

Perhaps you want to refresh metadata in one or more libraries; there are situations where refreshing the whole library doesn't work so you have to do it in groups, which can be tiring.

This script will simply loop through the libraries specified in the config, refreshing each item in the library.  It waits for the specified DELAY between each.

Script-specific variables in .env:
```
NONE
```
****
### Usage
1. setup as above
2. Run with `python refresh-metadata.py`

```
getting items from [TV Shows - 4K]...
looping over 1086 items...
[========================================] 100.1% ... Zoey's Extraordinary Playlist - DONE

getting items from [ TV Shows - Anime]...
looping over 2964 items...
[========================================] 100.0% ... Ōkami Shōnen Ken - DONE
```

## actor-count.py

Perhaps you want a list of actors with a count of how many movies from your libraries they have been in.

This script connects to a plex library, and grabs all the items.  For each item, it then gets the cast from TMDB and keeps track across all items how many times it sees each actor within the list, looking down to a configurable depth.  For TV libraries, it's pulling the cast at the show level, and I haven't yet done any research to see if guest stars from individual episodes show up in that list.

At the end, it produces a list of a configurable size in descending order of number of appearances.

Script-specific variables in .env:
```
CAST_DEPTH=20                   ### HOW DEEP TO GO INTO EACH MOVIE CAST
TOP_COUNT=10                    ### PUT THIS MANY INTO THE FILE AT THE END
ACTORS_ONLY=False               ### ONLY CONSIDER CAST MEMBERS "KNOWN FOR" ACTING
```

`CAST_DEPTH` is meant to prevent some journeyman character actor from showing up in the top ten; I'm thinking of someone like Clint Howard who's been in the cast of many movies, but I'm guessing when you think of the top ten actors in your library you're not thinking about Clint.  Maybe you are, though, in which case set that higher.

`TOP_COUNT` is the number of actors to show in the list at the end.

Every person in the cast list has a "known_for_department" attribute on TMDB.  If you set `ACTORS_ONLY=True`, then people who don't have "Acting" in that field will be excluded.  Turning this on may slightly distort results.  For example, Harold Ramis is the second lead in "Stripes" and "Ghostbusters", but he is primarily known for "Directing" according to TMDB, so if you turn this flag on he doesn't get counted at all.

### Usage
1. setup as above
1. Run with `python actor-count.py`

```
connecting to https://plex.bing.bang...
getting items from [Movies - 4K DV]...
Completed loading 1996 items from Movies - 4K DV
looping over 1996 items...
[======----------------------------------] 15.0% ... Captain America: Civil War    
```

It will go through all your movies, and then at the end print out however many actors you specified in TOP_COUNT.

Sample results for the library above:

CAST_DEPTH=20
TOP_COUNT = 10
```
30      Samuel L. Jackson - 2231
22      Idris Elba - 17605
22      Tom Hanks - 31
21      Woody Harrelson - 57755
21      Gary Oldman - 64
21      Tom Cruise - 500
21      Morgan Freeman - 192
21      Sylvester Stallone - 16483
20      Willem Dafoe - 5293
20      Laurence Fishburne - 2975
```

CAST_DEPTH=40
TOP_COUNT=10
```
33      Samuel L. Jackson - 2231
24      John Ratzenberger - 7907
23      Tom Hanks - 31
22      Bruce Willis - 62
22      Gary Oldman - 64
22      Idris Elba - 17605
22      Morgan Freeman - 192
21      Woody Harrelson - 57755
21      Fred Tatasciore - 60279
21      Tom Cruise - 500
```

Note that the top ten changed dramatically due to looking deeper into the cast lists.

