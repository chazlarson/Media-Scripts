# Kometa scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Setup

See the top-level [README](../README.md) for setup instructions.

All these scripts use the same `config.yaml` and requirements.

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
  config_dir: /kometa/is/here # location of Kometa config dir as seen by this script

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
1. [clean-overlay-backup.py](#clean-overlay-backuppy) - clean out leftover overlay backup art
1. [extract-collections.py](#extract-collectionspy) - extract collections from a library
1. [overlay-default-posters.py](#overlay-default-posterspy) - apply overlays to default collection posters
1. [kometa-trakt-auth.py](#kometa-trakt-authpy) - generate trakt auth block for Kometa config.yml
1. [kometa-mal-auth.py](#kometa-mal-authpy) - generate mal auth block for Kometa config.yml
1. [original-to-assets.py](#original-to-assetspy) - Copy image files from an "Original Posters" directory to an asset directory
1. [metadata-extractor.py](#metadata-extractorpy) - Extract all metadata from libraries into a Kometa-compatible metadata YAML file

### OBSOLETE
1. [top-n-actor-coll.py](#top-n-actor-collpy) - generate collections for the top *n* actors in a library

## clean-overlay-backup.py

You've deleted stuff from Plex and want to clean up the leftover backup art that Kometa saved when it applied overlays

### Settings

The script uses these settings from the `config.yaml`:
```yaml
general:
  delay: 1 # optional delay between items
  library_names: Movies,TV Shows,Movies 4K # comma-separated list of libraries to act on

kometa:
  config_dir: /kometa/is/here # location of Kometa config dir as seen by this script
```

### Usage
1. setup as above
2. Run with `python clean-overlay-backup.py`

The script will catalog the backup files and current Plex contents for each library listed in the `config.yaml`.

It then compares the two lists, and any files in the backup dir that do not correspond to current items in Plkex are deleted.

```
Starting clean-overlay-backup 0.1.0 at 2024-02-13 17:52:31
connecting to https://plex.bing.bang...
6686 images in the Movies overlay backup directory ...
Loading Movies ...
Loading movies from Movies  ...
Completed loading 6965 of 6965 movie(s) from Movies
Clean Overlay Backup Movies |████████████████████████████████████████| 6965/6965 [100%] in 11.0s (633.23/s)
Processed 6965 of 6965
0 items to delete
279 items in Plex with no backup art
These might be items added to Plex since the last overlay run
They might be items that are not intended to have overlays
...
```

## extract-collections.py

You're getting started with Kometa and you want to export your existing collections

Here is a quick and dirty [emphasis on "quick" and "dirty"] way to do that.

### Usage

1. setup as above
2. Run with `python extract-collections.py`

The script will grab some details from each collection and write a metadata file that you could use with Kometa.  It also grabs artwork and background.

This is extremely naive; it doesn't recreate filters, just grabs a list of everything in each collection.

For example, you'll end up with something like this for each collection:

```yaml
collections:
  ABC:
    sort_title: +++_ABC
    url_poster: ./config/TV Shows - 4K-artwork/ABC.png
    summary: A collection of ABC content
    collection_order: release
    plex_search:
      any:
        title:
          - Twin Peaks
          - Strange World
          - Designated Survivor
          - The Good Doctor
```

## overlay-default-posters.py

You want to apply an overlay to the default collection posters; perhaps for branding, perhaps you don't like the separators, whatever

Here is a basic script to do that.

### Usage
1. setup as above
1. create overlay images in `default_collection_overlays` [see README in that folder for notes.]
1. Run with `overlay-default-posters.py`

The script will clone or update the `Kometa-Images` repo, then iterate through it applying overlays to each image and storing them in a parallel file system rooted at `Kometa-Images-Overlaid`, ready for you to use with the Kometa Asset Directory [after moving them to that directory] or via template variables.

It chooses the overlay by name based on the "group" that each collection is part of:
```
Kometa-Images
├── aspect
├── audio_language
├── award
├── based
├── chart
├── content_rating
├── country
├── decade
├── franchise
├── genre
├── network
├── playlist
├── resolution
├── seasonal
├── separators
├── streaming
├── studio
├── subtitle_language
├── universe
└── year
```

For example, all the `audio_language` collection posters will be overlaid by `Kometa/default_collection_overlays/audio_language.png`.

If there isn't a specific image for a "group", then `Kometa/default_collection_overlays/overlay-template.png` will be used.

```
Fetch/Pull on Kometa-Images
Using default_collection_overlays/overlay-template.png as global overlay
building list of targets
Applying overlays |████████████████████████████▎           | ▇▅▃ 5027/7119 [71%] in 3:53 (21.6/s, eta: 1:37)
Kometa-Images/genre/Sword & Sandal.jpg
```

## kometa-trakt-auth.py

Perhaps you're running Kometa in a docker or something where getting it into interactive mode to authentication trakt is a hassle.

This little script will generate the trakt section for your Kometa config file.  Most of this code is pulled from Kometa's own trakt authentication; it's just been simplified to do the one thing.

You can run this on a completely separate machine to where Kometa is running.

There is an online version available [here](https://metamanager.wiki/en/latest/config/auth/).

### Usage
1. Run with `python kometa-trakt-auth.py`


You'll be asked for your trakt Client ID and Client Secret then taken to a trakt web page.

Copy the PIN and paste it at the prompt.

Some yaml will be printed, ready to copy-paste into your Kometa config.yml.

```
Let's authenticate against Trakt!


Trakt Client ID: JOHNNYJOEYDEEDEE
Trakt Client Secret: PETEROGERJOHNKEITH
Taking you to: https://trakt.tv/oauth/authorize?response_type=code&client_id=JOHNNYJOEYDEEDEE&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob

If you get an OAuth error your Client ID or Client Secret is invalid

If a browser window doesn't open go to that URL manually.


Enter the Trakt pin from that web page: 9CE4045E
Copy the following into your Kometa config.yml:
############################################
trakt:
  client_id: JOHNNYJOEYDEEDEE
  client_secret: PETEROGERJOHNKEITH
  authorization:
    access_token: OZZYTONYGEEZERBILL
    token_type: Bearer
    expires_in: 7889237
    refresh_token: JOHNPAULGEORGERINGO
    scope: public
    created_at: 1644589166
############################################
```

## kometa-mal-auth.py

This little script will generate the `mal` section for your Kometa config file.  Most of this code is pulled from Kometa's own MAL authentication; it's just been simplified to do the one thing.

You can run this on a completely separate machine to where Kometa is running.

There is an online version available [here](https://metamanager.wiki/en/latest/config/auth/).

### Usage
1. `python3 -m pip install pyopenssl`
1. `python3 -m pip install requests secrets`
1. Run it with `python3 kometa-mal-auth.py`.

You'll be asked for your MyAnimeList Client ID and Client Secret then taken to a MyAnimeList web page.

Log in and click "Allow"; you'll be redirected to a localhost page that won't load.

Copy that localhost URL and paste it at the prompt.

Some yaml will be printed, ready to copy-paste into your Kometa config.yml.

```
Let's authenticate against MyAnimeList!


MyAnimeList Client ID: JOHNNYJOEYDEEDEE
MyAnimeList Client Secret: PETEROGERJOHNKEITH
We're going to open https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id=JOHNNYJOEYDEEDEE&code_challenge=STINGANDYSTEWART


Log in and click the Allow option.

You will be redirected to a localhost url that probably won't load.

That's fine.  Copy that localhost URL and paste it below.

Hit enter when ready:
URL: http://localhost/?code=TuomasEmppuTroyFloorKaiJukka


Copy the following into your Kometa config.yml:
############################################
mal:
  client_id: JOHNNYJOEYDEEDEE
  client_secret: PETEROGERJOHNKEITH
  authorization:
    access_token: OZZYTONYGEEZERBILL
    token_type: Bearer
    expires_in: 2415600
    refresh_token: JOHNPAULGEORGERINGO
############################################

```

## original-to-assets.py

You've applied overlays to a library and want to seed an asset directory with the "Original Posters".

Here is a basic script to do that.

### Usage
1. setup as above
1. Run with `original-to-assets.py`

The script will copy the contents of the "Original Posters" directory to an asset directory.

Note, this will only copy images that have received overlays, and for which the rating keys in Plex are matching.

If you don't have overlays on any episodes, this script will not put any episode images in the asset directory, and so on.

```yaml
image_download:
  where_to_put_it:
    use_asset_folders: 1 # should those Kometa-Asset-Directory names use asset folders?
    asset_dir: "assets" # top-level directory for those Kometa-Asset-Directory images
```

The asset file system will be rooted at the directory in the `asset_dir` setting, and `use_asset_folders` controls whether the images are stored as:

```yaml
    use_asset_folders: 1
```

```
Media-Scripts/Plex/assets/All That Jazz (1979) {imdb-tt0078754} {tmdb-16858}.jpg
```

or

```yaml
    use_asset_folders: 0
```

```
Media-Scripts/Plex/assets/All That Jazz (1979) {imdb-tt0078754} {tmdb-16858}/poster.jpg
```

example output:
```
Starting originals-to-assets 0.0.1 at 2024-04-01 17:13:30
connecting to https://test-plex.DOMAIN.TLD...
Loading Test-Movies ...
Loading movies  ...
Completed loading 35 of 35 movie(s) from Test-Movies
Grab all posters Test-Movies |████████████████████████████████████████| 35/35 [100%] in 0.2s (190.63/s)
Processed 35 of 35
Complete!
```

## metadata-extractor.py

You want to seed a Kometa metadata file with the contents of one or more libraries.

Here is a basic script to do that.

### Usage
1. setup as above
1. Run with `metadata-extractor.py`

The script will read all metadata from one of more libraries and format it into a Kometa-compatible metadata file.  This includes current artwork, which will be downloaded and the files linked in the metadata YAML.

IMPORTANT NOTES:

This script backs up all Kometa-supported metadata [with a few minor exceptions], which includes things you may not have changed.  It also includes the "Overlay" label.  It backs up this label because it *also* backs up the current art, which might be overlaid.  You will probably want to edit or trim this file before using it to restore.

Metadata not backed up:
```
metadata_language     Movie, Show
subtitle mode         Show, Season
content_rating        Episode
```
Generally these are because it's not obvious how to extract them from Plex and I haven't reviewed the Kometa source to see what it sets in these cases, OR the values in Plex differ from the values in Kometa and I haven't looked into why.

The match method defaults to IMDb ID, falls back to TMDB/TVDB if here is no IMDb ID, and if neither exist, uses title and year.  The edition [value or blank] is added for movies in any case.

example output:
```
Starting metadata-extractor 0.2.0 at 2024-08-16 21:20:27
connecting to http://192.168.1.11:32400...
tmdb config...
getting items from [Kometa-Demo-Movies]...
looping over 218 items...
Extracting metadata from Kometa-Demo-Movies |████████████████████████████████████████| 218/218 [100%] in 9:17.8 (0.39/s)
getting items from [Kometa-Demo-TV]...
looping over 24 items...
Extracting metadata from Kometa-Demo-TV |████████████████████████████████████████| 24/24 [100%] in 1:21.6 (0.29/s)


processed 242 items in 642.92 seconds.
```

That run produced two metadata files:
```
metadata-Kometa-Demo-Movies.yml
metadata-Kometa-Demo-TV.yml
```
And a directory of images:
```
metadata-items
├── Kometa-Demo-Movies
│   ├── imdb-tt0031381-378
│   │   ├── background.jpg
│   │   └── poster.jpg
│   ├── imdb-tt0031679-584
│   │   ├── background.jpg
│   │   └── poster.jpg
│   ├── imdb-tt0035575-1238
│   │   ├── background.jpg
...
```

## OBSOLETE SCRIPTS

## top-n-actor-coll.py

This has been obsoleted by "Dynamic Collections" in Kometa; it's left here for historical reference.

You should use Dynamic Collections instead.

Connects to a plex library, grabs all the movies.

For each movie, gets the cast from TMDB; keeps track across all movies how many times it sees each actor.  You can specify a TV library, but I haven't tested that a lot.  My one attempt showed a list of 10 actors who had each been in 1 series, which doesn't seem right.

At the end, builds a basic Kometa metadata file for the top N actors.

Script-specific variables in `config.yaml`:

```yaml
actor:
  cast_depth: 20 # how deep to go into the cast for actor collections
  top_count: 10 # how many actors to export
```

`CAST_DEPTH` is meant to prevent some journeyman character actor from showing up in the top ten; I'm thinking of someone like Clint Howard who's been in the cast of many movies, but I'm guessing when you think of the top ten actors in your library you're not thinking about Clint.  Maybe you are, though, in which case set that higher.

`TOP_COUNT` is the number of actors to dump into the metadata file at the end.

`template.tmpl` - this is the beginning of the target metadata file; change it if you like, but you're on your own there.

`collection.tmpl` - this is the collection definition inserted for each actor [`%%NAME%%%` and `%%ID%%` are placeholders that get substituted for each actor]; change it if you like, but this script only knows about those two data field substitutions.

### Usage
1. setup as above
1. Run with `python top-n-actor-coll.py`

```
connecting...
getting movies...
looping over 2819 movies...
[==--------------------------------------] 5.4% ... Annihilation
```

It will go through all your movies, and then at the end print out however many actors you specified in TOP_COUNT and produce a yml file.

```
38      2231-Samuel L. Jackson
26      500-Tom Cruise
25      64-Gary Oldman
25      192-Morgan Freeman
23      884-Steve Buscemi
22      62-Bruce Willis
22      31-Tom Hanks
21      19278-Bill Hader
21      2888-Will Smith
21      16483-Sylvester Stallone
```

In my 4K movie library, the script produces:

```
######################################################
#               People Collections                   #
######################################################
templates:
  Person:
    smart_filter:
      any:
        actor: tmdb
        director: tmdb
        writer: tmdb
        producer: tmdb
      sort_by: year.asc
      validate: false
    tmdb_person: <<person>>
    sort_title: +9_<<collection_name>>
    schedule: weekly(monday)
    collection_order: release
    collection_mode: hide

collections:
  Samuel L. Jackson:
    template: {name: Person, person: 2231}
  Tom Cruise:
    template: {name: Person, person: 500}
  Gary Oldman:
    template: {name: Person, person: 64}
  Morgan Freeman:
    template: {name: Person, person: 192}
  Steve Buscemi:
    template: {name: Person, person: 884}
  Bruce Willis:
    template: {name: Person, person: 62}
  Tom Hanks:
    template: {name: Person, person: 31}
  Bill Hader:
    template: {name: Person, person: 19278}
  Will Smith:
    template: {name: Person, person: 2888}
  Sylvester Stallone:
    template: {name: Person, person: 16483}
```
