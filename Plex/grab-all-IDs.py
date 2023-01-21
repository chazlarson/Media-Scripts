import logging
import os
import re
import platform
from pathlib import Path
import sys
from pathvalidate import ValidationError, validate_filename

import time

from alive_progress import alive_bar
from dotenv import load_dotenv
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download
from helpers import booler, get_ids, validate_filename, get_plex

import json
import piexif
import piexif.helper

import filetype

import requests
import time
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import sqlalchemy as db
from sqlalchemy.dialects.sqlite import insert

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
                db.Column('title', db.String(255), nullable=True),
                db.Column('type', db.String(25), nullable=True),
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

def insert_record(payload):
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)
    stmt = insert(keys).values(guid=payload['guid'], 
                                    imdb=payload['imdb'], 
                                    tmdb=payload['tmdb'], 
                                    tvdb=payload['tvdb'], 
                                    title=payload['title'], 
                                    type=payload['type'], 
                                    complete=payload['complete'])
    do_update_stmt = stmt.on_conflict_do_update(
        index_elements=['guid'],
        set_=dict(imdb=payload['imdb'], tmdb=payload['tmdb'], tvdb=payload['tvdb'], title=payload['title'], type=payload['type'], complete=payload['complete'])
    )

    result = connection.execute(do_update_stmt)
    connection.close()

load_dotenv()

logging.basicConfig(
    filename="grab-all-IDs.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Starting grab-all-IDs.py")

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TMDB_KEY = os.getenv("TMDB_KEY")

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

logging.info(f"connecting to {PLEX_URL}...")
plex = get_plex(PLEX_URL, PLEX_TOKEN)

foo = plex.library.sections()

logging.info("connection success")

def get_progress_string(item):
    if item.TYPE == "season":
        ret_val = f"{item.parentTitle} - {get_SE_str(item)} - {item.title}"
    elif item.TYPE == "episode":
        ret_val = f"{item.grandparentTitle} - {item.parentTitle} - {get_SE_str(item)} - {item.title}"
    else:
        ret_val = f"{item.title}"

    return ret_val

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
                            'type': type,
                            'complete': complete
                        }

                        insert_record(payload)
                except Exception as ex:
                    print(f"{item.ratingKey}- {item.title} - Exception: {ex}")  
                    logging.info(f"EXCEPTION: {item.ratingKey}- {item.title} - Exception: {ex}")
            else:
                logging.info(f"{guid} already complete")
        except Exception as ex:
            logging.info(f"No guid: {bits}")
        
def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

COMPLETE_ARRAY = []

for lib in LIB_ARRAY:
    completed_things = get_completed()

    for thing in completed_things:
        COMPLETE_ARRAY.append(thing['guid'])

    try:
        the_lib = plex.library.section(lib)

        count = plex.library.section(lib).totalSize
        print(f"getting {count} {the_lib.type}s from [{lib}]...")
        logging.info(f"getting {count} {the_lib.type}s from [{lib}]...")
        items = plex.library.section(lib).all()
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