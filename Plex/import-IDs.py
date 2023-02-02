import os
import ast
import logging
from pathlib import Path

import sqlalchemy as db
from alive_progress import alive_bar
from dotenv import load_dotenv
from sqlalchemy.dialects.sqlite import insert

CHANGE_FILE_NAME = "changes.txt"
change_file = Path(CHANGE_FILE_NAME)

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

def get_current(the_guid):
    engine, metadata, connection = get_connection()
    keys = db.Table('keys', metadata, autoload=True, autoload_with=engine)

    query = db.select(keys).where(keys.columns.guid == the_guid)
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

    # for Sql
    # print(do_update_stmt.compile(compile_kwargs={"literal_binds": True}))
    # INSERT INTO keys (guid, imdb, tmdb, tvdb, title, type, complete) VALUES ('5d77709531d95e001f1a5216', NULL, '557680', NULL, '"Eiyuu" Kaitai', 'movie', 0) ON CONFLICT (guid) DO UPDATE SET imdb = ?, tmdb = ?, tvdb = ?, title = ?, type = ?, complete = ?
    # need to update that second set of '?'

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
        diffs['updated'] = len(diffs['changes']) > 0
    else:
        diffs['new'] = True
        diffs['changes']['imdb']= payload['imdb']
        diffs['changes']['tmdb']= payload['tmdb']
        diffs['changes']['tmdb']= payload['tmdb']
        diffs['changes']['year']= payload['year']
    
    return diffs

logging.basicConfig(
    filename="grab-all-IDs.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Starting import-IDs.py")

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info(f"No environment [.env] file.  Exiting.")
    print(f"No environment [.env] file.  Exiting.")
    exit()

change_records = None

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
            logging.info(f"Importing {action} {values['guid']}")
            bar.text = f"Importing {action} {values['guid']}"
            payload = {}

            for key in values.keys():
                payload[key] = values[key]
                        
            is_complete = payload['imdb'] is not None and payload['tmdb'] is not None and payload['tvdb'] is not None and payload['year'] is not None
            
            payload['complete'] = is_complete
            
            logging.info(f"{payload}")

            insert_record(payload)

        bar()
