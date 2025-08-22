# Plex scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Setup

See the top-level [README](../README.md) for setup instructions.

All these scripts use the same `config.yaml` and requirements.

NOTE: on 08-22-2025 these scripts have changed to using a yaml config rather than an env file.  TYOu will need to transfer your settings manually from one to the other.

### `config.template.yaml` contents

```yaml
plex_api:
  header_identifier: "media-scripts"
  timeout: 360
  auth_server:
    base_url: 'YOUR_PLEX_URL'
    token: 'YOUR_PLEX_TOKEN'
  log:
    backup_count: 3
    format: "%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s"
    level: "INFO"
    path: "plexapi.log"
    rotate_bytes: 512000
    show_secrets: 0
  skip_verify_ssl: 0

general:
  tmdb_key: "TMDB_API_KEY" # https://developers.themoviedb.org/3/getting-started/introduction
  tvdb_key: "TVDB_V4_API_KEY" # currently not used; https://thetvdb.com/api-information
  delay: 1 # optional delay between items
  library_names: Movies,TV Shows,Movies 4K # comma-separated list of libraries to act on
  superchat: 0

kometa:
  config_dir: /kometa/is/here

image_download:
  what_to_grab:
    ### collection-related
    include_collection_artwork: 1 # should get-all-posters retrieve collection posters?
    only_collection_artwork: 0 # should get-all-posters retrieve ONLY collection posters?
    only_these_collections: "Bing|Bang|Boing" # only grab artwork for these collections and items in them

    ### tv-related
    seasons: 1 # should get-all-posters retrieve season posters?
    episodes: 1 # should get-all-posters retrieve episode posters? [requires GRAB_SEASONS]

    ### background-related
    backgrounds: 1 # should get-all-posters retrieve backgrounds?
    artwork: 1 # current background is downloaded with current poster

    ### quantity-related
    only_current: 0 # should get-all-posters retrieve ONLY current artwork?
    poster_depth: 20 # grab this many posters [0 grabs all] [ONLY_CURRENT overrides this]

    ### what-to-keep
    keep_junk: 0 # keep files that script would normally delete [incorrect filetypes, mainly]
    find_overlaid_images: 0 # check all downloaded images for overlays
    retain_overlaid_images: 0 # keep images that have an overlay EXIF tag [this will override the following two]
    retain_kometa_overlaid_images: 0 # keep images that have the Kometa overlay EXIF tag
    retain_tcm_overlaid_images: 0 # keep images that have the TCM overlay EXIF tag

  ## where-to-put-it
  where_to_put_it:
    use_asset_naming: 1 # should grab-all-posters name images to match Kometa's Asset Directory requirements?
    use_asset_folders: 1 # should those Kometa-Asset-Directory names use asset folders?
    use_asset_subfolders: 0 # create asset folders in subfolders ["Collections", "Other", or [0-9, A-Z]] ]
    assets_by_libraries: 1 # should those Kometa-Asset-Directory images be sorted into library folders?
    asset_dir: "assets" # top-level directory for those Kometa-Asset-Directory images
    # if asset-directory naming is on, the next three are ignored
    poster_dir: "extracted_posters" # put downloaded posters here
    current_poster_dir: "current_posters" # put downloaded current posters and artwork here
    poster_consolidate: 0 # if false, posters are separated into folders by library

  ## tracking
  tracking:
    track_urls: 1 # If set to 1, URLS are tracked and won't be downloaded twice
    track_completion: 1 # If set to 1, movies/shows are tracked as complete by rating id
    track_image_sources: 1 # keep a file containing file names and source URLs

  ## general
  general:
    poster_download: 1 # if false, generate a script rather than downloading
    folders_only: 0 # Just build out the folder hierarchy; no image downloading
    default_years_back: 2 # in absence of a "last run date", grab things added this many years back.
    # 0 sets the fallback date to the beginning of time
    threaded_downloads: 0 # should downloads be done in the background in threads?
    reset_libraries: "Bing,Bang,Boing" # reset "last time" count to the fallback date for these libraries
    reset_collections: "Bing,Bang,Boing" # CURRENTLY UNUSED
    add_source_exif_comment: 1 # CURRENTLY UNUSED

status:
  plex_owner: "yournamehere" # account name of the server owner
  target_plex_url: "https://plex.domain2.tld" # As above, the target of apply_all_status
  target_plex_token: "PLEX-TOKEN-TWO" # As above, the target of apply_all_status
  target_plex_owner: "yournamehere" # As above, the target of apply_all_status
  library_map: '{"LIBRARY_ON_PLEX":"LIBRARY_ON_TARGET_PLEX", ...}'
  # In apply_all_status, map libraries according to this JSON.

reset_posters:
  track_reset_status: 1 # should reset-posters-* keep track of status and pick up where it left off?
  clear_reset_status: 0
  local_reset_archive: 1 # should reset-posters-tmdb keep a local archive of posters?
  override_overlay_status: 0
  target_labels: this label, that label # comma-separated list of labels to reset posters on
  remove_labels: 0 # attempt to remove the TARGET_LABELs from items after resetting the poster
  reset_seasons: 1 # reset-posters-* resets season artwork as well in TV libraries
  reset_episodes: 1 # reset-posters-* resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
  retain_reset_status_file: 0 # Don't delete the reset progress file at the end
  flush_status_at_start: 0 # Delete the reset progress file at the start instead of reading it
  reset_seasons_with_series: 0 # If there isn't a season poster, use the series poster
  dry_run: 0 # [currently only works with reset-posters-*]; don't actually do anything, just log

list_item_ids:
  include_collection_members: 0
  only_collection_members: 0

delete_collection:
  keep_collections: "bing,bang" # List of collections to keep

refresh_metadata:
  refresh_1970_only: 1 # If 1, only refresh things that have an originally-available date of 1970-01-01

rematch_items:
  unmatched_only: 1 # If 1, only rematch things that are currently unmatched

reset_added_at:
  adjust_date_futures_only: 0 # Only look at items that show up as added in the future
  adjust_date_epoch_only: 1 # Only adjust items that have "originally available" dates of `1970-01-01`

actor:
  cast_depth: 20 # how deep to go into the cast for actor collections
  top_count: 10 # how many actors to export
  job_type: "Actor"
  known_for_only: 0 # ignore cast members who are not primarily known as actors
  build_collections: 0 # build yaml for Kometa config.yml
  num_collections: 20 # this many actors in Kometa yaml
  track_gender: 1 # Pay attention to actor gender [as recorded on TMDB]
  min_gender_none: 5 # include minimum this many "none" gendered actors in the YAML, if possible
  min_gender_female: 5 # include minimum this many "female" gendered actors in the YAML, if possible
  min_gender_male: 5 # include minimum this many "male" gendered actors in the YAML, if possible
  min_gender_nb: 5 # include minimum this many "non-binary" gendered actors in the YAML, if possible

low_poster_count:
  poster_threshold: 10 # how many posters counts as a "low" count?

crew:
  depth: 20
  count: 100
  target_job: Director
  show_jobs: 0
```

