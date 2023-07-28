import json
import logging
import os
import platform
import re
import sys
import time
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path

import filetype
import piexif
import piexif.helper
import plexapi
import requests
import sqlalchemy as db
from alive_progress import alive_bar
from dotenv import load_dotenv
from pathvalidate import ValidationError, validate_filename
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download
from sqlalchemy.dialects.sqlite import insert

from helpers import booler, get_all_from_library, get_ids, get_plex, validate_filename, load_and_upgrade_env

import logging
from pathlib import Path
from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

status = load_and_upgrade_env(env_file_path)

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TMDB_KEY = os.getenv("TMDB_KEY")
NEW = []
UPDATED = []

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

CHANGE_FILE_NAME = "changes.txt"
change_file = Path(CHANGE_FILE_NAME)
# Delete any existing change file
if change_file.is_file():
    change_file.unlink()

def get_connection():
    engine = db.create_engine('sqlite:///ids.sqlite')
    metadata = db.MetaData()

    connection = engine.connect()
        
    try:
        ids = db.Table('keys', metadata, autoload=True, autoload_with=engine)
    except db.exc.NoSuchTableError as nste:
        defaultitem = db.Table('keys', metadata,
                db.Column('guid', db.String(25), primary_key=True),
                db.Column('imdb', db.String(25), nullable=True),
                db.Column('tmdb', db.String(25), nullable=True),
                db.Column('tvdb', db.String(25), nullable=True),
                db.Column('title', db.String(255), nullable=False),
                db.Column('year', db.Integer),
                db.Column('source', db.Integer),
                db.Column('type', db.String(25), nullable=False),
                db.Column('complete', db.Boolean),
                )
        metadata.create_all(engine)

    return engine, metadata, connection

def get_completed():
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys).where(keys.columns.complete == True)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()

    connection.close()

    return ResultSet

def get_count():
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    count = len(ResultSet)
    
    connection.close()

    return count

def insert_record(payload):
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)
    stmt = insert(keys).values(guid=payload['guid'], 
                                    imdb=payload['imdb'], 
                                    tmdb=payload['tmdb'], 
                                    tvdb=payload['tvdb'], 
                                    title=payload['title'], 
                                    year=payload['year'], 
                                    type=payload['type'], 
                                    complete=payload['complete'])
    do_update_stmt = stmt.on_conflict_do_update(
        index_elements=['guid'],
        set_=dict(imdb=payload['imdb'], tmdb=payload['tmdb'], tvdb=payload['tvdb'], title=payload['title'], year=payload['year'], type=payload['type'], complete=payload['complete'])
    )

    result = connection.execute(do_update_stmt)

    connection.close()

def get_diffs(payload):
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys).where(keys.columns.guid == payload['guid'])
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    diffs = {
        'new': False,
        'updated': False,
        'changes': {}
    }
    if len(ResultSet) > 0:
        if ResultSet[0]['imdb'] != payload['imdb']:
            diffs['changes']['imdb']= payload['imdb']
        if ResultSet[0]['tmdb'] != payload['tmdb']:
            diffs['changes']['tmdb']= payload['tmdb']
        if ResultSet[0]['tmdb'] != payload['tmdb']:
            diffs['changes']['tmdb']= payload['tmdb']
        if ResultSet[0]['year'] != payload['year']:
            diffs['changes']['year']= payload['year']
        diffs['updated'] = len(diffs['changes']) > 0
    else:
        diffs['new'] = True
        diffs['changes']['imdb']= payload['imdb']
        diffs['changes']['tmdb']= payload['tmdb']
        diffs['changes']['tmdb']= payload['tmdb']
        diffs['changes']['year']= payload['year']
    
    return diffs

plex = get_plex()

logging.info("connection success")

def get_IDs(type, item):
    imdbid = None
    tmid = None
    tvid = None
    raw_guid = item.guid
    bits = raw_guid.split('/')
    # plex://movie/5d776b59ad5437001f79c6f8
    # local://3961921
    if bits[0] == 'plex:':
        try:
            guid = bits[3]
        
            if guid not in COMPLETE_ARRAY:
                try:
                    if item.type != 'collection':
                        logging.info("Getting IDs")
                        imdbid, tmid, tvid = get_ids(item.guids, TMDB_KEY)
                        complete = imdbid is not None and tmid is not None and tvid is not None 
                        payload = {
                            'guid': guid,
                            'imdb': imdbid,
                            'tmdb': tmid,
                            'tvdb': tvid,
                            'title': item.title,
                            'year': item.year,
                            'type': type,
                            'complete': complete
                        }

                        diffs = get_diffs(payload)
                            
                        if diffs['new'] or diffs['updated']:
                            # record change
                            if diffs['new']:
                                action = 'new'
                                NEW.append(guid)
                            else:
                                action = 'updated'
                                UPDATED.append(guid)

                            with open(change_file, "a", encoding="utf-8") as cf:
                                cf.write(f"{action} - {payload} {os.linesep}")

                            insert_record(payload)
                except Exception as ex:
                    print(f"{item.ratingKey}- {item.title} - Exception: {ex}")  
                    logging.info(f"EXCEPTION: {item.ratingKey}- {item.title} - Exception: {ex}")
            else:
                logging.info(f"{guid} already complete")
        except Exception as ex:
            logging.info(f"No guid: {bits}")
        
COMPLETE_ARRAY = []

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

with open(change_file, "a", encoding="utf-8") as cf:
    cf.write(f"start: {get_count()} records{os.linesep}")

for lib in LIB_ARRAY:
    completed_things = get_completed()

    for thing in completed_things:
        COMPLETE_ARRAY.append(thing['guid'])

    try:
        the_lib = plex.library.section(lib)

        count = plex.library.section(lib).totalSize
        print(f"getting {count} {the_lib.type}s from [{lib}]...")
        logging.info(f"getting {count} {the_lib.type}s from [{lib}]...")
        items = get_all_from_library(plex, the_lib)
        # items = the_lib.all()
        item_total = len(items)
        logging.info(f"looping over {item_total} items...")
        item_count = 1

        plex_links = []
        external_links = []

        with alive_bar(item_total, dual_line=True, title="Grab all IDs") as bar:
            for item in items:
                logging.info("================================")
                logging.info(f"Starting {item.title}")

                get_IDs(the_lib.type, item)

                bar()

        progress_str = "COMPLETE"
        logging.info(progress_str)

        bar.text = progress_str

        print(os.linesep)

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        logging.info(progress_str)

        print(progress_str)

logging.info("================================")
logging.info(f"NEW: {len(NEW)}; UPDATED: {len(UPDATED)}")
print(f"NEW: {len(NEW)}; UPDATED: {len(UPDATED)}")

with open(change_file, "a", encoding="utf-8") as cf:
    cf.write(f"end: {get_count()} records{os.linesep}")

