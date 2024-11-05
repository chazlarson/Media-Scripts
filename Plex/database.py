""" Database functions for Plex Media Server scripts """
import sqlite3

def get_connection(db_name='mediascripts.sqlite'):
    """ Get a connection to the database """
    sqlite_connection = sqlite3.connect(db_name, timeout=10,
                                        detect_types=sqlite3.PARSE_DECLTYPES |
                                                    sqlite3.PARSE_COLNAMES)

    return sqlite_connection

# Track artwork download runs
def last_artwork_run_table_create_query():
    """ Create the last_run_by_library table """
    return '''CREATE TABLE IF NOT EXISTS last_run_by_library (
                                        uuid TEXT NOT NULL,
                                        level TEXT NOT NULL,
                                        name TEXT,
                                        last_run_date TIMESTAMP,
                                        PRIMARY KEY (uuid, level)
                                        );'''

def add_last_run(uuid, name, level, last_run_date):
    """ Add the last run date for a library """
    method_name = "add_last_run"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = last_artwork_run_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_insert_with_param = """INSERT OR IGNORE INTO 'last_run_by_library'
                          ('uuid', 'level', 'name', 'last_run_date')
                          VALUES (?, ?, ?, ?);"""

        data_tuple = (uuid, level, name, last_run_date)
        cursor.execute(sqlite_insert_with_param, data_tuple)

        sqlite_update_with_param = """UPDATE 'last_run_by_library'
                          SET 'last_run_date' = ?
                          WHERE uuid == ? AND
                          name == ? AND
                          level == ?;"""

        data_tuple = (last_run_date, uuid, name, level)
        cursor.execute(sqlite_update_with_param, data_tuple)

        sqlite_connection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

def get_last_run(uuid, level):
    """ Get the last run date for a library """
    method_name = "get_last_run"
    last_run_date = None

    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = last_artwork_run_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT last_run_date from last_run_by_library where uuid = ? and level = ?"""
        cursor.execute(sqlite_select_query, (uuid, level, ))
        records = cursor.fetchall()

        for row in records:
            last_run_date = row[0]

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

    return last_run_date

def reset_last_run():
    """ Reset the last run date for all libraries """
    method_name = "reset_last_run"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS last_run_by_library;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = last_artwork_run_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

# Track media details
def media_details_table_create_query():
    """ Create the media_details table """
    return '''CREATE TABLE IF NOT EXISTS media_details (
                                        path TEXT PRIMARY KEY,
                                        title TEXT NOT NULL,
                                        type TEXT NOT NULL,
                                        height INTEGER,
                                        width INTEGER,
                                        aspect_ratio TEXT,
                                        aspect_ratio_calc TEXT
                                        );'''

def add_media_details(path, title, media_type, height, width, aspect_ratio, aspect_ratio_calc): # pylint: disable=too-many-arguments, too-many-positional-arguments
    """ Add media details to the database """
    method_name = "add_media_details"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = media_details_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_insert_with_param = """INSERT OR IGNORE INTO 'media_details'
                          ('path','title','type','height','width','aspect_ratio','aspect_ratio_calc')
                          VALUES (?, ?, ?, ?, ?, ?, ?);"""

        data_tuple = (path, title, media_type, height, width, aspect_ratio, aspect_ratio_calc)
        cursor.execute(sqlite_insert_with_param, data_tuple)

        sqlite_connection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

def reset_media_details():
    """ Reset the media details table """
    method_name = "reset_media_details"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS media_details;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = media_details_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

# Track downloaded URLs
def url_tracking_table_create_query():
    """ Create the url_tracking table """
    return '''CREATE TABLE IF NOT EXISTS url_tracking (
                                        url TEXT,
                                        uuid TEXT,
                                        title TEXT,
                                        retrieved TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (url, uuid)
                                        );'''

def add_url(url, uuid, title):
    """ Add a URL to the database """
    method_name = "add_url"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = url_tracking_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_insert_with_param = """INSERT OR IGNORE INTO 'url_tracking'
                          ('url', 'uuid', 'title') VALUES (?, ?, ?);"""

        data_tuple = (url, uuid, title, )
        cursor.execute(sqlite_insert_with_param, data_tuple)

        sqlite_connection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name} ({url}, {uuid}, {title}): ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

def check_url(url, uuid):
    """ Check if a URL has been downloaded """
    method_name = "check_url"
    known_url = False

    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = url_tracking_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT url from url_tracking where url = ? and uuid = ?"""
        cursor.execute(sqlite_select_query, (url, uuid, ))
        records = cursor.fetchall()

        known_url = len(records) > 0

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

    return known_url

