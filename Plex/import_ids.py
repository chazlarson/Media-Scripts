""" Import the IDs from the changes file """
#!/usr/bin/env python
import os
import ast
import sys
from pathlib import Path
from datetime import datetime
import logging

import sqlalchemy as db
from alive_progress import alive_bar
from dotenv import load_dotenv
from sqlalchemy.dialects.sqlite import insert

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

PRG_STRING = f"Starting {SCRIPT_NAME}"
logging.info(PRG_STRING)
print(PRG_STRING)

CHANGE_FILE_NAME = "changes.txt"
change_file = Path(CHANGE_FILE_NAME)

def get_connection():
    """ Get the connection to the database """
    engine = db.create_engine('sqlite:///ids.sqlite')
    metadata = db.MetaData()

    connection = engine.connect()

    try:
        ids = db.Table('keys', metadata, autoload=True, autoload_with=engine) # pylint: disable=unused-variable
    except db.exc.NoSuchTableError:
        defaultitem = db.Table('keys', metadata, # pylint: disable=unused-variable
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
    """ Get the completed records """
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys).where(keys.columns.complete is True)
    result_proxy = connection.execute(query)
    result_set = result_proxy.fetchall()

    connection.close()

    return result_set

def get_current(the_guid):
    """ Get the current record """
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys).where(keys.columns.guid == the_guid)
    result_proxy = connection.execute(query)
    result_set = result_proxy.fetchall()

    connection.close()

    return result_set

def get_count():
    """ Get the count of records """
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys)
    result_proxy = connection.execute(query)
    result_set = result_proxy.fetchall()
    count = len(result_set)

    connection.close()

    return count

def insert_record(p_payload):
    """ Insert a record into the database """
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)
    stmt = insert(keys).values(guid=p_payload['guid'],
                                    imdb=p_payload['imdb'],
                                    tmdb=p_payload['tmdb'],
                                    tvdb=p_payload['tvdb'],
                                    title=p_payload['title'],
                                    year=p_payload['year'],
                                    type=p_payload['type'],
                                    complete=p_payload['complete'])
    do_update_stmt = stmt.on_conflict_do_update(
        index_elements=['guid'],
        set = { "imdb":     p_payload['imdb'],
                "tmdb":     p_payload['tmdb'],
                "tvdb":     p_payload['tvdb'],
                "title":    p_payload['title'],
                "year":     p_payload['year'],
                "type":     p_payload['type'],
                "complete": p_payload['complete']
                }
    )

    result = connection.execute(do_update_stmt) # pylint: disable=unused-variable

    connection.close()

def get_diffs(p_payload):
    """ Get the differences between the current record and the new record """
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys).where(keys.columns.guid == p_payload['guid'])
    result_proxy = connection.execute(query)
    result_set = result_proxy.fetchall()
    diffs = {
        'new': False,
        'updated': False,
        'changes': {}
    }
    if len(result_set) > 0:
        if result_set[0]['imdb'] != p_payload['imdb']:
            diffs['changes']['imdb']= p_payload['imdb']
        if result_set[0]['tmdb'] != p_payload['tmdb']:
            diffs['changes']['tmdb']= p_payload['tmdb']
        if result_set[0]['tmdb'] != p_payload['tmdb']:
            diffs['changes']['tmdb']= p_payload['tmdb']
        diffs['updated'] = len(diffs['changes']) > 0
    else:
        diffs['new'] = True
        diffs['changes']['imdb']= p_payload['imdb']
        diffs['changes']['tmdb']= p_payload['tmdb']
        diffs['changes']['tmdb']= p_payload['tmdb']
        diffs['changes']['year']= p_payload['year']

    return diffs

logging.basicConfig(
    filename="grab-all-IDs.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info("No environment [.env] file.  Exiting.")
    print("No environment [.env] file.  Exiting.")
    sys.exit()

CHANGE_RECORDS = None

COMPLETE_ARRAY = []

completed_things = get_completed()

for thing in completed_things:
    COMPLETE_ARRAY.append(thing['guid'])

with open(change_file, "r", encoding="utf-8") as cf:
    data = cf.read()
    items = data.split("\n")

item_total = len(items)

with alive_bar(item_total, dual_line=True, title="Import changes") as bar:
    for item in items:

        parts = item.strip().split(' - ')

        if len(parts) == 2:
            action = parts[0]
            values = ast.literal_eval(parts[1])
            logging.info("================================")
            BAR_TEXT = f"Importing {action} {values['guid']}"
            logging.info(BAR_TEXT)
            bar.text = BAR_TEXT

            payload = {}

            for key in values.keys():
                payload[key] = values[key]

            is_complete = payload['imdb'] is not None and payload['tmdb'] is not None and payload['tvdb'] is not None and payload['year'] is not None

            payload['complete'] = is_complete

            logging.info(payload)

            insert_record(payload)

        bar() # pylint: disable=not-callable
 