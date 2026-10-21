# TMDB scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Setup

See the top-level [README](../README.md) for setup instructions.

All these scripts use the same `config.yaml` and requirements.

### `config.yaml` contents

`general.tmdb_key` and `general.delay` are shared. Script-specific settings:

```yaml
tmdb_people:
  poster_dir: people_posters # tmdb-people.py saves profile images here
  person_depth: 10 # how many name-search results to download

original_language:
  input_files: "" # comma-separated files for get_TMDB_Original_Language.py; empty queries Plex
```

The full template is [../config.template.yaml](../config.template.yaml).

## Scripts:
1. [tmdb-people.py](#tmdb-peoplepy) - retrieve TMDB images for a list of people

## tmdb-people.py.py

You want a bunch of person images from TMDB.

### Usage
1. setup as above
2. enter names or TMDB IDs into people_list.txt
3. Run with `python tmdb-people.py`

The script will loop through all the names in the list and download their profile images from TMDB.

```shell
 $ python tmdb-people.py
526 item(s) retrieved...
on 33: ->  exception: Archie Bunker - No Results Found
on 48: ->  exception: Benson & Moorhead - No Results Found
TMDB people |████████▌                               | █▆▄ 111/526 [21%] in 33s (3.4/s, eta: 2:03)
->   starting: Chuck Russell
```

If the name search returns more than one result, the script will attempt to download images for the first `tmdb_people.person_depth` results.