def reset_url_tracking():
    """ Reset the URL tracking table """
    method_name = "reset_url_tracking"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS url_tracking;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = url_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

# Track artwork download completion
def completion_tracking_table_create_query():
    """ Create the completed_keys table """
    return '''CREATE TABLE IF NOT EXISTS completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid)
                                        );'''

def add_key(rating_key, uuid, tracking):
    """ Add a key to the completion tracking table """
    method_name = "add_key"
    if tracking:
        try:
            sqlite_connection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqlite_connection.cursor()

            sqlite_create_table_query = completion_tracking_table_create_query()

            cursor = sqlite_connection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_insert_with_param = """INSERT OR IGNORE INTO 'completed_keys' ('rating_key', 'uuid') VALUES (?, ?);"""

            data_tuple = (rating_key, uuid, )
            cursor.execute(sqlite_insert_with_param, data_tuple)

            sqlite_connection.commit()

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

def check_key(rating_key, uuid, tracking):
    """ Check if a key has been downloaded """
    method_name = "check_key"
    known_key = False

    if tracking:
        try:
            sqlite_connection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqlite_connection.cursor()

            sqlite_create_table_query = completion_tracking_table_create_query()

            cursor = sqlite_connection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_select_query = """SELECT rating_key from completed_keys where rating_key = ? and uuid = ?"""
            cursor.execute(sqlite_select_query, (rating_key, uuid, ))
            records = cursor.fetchall()

            known_key = len(records) > 0

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    return known_key

def reset_completion_tracking():
    """ Reset the completion tracking table """
    method_name = "reset_completion_tracking"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS completed_keys;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = completion_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

# Track item rematch completion
def rematch_tracking_table_create_query():
    """ Create the rematch_completed_keys table """
    return '''CREATE TABLE IF NOT EXISTS rematch_completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid)
                                        );'''

def add_rematch_key(rating_key, uuid, tracking):
    """ Add a key to the rematch completion tracking table """
    method_name = "add_rematch_key"
    if tracking:
        try:
            sqlite_connection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqlite_connection.cursor()

            sqlite_create_table_query = rematch_tracking_table_create_query()

            cursor = sqlite_connection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_insert_with_param = """INSERT OR IGNORE INTO 'rematch_completed_keys' ('rating_key', 'uuid') VALUES (?, ?);"""

            data_tuple = (rating_key, uuid, )
            cursor.execute(sqlite_insert_with_param, data_tuple)

            sqlite_connection.commit()

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

def check_rematch_key(rating_key, uuid, tracking):
    """ Check if a key has been rematched """
    method_name = "check_rematch_key"
    known_key = False

    if tracking:
        try:
            sqlite_connection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqlite_connection.cursor()

            sqlite_create_table_query = rematch_tracking_table_create_query()

            cursor = sqlite_connection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_select_query = """SELECT rating_key from rematch_completed_keys where rating_key = ? and uuid = ?"""
            cursor.execute(sqlite_select_query, (rating_key, uuid, ))
            records = cursor.fetchall()

            known_key = len(records) > 0

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    return known_key

def reset_rematch_tracking():
    """ Reset the rematch completion tracking table """
    method_name = "reset_rematch_tracking"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS rematch_completed_keys;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = rematch_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

# Track artwork reset completion
def art_reset_tracking_table_create_query():
    """ Create the art_reset_completed_keys table """
    return '''CREATE TABLE IF NOT EXISTS art_reset_completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        source TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid, source)
                                        );'''

def add_art_reset_key(rating_key, uuid, source, tracking):
    """ Add a key to the artwork reset completion tracking table """
    method_name = "add_art_reset_key"
    if tracking:
        try:
            sqlite_connection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqlite_connection.cursor()

            sqlite_create_table_query = art_reset_tracking_table_create_query()

            cursor = sqlite_connection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_insert_with_param = """INSERT OR IGNORE INTO 'art_reset_completed_keys' ('rating_key', 'uuid', 'source') VALUES (?, ?, ?);"""

            data_tuple = (rating_key, uuid, source)
            cursor.execute(sqlite_insert_with_param, data_tuple)

            sqlite_connection.commit()

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

