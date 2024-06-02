# Media-Scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Requirements

1. A system that can run Python 3.7 [or newer]
1. Python 3.7 [or newer] installed on that system

   One of the requirements of these scripts is alive-progress 2.4.1, which requires Python 3.7.

1. A basic knowledge of how to run Python scripts.

## Setup

### if you use [`direnv`](https://github.com/direnv/direnv):
1. clone the repo
1. cd into the repo dir
1. run `direnv allow` as the prompt will tell you to
1. direnv will build the virtual env and keep requirements up to date

### if you don't use [`direnv`](https://github.com/direnv/direnv):
1. install direnv
2. go to the previous section
   
ok no

1. clone repo
   ```
   git clone https://github.com/chazlarson/Media-Scripts.git
   ```
1. cd to repo directory
   ```
   cd Media-Scripts
   ```
1. Install requirements with `python3 -m pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
   
   Creating a virtual environment is described [here](https://docs.python.org/3/library/venv.html); there's also a step-by-step in the local walkthrough in the Kometa wiki.

### After you've done one of the above:
Once you have the requirements installed via whatever means, you are ready to set up the script-specific stuff.

1. cd to script directory [`Plex`, `Kometa`, `TMDB`, etc]
   for example:
   ```
   cd Plex
   ```
1. Copy `.env.example` to `.env`
   
   Linux or Mac:
   ```
   cp .env.example .env
   ```
   Windows:
   ```
   copy .env.example .env
   ```  
1. Edit .env to suit your environment [plex url, token, libraries] and your requirements [what to do, where to download things, etc.]; the settings for each script are detailed in the readme within each folder as shown below.

   Edit the file with whatever text editor you wish.
1. Run the desired script.


All these scripts use the same `.env` and requirements.

## Plex scripts:

1. adjust-added-dates.py - fix broken added and perhaps originally available dates in your library
1. user-emails.py - extract user emails from your shares
1. reset-posters-tmdb.py - reset all artwork in a library to TMDB default
1. reset-posters-plex.py - reset all artwork in a library to Plex default
1. grab-all-IDs.py - grab [into a sqlite DB] ratingKey, IMDB ID, TMDB ID, TVDB ID for everything in a library from plex
1. grab-all-posters.py - grab some or all of the artwork for a library from plex
1. image_picker.py - simple web app to make choosing active art from the images downloaded by grab-all-posters simpler
1. grab-all-status.py - grab watch status for all users all libraries from plex
1. apply-all-status.py - apply watch status for all users all libraries to plex from the file emitted by the previous script
1. show-all-playlists.py - Show contents of all user playlists
1. delete-collections.py - delete most or all collections from one or more libraries
1. refresh-metadata.py - Refresh metadata individually on items in a library
1. list-item-ids.py - Generate a list of IDs in libraries and/or collections
1. actor-count.py - Generate a list of actor credit counts
1. crew-count.py - Generate a list of crew credit counts
1. list-low-poster-counts.py - Generate a list of items that have fewer than some number of posters in Plex

See the [Plex Scripts README](Plex/README.md) for details.

## Kometa scripts

1. extract-collections.py - extract collections from a library
2. kometa-trakt-auth.py - generate trakt auth block for Kometa config.yml
3. kometa-mal-auth.py - generate mal auth block for Kometa config.yml
4. original-to-assets.py - Copy image files from an "Original Posters" directory to an asset directory

See the [Kometa Scripts README](Kometa/README.md) for details.

# TMDB scripts

1. tmdb-people.py - retrieve TMDB images for a list of people

See the [TMDB Scripts README](TMDB/README.md) for details.

# Other script repos of interest

1. [bullmoose](https://github.com/bullmoose20/Plex-Stuff)
2. [Casvt](https://github.com/Casvt/Plex-scripts)
3. [maximuskowalski](https://github.com/maximuskowalski/maxmisc)
