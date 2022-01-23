# Plex-Meta Manager scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## top-n-actor-coll.py

Connects to a plex library, grabs all the movies.
For each movie, gets the cast from TMDB; keeps track across all movie how many times it sees each actor.
At the end, builds a basic Plex-Meta-Manager metadata file for the top N actors.

Config variables in .env:
```
TMDB_KEY=TMDB_API_KEY           ### YOUR TMDB API KEY
PLEX_URL=https://plex.domin.tld ### PLEX URL
PLEX_TOKEN=PLEX-TOKEN           ### PLEX TOKEN
MOVIE_LIBRARY_NAME=Movies       ### LIBRARY TO TARGET
CAST_DEPTH=20                   ### HOW DEEP TO GO INTO EACH MOVIE CAST
TOP_COUNT=10                    ### PUT THIS MANY INTO THE FILE AT THE END
```

`CAST_DEPTH` is meant to prevent some journeyman character actor from showing up in the top ten; I'm thinking of someone like Clint Howard who's been in the cast of many movies, but I'm guessing when you think of the top ten actors in you library you're not thinking about Clint.

`template.tmpl` - this is the beginning of the target metadata file

`collection.tmpl` - this is the collection definition inserted for each actor [`%%NAME%%%` and `%%ID%%` are placeholders that get substituted for each actor]

## Usage
1. clone repo
1. Install requirements with `pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
1. Copy `.env.example` to `.env`
1. Edit .env to suit
3. Run with `python top-n-actor-coll.py`

```
connecting...
getting movies...
looping over 2819 movies...
[==--------------------------------------] 5.4% ... Annihilation
```

It will got through all your movies, and then at the end print out the top TOP_COUNT and produce a yml file.

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