## Scripts:
1. [adjust-added-dates.py](#adjust-added-datespy) - fix broken added and perhaps originally available dates in your library
1. [user-emails.py](#user-emailspy) - extract user emails from your shares
1. [reset-posters-tmdb.py](#reset-posters-tmdbpy) - reset all artwork in a library to TMDB default
1. [reset-posters-plex.py](#reset-posters-plexpy) - reset all artwork in a library to Plex default
1. [grab-all-IDs.py](#grab-all-IDspy) - grab [into a sqlite DB] ratingKey, IMDB ID, TMDB ID, TVDB ID for everything in a library from plex
1. [grab-all-posters.py](#grab-all-posterspy) - grab some or all of the artwork for a library from plex
1. [image_picker.py](#image_pickerpy) - Replaced by [Plex Image Picker](../Plex%20Image%20Picker/)
1. [grab-all-status.py](#grab-all-statuspy) - grab watch status for all users all libraries from plex
1. [apply-all-status.py](#apply-all-statuspy) - apply watch status for all users all libraries to plex from the file emitted by the previous script
1. [show-all-playlists.py](#show-all-playlistspy) - Show contents of all user playlists
1. [delete-collections.py](#delete-collectionspy) - delete most or all collections from one or more libraries
1. [refresh-metadata.py](#refresh-metadatapy) - Refresh metadata individually on items in a library
1. [list-item-ids.py](#list-item-idspy) - Generate a list of IDs in libraries and/or collections
1. [actor-count.py](#actor-countpy) - Generate a list of actor credit counts
1. [crew-count.py](#crew-countpy) - Generate a list of crew credit counts
1. [list-low-poster-counts.py](#list-low-poster-countspy) - Generate a list of items that have fewer than some number of posters in Plex


## adjust-added-dates.py

You have things in your library that show up added in the future, or way in the past.

This script will set the "added at" date and "originally available" date to match the thing's release date as found on TMDB, if the values set in Plex are more than a day or so off the TMDB release date.

Script-specific variables in `config.yaml`:
```yaml
reset_added_at:
  adjust_date_futures_only: 0 # Only look at items that show up as added in the future
  adjust_date_epoch_only: 1 # Only adjust items that have "originally available" dates of `1970-01-01`

```

### Usage
1. setup as above
2. Run with `python adjust-added-dates.py`


## user-emails.py

You want a list of email addresses for all the people you share with.

Here is a quick and dirty [emphasis on "quick" and "dirty"] way to do that.

### Usage
1. setup as above
2. Run with `python user-emails.py`

The script will loop through all the shared users on your account and spit out username and email address.

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

This script will set the poster for every series or movie to the default poster from TMDB/TVDB.  It also saves that poster under `./posters/[movies|shows]/<rating_key>.ext` in case you want to use them with Kometa's overlay resets.

If there is a file already located at `./posters/[movies|shows]/<rating_key>.ext`, the script will use *that image* instead of retrieving a new one, so if you replace that local one with a poster of your choice, the script will use the custom one rather than the TMDB/TVDB default.

Script-specific variables in `config.yaml`:
```yaml
reset_posters:
  track_reset_status: 1 # should reset-posters-* keep track of status and pick up where it left off?
  clear_reset_status: 0
  local_reset_archive: 1 # should reset-posters-tmdb keep a local archive of posters?
  override_overlay_status: 0
  target_labels: this label, that label # comma-separated list of labels to reset posters on
  remove_labels: 0 # attempt to remove the TARGET_LABELs from items after resetting the poster
  reset_seasons: 1 # reset-posters-* resets season artwork as well in TV libraries
  reset_episodes: 1 # reset-posters-* resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
  retain_reset_status_file: 0 # Don't delete the reset progress file at the end
  flush_status_at_start: 0 # Delete the reset progress file at the start instead of reading it
  reset_seasons_with_series: 0 # If there isn't a season poster, use the series poster
  dry_run: 0 # [currently only works with reset-posters-*]; don't actually do anything, just log
```

If you set:
```yaml
  track_reset_status: 1
```
The script will keep track of where it is and will pick up at that point on subsequent runs.  This is useful in the event of a lost connection to Plex.

Once it gets to the end of the library successfully, the tracking file is deleted.  If you want to disable that for some reason, set `RETAIN_RESET_STATUS_FILE` to 1

If you want to reset any existing progress tracking and start from the beginning for some reason, set `FLUSH_STATUS_AT_START` to 1.

If you specify a comma-separated list of labels in the env file:
```yaml
  target_labels: this label, that label
```
The script will reset posters only on movies with those labels assigned.

If you also set:
```yaml
  remove_labels: 1
```
The script will *attempt* to remove those labels after resetting the poster.  I say "attempt" since in testing I have experienced an odd situation where no error occurs but the label is not removed.  My test library of 230 4K-Dolby Movies contains 47 that fail in this way; every run it goes through the 47 movies "removing labels" without error yet they still have the labels on the next run.

Besides that Heisenbug, I don't recommend using this [`remove_labels`] since the label removal takes a long time [dozens of seconds per item].  Doing this through the Plex UI is much faster.

If you set:
```yaml
  local_reset_archive: 1
```
The script will set the artwork by sending the TMDB URL to Plex, without downloading the file locally first.  This means a faster run compared to the initial run when downloading.

Example timings on a test library of 1140 TV Shows, resetting artwork for Show-Season-Episode level:

1. No downloading: 1 hour 25 minutes
1. With downloading: 2 hours 30 minutes
2. Second run with downloaded archive: 1 hours 10 minutes

That is on a system with a 1G connection up and down, so values are just relative to each other.

The value of the local archive is that if you want to replace some of those images with your own, it provides a simple way to update all the posters in a library to custom posters of your own.  When the script runs, it looks at that archive first, only downloading an image if one doesn't exist in the archive.

In that way it's sort of like Kometa's Asset Directory.

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

Script-specific variables in `config.yaml`:
```yaml
reset_posters:
  track_reset_status: 1 # should reset-posters-* keep track of status and pick up where it left off?
  clear_reset_status: 0
  local_reset_archive: 1 # should reset-posters-tmdb keep a local archive of posters?
  override_overlay_status: 0
  target_labels: this label, that label # comma-separated list of labels to reset posters on
  remove_labels: 0 # attempt to remove the TARGET_LABELs from items after resetting the poster
  reset_seasons: 1 # reset-posters-* resets season artwork as well in TV libraries
  reset_episodes: 1 # reset-posters-* resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
  retain_reset_status_file: 0 # Don't delete the reset progress file at the end
  flush_status_at_start: 0 # Delete the reset progress file at the start instead of reading it
  reset_seasons_with_series: 0 # If there isn't a season poster, use the series poster
  dry_run: 0 # [currently only works with reset-posters-*]; don't actually do anything, just log
```

Same as `reset-posters-tmdb.py`, but it resets the artwork to the first item in Plex's own list of artwork, rather than downloading a new image from TMDB.

With `reset_seasons_with_series: 1`, if the season doesn't have artwork the series artwork will be used instead.

## grab-all-IDs.py

Perhaps you want to gather all the IDs for everything in a library.

This script will go through a library and grab PLex RatingKey [which may be unique], IMDB ID, TMDB ID, and TVDB ID for everything in the list of libraries specified in the `config.yaml`.  It stores the data in a sqlite database called `ids.sqlite`; the repo copy of this file contains that data for 105871 movies and 26699 TV Shows.


## grab-all-posters.py

Perhaps you want to get local copies of some or all the posters Plex knows about for everything in a library.

Maybe you find it easier to look through a bunch of options in CoverFlow or something.

Maybe you want to grab all the current custom art in a library to put in a Kometa asset directory or back it up for some other purpose.

This script will download some or all the posters for every item in a given set of libraries.  It (probably) won't download the same thing more than once, so you can cancel it and restart it if need be.  I say "probably" because the script is assuming that the list of posters retrieved from Plex is always in the same order [i.e. that new posters get appended to the end of the list].  On subsequent runs, the script checks only that a target file exists.  It doesn't pay any attention to whether the two [the one on disk vs. the one coming from Plex] are the same image.  I'll probably add a check to look at the image URL to attempt to ameliorate this at some point.

The script can name these files so that they are ready for use with [Kometa's Asset Directory](https://metamanager.wiki/en/latest/home/guides/assets.html).  This only works with `ONLY_CURRENT` set, since Kometa has no provision for multiple assets for a given thing.

If you have downloaded more than one image for each thing, see [image_picker.py](#image_pickerpy) for a simpler way to choose which one you want to make active.

If threaded downloads are enabled, the script queues downloads so they happen in the background in multiple threads.  Once it's gone through the libraries listed in the config, it will then wait until the queue is drained before exiting.  If you want to drop out of the library-scanning loop early, create a file `stop.dat` next to the script, and the library loop will exit at the end of the current show or movie, then go to the "waiting for the downloads" section.  This allows you to get out early without flushing the queue [as control-C would do].

You can also skip the current library by creating `skip.dat`.

Script-specific variables in `config.yaml`:
```yaml
image_download:
  what_to_grab:
    ### collection-related
    include_collection_artwork: 1 # should get-all-posters retrieve collection posters?
    only_collection_artwork: 0 # should get-all-posters retrieve ONLY collection posters?
    only_these_collections: "Bing|Bang|Boing" # only grab artwork for these collections and items in them

    ### tv-related
    seasons: 1 # should get-all-posters retrieve season posters?
    episodes: 1 # should get-all-posters retrieve episode posters? [requires GRAB_SEASONS]

    ### background-related
    backgrounds: 1 # should get-all-posters retrieve backgrounds?
    artwork: 1 # current background is downloaded with current poster

    ### quantity-related
    only_current: 0 # should get-all-posters retrieve ONLY current artwork?
    poster_depth: 20 # grab this many posters [0 grabs all] [ONLY_CURRENT overrides this]

    ### what-to-keep
    keep_junk: 0 # keep files that script would normally delete [incorrect filetypes, mainly]
    find_overlaid_images: 0 # check all downloaded images for overlays
    retain_overlaid_images: 0 # keep images that have an overlay EXIF tag [this will override the following two]
    retain_kometa_overlaid_images: 0 # keep images that have the Kometa overlay EXIF tag
    retain_tcm_overlaid_images: 0 # keep images that have the TCM overlay EXIF tag

  ## where-to-put-it
  where_to_put_it:
    use_asset_naming: 1 # should grab-all-posters name images to match Kometa's Asset Directory requirements?
    use_asset_folders: 1 # should those Kometa-Asset-Directory names use asset folders?
    use_asset_subfolders: 0 # create asset folders in subfolders ["Collections", "Other", or [0-9, A-Z]] ]
    assets_by_libraries: 1 # should those Kometa-Asset-Directory images be sorted into library folders?
    asset_dir: "assets" # top-level directory for those Kometa-Asset-Directory images
    # if asset-directory naming is on, the next three are ignored
    poster_dir: "extracted_posters" # put downloaded posters here
    current_poster_dir: "current_posters" # put downloaded current posters and artwork here
    poster_consolidate: 0 # if false, posters are separated into folders by library

  ## tracking
  tracking:
    track_urls: 1 # If set to 1, URLS are tracked and won't be downloaded twice
    track_completion: 1 # If set to 1, movies/shows are tracked as complete by rating id
    track_image_sources: 1 # keep a file containing file names and source URLs

  ## general
  general:
    poster_download: 1 # if false, generate a script rather than downloading
    folders_only: 0 # Just build out the folder hierarchy; no image downloading
    default_years_back: 2 # in absence of a "last run date", grab things added this many years back.
    # 0 sets the fallback date to the beginning of time
    threaded_downloads: 0 # should downloads be done in the background in threads?
    reset_libraries: "Bing,Bang,Boing" # reset "last time" count to the fallback date for these libraries
    reset_collections: "Bing,Bang,Boing" # CURRENTLY UNUSED
    add_source_exif_comment: 1 # CURRENTLY UNUSED
```

The point of `poster_depth` is that sometimes movies have an insane number of posters, and maybe you don't want all 257 Endgame posters or whatever.  Or maybe you want to download them in batches.

If `poster_download` is `0`, the script will build a shell/batch script for each library to download the images at your convenience instead of downloading them as it runs, so you can run the downloads overnight or on a different machine with ALL THE DISK SPACE or something.

If `poster_consolidate` is `1`, the script will store all the images in one directory rather than separating them by library name.  The idea is that Plex shows the same set of posters for "Star Wars" whether it's in your "Movies" or "Movies - 4K" or whatever other libraries, so there's no reason to pull the same set of posters multiple times.  There is an example below.

If `include_collection_artwork` is `1`, the script will grab artwork for all the collections in the target library.

If `only_collection_artwork` is `1`, the script will grab artwork for ONLY the collections in the target library; artwork for individual items [movies, shows] will not be grabbed.

If `only_these_collections` is not empty, the script will grab artwork for ONLY the collections listed and items contained in those collections.  This doesn't affect the sorting or naming, just the filter applied when asking Plex for the items.  IF YOU DON'T CHANGE THIS SETTING, NOTHING WILL BE DOWNLOADED.

If `track_urls` is `1`, the script will track every URL it downloads in a sqlite database.  On future runs, if a given URL is found in that database it won't be downloaded a second time.  This may save time if the same URL appears multiple times in the list of posters from Plex.

If `track_completion` is `1`, the script records collections/movies/shows/seasons/episodes by rating key in a sqlite database.  On future runs, if a given rating key is found in that database the thing is considered complete and it will be skipped.  This will save time in subsequent runs as the script will not look through all the images for a thing only to determine that it's already downloaded all of them.  HOWEVER, this also means that if you increase `poster_depth`, those additional images won't be picked up when you run the script again, since the item will be marked as complete.

The script keeps track of the last date it retrieved items from a library [for show libraries it also tracks seasons and episodes separately], and on each run will only retrieve items added since that date.  If there is no "last run date" for a given thing, the script uses a fallback "last run" date of today - `default_years_back`.

If `default_years_back` = 0, the fallback date is "the beginning of time".  There is one other circumstance that will result in a fallback date of "the beginning of time".

If:
1. You are running Windows
2. `default_years_back` is > 0
3. the calculated fallback date is before 01/01/1970

Then the "beginning of time" fallback date will be used.  This is a Windows issue.

Normally, this fallback date is used *only* if there is no last-run date stored, for example the first time you run the script.  This means that if you run the script once with `default_years_back: 2` then change that to `default_years_back: 0`, nothing new will be downloaded.  The script will read the last run date from its database and will never look at the new fallback date.

You can use `reset_libraries` to force the "last run date" to that fallback date for one or more libraries.

If you want to reset all libraries and clear all history, delete `mediascripts.sqlite`.

For example:

You run `grab-all-posters` with `default_years_back: 2`; it downloads posters for half your "Movies" library.  Now you want to grab all the rest.  You change that to `default_years_back: 0` and run `grab-all-posters` again.  Nothing new will be downloaded since the last run date is now the time of that first run, and nothing has been added to Plex since then.  If you want to grab all posters from the beginning of time for that library, set:
```yaml
  default_years_back: 0
  reset_libraries: Movies
```
That will set the fallback date to "the beginning of time" and apply that new fallback date to the "Movies" library only.

If `find_overlaid_images` is `1`, the script checks every imnage it downloads for the EXIF tag that indicates Kometa created it.  If found, the image is deleted.  You can override the deleting with `retain_kometa_overlaid_images` and/or `retain_tcm_overlaid_images`.

If `retain_kometa_overlaid_images` is `1`, those images with the Kometa EXIF tag are **not** deleted.

If `retain_tcm_overlaid_images`` is `1`, those images with the Kometa EXIF tag are **not** deleted.

If `retain_overlaid_images` is `1`, the previous two settings will be forced to `0` and all overlaid images will be retained.  This is a older deprecated setting.

NOTE: `only_current` and `poster_depth` do not take these images into account, meaning that if you have:
```yaml
  only_current: 1
  retain_kometa_overlaid_images: 0
```
Then nothing will be retained for items with overlaid posters.  `grab-all-posters` will download the current art, find that it has an overlay, delete it, then go to the next movie/show.

Similarly:
```yaml
  only_current: 0
  poster_depth: 20
  retain_kometa_overlaid_images: 0
```
This won't grab images until you have 20 downloaded.  It will grab 20 images, and if ten are found to have overlays, those ten will be deleted and you will end up with 10.

### Usage
1. setup as above
2. Run with `python grab-all-posters.py`

The posters will be sorted by library [if enabled] with each poster getting an incremented number, like this:

The image names are: `title-source-location-INCREMENT.ext`

`source` is where plex reports it got the image: tmdb, fanarttv, gracenote, etc. This will alaways be "None" for collection images since they are provided by the user or generated [the four-poster ones] by Plex.

`location` will be `local` or `remote` depending whether the URL pointed to the plex server or to some other site like tmdb.

The folder structure in which the images are saved is controlled by a combination of settings; please review the examples below to find the format you want and the settings that you need to generate it.

All movies and TV shows in a single folder:
```yaml
  poster_consolidate: 1
```
```shell
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

Split by Plex library name ['Movies' and 'TV Shows' are Plex library names]:
```yaml
  poster_consolidate: 0
```
```shell
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

Use Kometa Asset-directory naming, flat:
```yaml
image_download:
  what_to_grab:
    only_current: 1
  where_to_put_it:
    use_asset_naming: 1
    use_asset_folders: 0
    assets_by_libraries: 0
```
```shell
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

Use Kometa Asset-directory naming, movies and TV in a single directory, split by item name:
```yaml
image_download:
  what_to_grab:
    only_current: 1 # OR poster_depth: 1
  where_to_put_it:
    use_asset_naming: 1
    use_asset_folders: 1
    assets_by_libraries: 0
```
```shell
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

Use Kometa Asset-directory naming, split by Plex library name, flat folder:
```yaml
image_download:
  what_to_grab:
    only_current: 1
  where_to_put_it:
    use_asset_naming: 1
    use_asset_folders: 0
    assets_by_libraries: 1
```
```shell
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

Use Kometa Asset-directory naming, split by Plex library name, split by item name:
```yaml
image_download:
  what_to_grab:
    only_current: 1 # OR poster_depth: 1
  where_to_put_it:
    use_asset_naming: 1
    use_asset_folders: 1
    assets_by_libraries: 1
```
```shell
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

Use Kometa Asset-directory naming, split by Plex library name, split by first letter, split by item name:
```yaml
image_download:
  what_to_grab:
    only_current: 1 # OR poster_depth: 1
  where_to_put_it:
    use_asset_naming: 1
    use_asset_folders: 1
    assets_by_libraries: 1
    use_asset_subfolders: 1
```
```shell
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

## image_picker.py

Replaced with [Plex Image Picker](../Plex%20Image%20Picker/).

## grab-all-status.py

Perhaps you want to move or restore watch status from one server to another [or to a rebuild]

This script will retrieve all watched items for all libraries on a given plex server.  It stores them in a tab-delimited file.

Script-specific variables in `config.yaml`:
```yaml
status:
  plex_owner: "yournamehere" # account name of the server owner
```

### Usage
1. setup as above
2. Run with `python grab-all-status.py`

```shell
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

```shell
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

Script-specific variables in `config.yaml`:
```yaml
status:
  target_plex_url: "https://plex.domain2.tld" # As above, the target of apply_all_status
  target_plex_token: "PLEX-TOKEN-TWO" # As above, the target of apply_all_status
  target_plex_owner: "yournamehere" # As above, the target of apply_all_status
  library_map: '{"LIBRARY_ON_PLEX":"LIBRARY_ON_TARGET_PLEX", ...}'
  # In apply_all_status, map libraries according to this JSON.
```

These values are for the TARGET of this script; this is easier than requiring you to edit the PLEX_URL, etc, when running the script.

If the target Plex has different library names, you can map one to the other in `library_map`.

For example, if the TV library on the source Plex is called "TV - 1080p" and on the target Plex it's "TV Shows on SpoonFlix", you'd map that with:

```yaml
  library_map: '{"TV - 1080p":"TV Shows on SpoonFlix"}'
```
And any records from the status.txt file that came from the "TV - 1080p" library on the source Plex would get applied to the "TV Shows on SpoonFlix" library on the target.

### Usage
1. setup as above
2. Run with `python apply-all-status.py`

```shell
connecting to https://cp1.DOMAIN.TLD...

------------ Movies - 4K ------------
Searching for It Comes at Night                                                      Marked watched for chazlarson
...
```

There might be a problem with special characters in titles.


## show-all-playlists.py

Perhaps you want to creep on your users and see what they have on their playlists

This script will list the contents of all playlists users have created [except the owner's, since you already have access to those].

Script-specific variables in `config.yaml`:
```
NONE
```

****
### Usage
1. setup as above
2. Run with `python show-all-playlists.py`

```shell
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

## delete-collections.py

Perhaps you want to delete all the collections in one or more libraries

This script will simply delete all collections from the libraries specified in the config, except those listed.

Script-specific variables in `config.yaml`:
```yaml
delete_collection:
  keep_collections: "bing,bang" # List of collections to keep
```
****
### Usage
1. setup as above
2. Run with `python delete-collections.py`

```shell
39 collection(s) retrieved...****
Collection delete - Plex |█████████▎                              | ▂▄▆ 9/39 [23%] in 14s (0.6/s, eta: 27s)
-> deleting: 98 Best Action Movies Of All Time
```

## refresh-metadata.py

Perhaps you want to refresh metadata in one or more libraries; there are situations where refreshing the whole library doesn't work so you have to do it in groups, which can be tiring.

This script will simply loop through the libraries specified in the config, refreshing each item in the library.  It waits for the specified DELAY between each.

Script-specific variables in `config.yaml`:
```yaml
refresh_metadata:
  refresh_1970_only: 1 # If 1, only refresh things that have an originally-available date of 1970-01-01
```
****
### Usage
1. setup as above
2. Run with `python refresh-metadata.py`

```shell
getting items from [TV Shows - 4K]...
looping over 1086 items...
[========================================] 100.1% ... Zoey's Extraordinary Playlist - DONE

getting items from [ TV Shows - Anime]...
looping over 2964 items...
[========================================] 100.0% ... Ōkami Shōnen Ken - DONE
```

## list-item-ids.py

Perhaps you want a list of all the IDs of everything in your libraries or collections.

This script wil output this data into its log file:
```
on 0: INFO: 11/05/2023 05:03:04 PM This collection is called New Episodes
on 0: INFO: 11/05/2023 05:03:05 PM Collection: New Episodes item     1/  125 | TVDb ID: 411029    | IMDb ID: tt15320362  | All the Light We Cannot See
on 0: INFO: 11/05/2023 05:03:05 PM Collection: New Episodes item     2/  125 | TVDb ID: 421526    | IMDb ID: tt15475330  | Black Cake
on 0: INFO: 11/05/2023 05:03:05 PM Collection: New Episodes item     3/  125 | TVDb ID: 419379    | IMDb ID: tt15384586  | Fellow Travelers
on 0: INFO: 11/05/2023 05:03:05 PM Collection: New Episodes item     4/  125 | TVDb ID: 439494    | IMDb ID: tt10270200  | The Vanishing Triangle
```
or
```
on 5782: INFO: 11/05/2023 05:07:49 PM tem  5782/ 5786 | TMDb ID:   9398    | IMDb ID:  tt0196229  | Zoolander
on 5783: INFO: 11/05/2023 05:07:49 PM tem  5783/ 5786 | TMDb ID: 329833    | IMDb ID:  tt1608290  | Zoolander 2
on 5784: INFO: 11/05/2023 05:07:49 PM tem  5784/ 5786 | TMDb ID: 269149    | IMDb ID:  tt2948356  | Zootopia
```

env vars are the same as grab-all-posters.py for the most part [where they apply], except for:
```
INCLUDE_COLLECTION_MEMBERS=0
ONLY_COLLECTION_MEMBERS=0
```

Which probably do about what you'd expect.

### Usage
1. setup as above
2. Run with `python list-item-ids.py`

## actor-count.py

Perhaps you want a list of actors with a count of how many movies from your libraries they have been in.

This script connects to a plex library, and grabs all the items.  For each item, it then gets the cast from TMDB and keeps track across all items how many times it sees each actor within the list, looking down to a configurable depth.  For TV libraries, it's pulling the cast at the show level, and I haven't yet done any research to see if guest stars from individual episodes show up in that list.

At the end, it produces a list of a configurable size in descending order of number of appearances.

Script-specific variables in `config.yaml`:
```
actor:
  cast_depth: 20 # how deep to go into the cast for actor collections
  top_count: 10 # how many actors to export
  job_type: "Actor"
  known_for_only: 0 # ignore cast members who are not primarily known as actors
  build_collections: 0 # build yaml for Kometa config.yml
  num_collections: 20 # this many actors in Kometa yaml
  track_gender: 1 # Pay attention to actor gender [as recorded on TMDB]
  min_gender_none: 5 # include minimum this many "none" gendered actors in the YAML, if possible
  min_gender_female: 5 # include minimum this many "female" gendered actors in the YAML, if possible
  min_gender_male: 5 # include minimum this many "male" gendered actors in the YAML, if possible
  min_gender_nb: 5 # include minimum this many "non-binary" gendered actors in the YAML, if possible
```

`cast_depth` is meant to prevent some journeyman character actor from showing up in the top ten; I'm thinking of someone like Clint Howard who's been in the cast of many movies, but I'm guessing when you think of the top ten actors in your library you're not thinking about Clint.  Maybe you are, though, in which case set that higher.

`top_count` is the number of actors to show in the list at the end.

Every person in the cast list has a "known_for_department" attribute on TMDB.  If you set `known_for_only: 1`, then people who don't have "Acting" in that field will be excluded.  Turning this on may slightly distort results.  For example, Harold Ramis is the second lead in "Stripes" and "Ghostbusters", but he is primarily known for "Directing" according to TMDB, so if you turn this flag on he doesn't get counted at all.

`build_collections` will make the script build some YAML to paste into your Kometa config file to generate collections.

`num_collections` controls the number of collections in that YAML

`track_gender` controls whether the script pays attention to actor gender

`min_gender_*` control the minimum number of that gender [as recorded by TMDB] actor to include in the list [provided `track_gender: 1`]

Actors are sorted into lists by the four genders recorded at TMDB.  The top `min_gender_*` for each are added to the final list, then if there is space left over the remainder is filled from the master actor list.

If the four `min_gender_*` sum to more than `num_collections`, the script exits with an error.
### Usage
1. setup as above
1. Run with `python actor-count.py`

```shell
connecting to https://plex.bing.bang...
getting items from [Movies - 4K DV]...
Completed loading 1996 items from Movies - 4K DV
looping over 1996 items...
[======----------------------------------] 15.0% ... Captain America: Civil War
```

It will go through all your movies, and then at the end print out however many actors you specified in TOP_COUNT along with a bunch of other statistics.

Sample results for the library above:

```yaml
  cast_depth: 20
  top_count: 10
```
```shell
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

```yaml
  cast_depth: 40
  top_count: 10
```
```shell
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

## crew-count.py

Perhaps you want a list of crew members with a count of how many movies from your libraries they have been credited in.

This script connects to a plex library, and grabs all the items.  For each item, it then gets the crew from TMDB and keeps track across all items how many times it sees each individual with the configured `TARGET_JOB` within the list, looking down to a configurable depth.
At the end, it produces a list of a configurable size in descending order of number of appearances.

Script-specific variables in `config.yaml`:
```yaml
crew:
  depth: 20
  count: 100
  target_job: Director
  show_jobs: 0
```

`depth` is meant to allow the script to look deeper into the crew to find all the individuals working as TARGET_JOB.

`count` is the number of individuals to show in the list at the end.

If `show_jobs` is set to 1, the script will also output a list of all the jobs it saw, if you want a reference to what may be available.

### Usage
1. setup as above
1. Run with `python crew-count.py`

```shell
connecting to Plex...
getting items from [Test-Movies]...
looping over 35 items...
[=========================================] 102.9% ... Wild Gals of the Naked West
```

It will go through all your movies, and then at the end print out however many actors you specified in TOP_COUNT along with a bunch of other statistics.

Sample results for the library above:

```yaml
crew:
  depth: 20
  count: 100
  target_job: Director
  show_jobs: 0
```
```shell
Top 27 Director in [Test-Movies]:
3       Jules Bass - 16410
3       Arthur Rankin, Jr. - 16411
2       Peyton Reed - 59026
2       Pierre Coffin - 124747
2       Chris Renaud - 124748
2       Robert Wise - 1744
2       Nicholas Meyer - 1788
2       Leonard Nimoy - 1749
2       Jonathan Frakes - 2388
1       Ed Herzog - 219492
1       Zack Snyder - 15217
1       Noam Murro - 78914
1       Edward Berger - 221522
1       Bob Fosse - 66777
1       Jean-Pierre Jeunet - 2419
1       Dario Argento - 4955
1       Hideaki Anno - 77921
1       George Miller - 20629
1       Larry Roemer - 144977
1       Søren Fauli - 110047
1       William Shatner - 1748
1       David Carson - 2380
1       Stuart Baird - 2523
1       Richard Marquand - 19800
1       Jūzō Itami - 69167
1       Michael Boyle - 2754307
1       Russ Meyer - 4590
```

```yaml
crew:
  depth: 5
  count: 100
  target_job: Director
```
```shell
Top 22 Director in [Test-Movies]:
3       Jules Bass - 16410
3       Arthur Rankin, Jr. - 16411
2       Peyton Reed - 59026
2       Pierre Coffin - 124747
2       Chris Renaud - 124748
2       Leonard Nimoy - 1749
1       Ed Herzog - 219492
1       Zack Snyder - 15217
1       Noam Murro - 78914
1       Bob Fosse - 66777
1       Dario Argento - 4955
1       Hideaki Anno - 77921
1       George Miller - 20629
1       Larry Roemer - 144977
1       Søren Fauli - 110047
1       Nicholas Meyer - 1788
1       Jonathan Frakes - 2388
1       Stuart Baird - 2523
1       Richard Marquand - 19800
1       Jūzō Itami - 69167
1       Michael Boyle - 2754307
1       Russ Meyer - 4590
```

Note that the list changed due to the different depth; apparently Robert Wise's Director credit is more than 5 entries into the list.

## list-low-poster-counts.py

Perhaps you want to know which movies have fewer than 4 posters avaiable in Plex.

Script-specific variables in `config.yaml`:
```yaml
low_poster_count:
  poster_threshold: 10 # how many posters counts as a "low" count?
```

### Usage
1. setup as above
2. Run with `python list-low-poster-counts.py`

Starting list-low-poster-counts 0.1.0 at 2023-12-07 09:35:45
connecting to https://plex.bing.bang...
Loading Movies ...
Completed loading 6171 of 6171 movie(s) from Movies
on 15: 7 Plus Seven has 6 posters
on 52: 21 Up has 4 posters
on 77: 63 Up has 7 posters
on 94: 1962 Halloween Massacre has 8 posters
on 119: Ace in the Hole has 8 posters
Low poster counts Movies |█                                       | ▇▇▅ 162/6171 [3%] in 9s (18.6/s, eta: 5:18)