def check_art_reset_key(rating_key, uuid, source, tracking):
    """ Check if a key has been reset """
    method_name = "check_art_reset_key"
    known_key = False

    if tracking:
        try:
            sqlite_connection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqlite_connection.cursor()

            sqlite_create_table_query = art_reset_tracking_table_create_query()

            cursor = sqlite_connection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_select_query = """SELECT rating_key from art_reset_completed_keys where rating_key = ? and uuid = ? and source = ?"""
            cursor.execute(sqlite_select_query, (rating_key, uuid, source))
            records = cursor.fetchall()

            known_key = len(records) > 0

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    return known_key

def reset_art_reset_tracking():
    """ Reset the artwork reset completion tracking table """
    method_name = "reset_art_reset_tracking"
    try:
        sqlite_connection = get_connection()

        cursor = sqlite_connection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS art_reset_completed_keys;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = art_reset_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

# grab-all-ids
def media_keys_table_create_query():
    """ Create the keys table """
    return '''CREATE TABLE IF NOT EXISTS keys (
                                        guid TEXT,
                                        imdb TEXT,
                                        tmdb TEXT,
                                        tvdb TEXT,
                                        title TEXT,
                                        year INTEGER,
                                        source INTEGER,
                                        type TEXT,
                                        complete BOOLEAN,
                                        PRIMARY KEY (guid)
                                        );'''

def get_completed():
    """ Get all completed records """
    method_name = "get_completed"
    records = None

    try:
        sqlite_connection = get_connection(db_name='ids.sqlite')

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = media_keys_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT * from keys where complete = ?"""
        cursor.execute(sqlite_select_query, (True, ))
        records = cursor.fetchall()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

    return records

def get_count():
    """ Get the count of records """
    method_name = "get_count"
    record_count = 0

    try:
        sqlite_connection = get_connection(db_name='ids.sqlite')

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = media_keys_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT COUNT(guid) from keys"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()

        for row in records:
            record_count = row[0]

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

    return record_count

def get_media_key(target_guid):
    """ Get a specific media key """
    method_name = "check_media_key"
    result = None

    try:
        sqlite_connection = get_connection(db_name='ids.sqlite')

        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = media_keys_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT * from keys where guid = ? """
        cursor.execute(sqlite_select_query, (target_guid, ))
        records = cursor.fetchall()

        for row in records:
            result = row

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

    return result

def insert_record(payload):
    """ Insert a record into the keys table """
    method_name = "insert_record"

    try:
        sqlite_connection = sqlite3.connect('ids.sqlite',
                                        detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = media_keys_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_insert_with_param = """INSERT OR IGNORE INTO 'keys' ('guid','imdb','tmdb','tvdb','title','year','type','complete') VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""

        data_tuple = (payload['guid'], payload['imdb'], payload['tmdb'], payload['tvdb'], payload['title'], payload['year'], payload['type'], payload['complete'])
        cursor.execute(sqlite_insert_with_param, data_tuple)

        sqlite_connection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

def update_record(payload):
    """ Update a record in the keys table """
    method_name = "update_record"

    try:
        sqlite_connection = sqlite3.connect('ids.sqlite',
                                        detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqlite_connection.cursor()

        sqlite_create_table_query = media_keys_table_create_query()

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_update_with_param = 'UPDATE keys SET imdb=?,tmdb=?,tvdb=?,title=?,year=?,type=?,complete=? WHERE guid=?'

        update_tuple = (payload['imdb'], payload['tmdb'], payload['tvdb'], payload['title'], payload['year'], payload['type'], payload['complete'], payload['guid'])
        cursor.execute(sqlite_update_with_param, update_tuple)

        sqlite_connection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

def get_diffs(payload):
    """ Compare a payload to the current record """

    diffs = {
        'new': False,
        'updated': False,
        'changes': {}
    }

    current = get_media_key(payload['guid'])

    if current is not None and len(current) > 0:
        if current[1] != payload['imdb']:
            diffs['changes']['imdb']= payload['imdb']
        if current[2] != payload['tmdb']:
            diffs['changes']['tmdb']= payload['tmdb']
        if current[3] != payload['tvdb']:
            diffs['changes']['tvdb']= payload['tvdb']
        if current[5] != payload['year']:
            diffs['changes']['year']= payload['year']
        diffs['updated'] = len(diffs['changes']) > 0
    else:
        diffs['new'] = True
        diffs['changes']['imdb']= payload['imdb']
        diffs['changes']['tmdb']= payload['tmdb']
        diffs['changes']['tmdb']= payload['tmdb']
        diffs['changes']['year']= payload['year']

    return diffs
