import datetime
import sqlite3

# Track artwork download runs
def last_artwork_run_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS last_run_by_library (
                                        uuid TEXT NOT NULL, 
                                        level TEXT NOT NULL, 
                                        name TEXT,
                                        last_run_date TIMESTAMP,
                                        PRIMARY KEY (uuid, level)
                                        );'''

def add_last_run(uuid, name, level, last_run_date):
    method_name = "add_last_run"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = last_artwork_run_table_create_query()

        cursor = sqliteConnection.cursor()
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

        sqliteConnection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def get_last_run(uuid, level):
    method_name = "get_last_run"
    last_run_date = None

    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = last_artwork_run_table_create_query()

        cursor = sqliteConnection.cursor()
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
        if (sqliteConnection):
            sqliteConnection.close()

    return last_run_date

def reset_last_run():
    method_name = "reset_last_run"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS last_run_by_library;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = last_artwork_run_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

# Track media details
def media_details_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS media_details (
                                        path TEXT PRIMARY KEY, 
                                        title TEXT NOT NULL, 
                                        type TEXT NOT NULL,
                                        height INTEGER,
                                        width INTEGER,
                                        aspect_ratio TEXT,
                                        aspect_ratio_calc TEXT
                                        );'''

def add_media_details(path, title, type, height, width, aspect_ratio, aspect_ratio_calc):
    method_name = "add_media_details"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = media_details_table_create_query()

        cursor = sqliteConnection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_insert_with_param = """INSERT OR IGNORE INTO 'media_details'
                          ('path','title','type','height','width','aspect_ratio','aspect_ratio_calc') 
                          VALUES (?, ?, ?, ?, ?, ?, ?);"""

        data_tuple = (path, title, type, height, width, aspect_ratio, aspect_ratio_calc)
        cursor.execute(sqlite_insert_with_param, data_tuple)

        sqliteConnection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def reset_media_details():
    method_name = "reset_media_details"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS media_details;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = media_details_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

# Track downloaded URLs
def url_tracking_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS url_tracking (
                                        url TEXT,
                                        uuid TEXT,
                                        title TEXT,
                                        retrieved TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (url, uuid)
                                        );'''

def add_url(url, uuid, title):
    method_name = "add_url"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = url_tracking_table_create_query()

        cursor = sqliteConnection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_insert_with_param = """INSERT OR IGNORE INTO 'url_tracking'
                          ('url', 'uuid', 'title') VALUES (?, ?, ?);"""

        data_tuple = (url, uuid, title, )
        cursor.execute(sqlite_insert_with_param, data_tuple)

        sqliteConnection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name} ({url}, {uuid}, {title}): ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def check_url(url, uuid):
    method_name = "check_url"
    known_url = False

    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = url_tracking_table_create_query()

        cursor = sqliteConnection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT url from url_tracking where url = ? and uuid = ?"""
        cursor.execute(sqlite_select_query, (url, uuid, ))
        records = cursor.fetchall()

        for row in records:
            known_url = True
    
        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

    return known_url

def reset_url_tracking():
    method_name = "reset_url_tracking"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS url_tracking;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = url_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

# Track artwork download completion
def completion_tracking_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid)
                                        );'''

def add_key(rating_key, uuid, tracking):
    method_name = "add_key"
    if tracking:
        try:
            sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqliteConnection.cursor()

            sqlite_create_table_query = completion_tracking_table_create_query()

            cursor = sqliteConnection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_insert_with_param = """INSERT OR IGNORE INTO 'completed_keys' ('rating_key', 'uuid') VALUES (?, ?);"""

            data_tuple = (rating_key, uuid, )
            cursor.execute(sqlite_insert_with_param, data_tuple)

            sqliteConnection.commit()

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

def check_key(rating_key, uuid, tracking):
    method_name = "check_key"
    known_key = False

    if tracking:
        try:
            sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqliteConnection.cursor()

            sqlite_create_table_query = completion_tracking_table_create_query()

            cursor = sqliteConnection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_select_query = """SELECT rating_key from completed_keys where rating_key = ? and uuid = ?"""
            cursor.execute(sqlite_select_query, (rating_key, uuid, ))
            records = cursor.fetchall()

            for row in records:
                known_key = True
        
            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

    return known_key

def reset_completion_tracking():
    method_name = "reset_completion_tracking"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS completed_keys;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = completion_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

# Track item rematch completion
def rematch_tracking_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS rematch_completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid)
                                        );'''

def add_rematch_key(rating_key, uuid, tracking):
    method_name = "add_rematch_key"
    if tracking:
        try:
            sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqliteConnection.cursor()

            sqlite_create_table_query = rematch_tracking_table_create_query()

            cursor = sqliteConnection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_insert_with_param = """INSERT OR IGNORE INTO 'rematch_completed_keys' ('rating_key', 'uuid') VALUES (?, ?);"""

            data_tuple = (rating_key, uuid, )
            cursor.execute(sqlite_insert_with_param, data_tuple)

            sqliteConnection.commit()

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

def check_rematch_key(rating_key, uuid, tracking):
    method_name = "check_rematch_key"
    known_key = False

    if tracking:
        try:
            sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqliteConnection.cursor()

            sqlite_create_table_query = rematch_tracking_table_create_query()

            cursor = sqliteConnection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_select_query = """SELECT rating_key from rematch_completed_keys where rating_key = ? and uuid = ?"""
            cursor.execute(sqlite_select_query, (rating_key, uuid, ))
            records = cursor.fetchall()

            for row in records:
                known_key = True
        
            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

    return known_key

def reset_rematch_tracking():
    method_name = "reset_rematch_tracking"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS rematch_completed_keys;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = rematch_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

# Track artwork reset completion
def art_reset_tracking_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS art_reset_completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        source TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid, source)
                                        );'''

def add_art_reset_key(rating_key, uuid, source, tracking):
    method_name = "add_art_reset_key"
    if tracking:
        try:
            sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqliteConnection.cursor()

            sqlite_create_table_query = reset_tracking_table_create_query()

            cursor = sqliteConnection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_insert_with_param = """INSERT OR IGNORE INTO 'art_reset_completed_keys' ('rating_key', 'uuid', 'source') VALUES (?, ?, ?);"""

            data_tuple = (rating_key, uuid, source)
            cursor.execute(sqlite_insert_with_param, data_tuple)

            sqliteConnection.commit()

            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

def check_art_reset_key(rating_key, uuid, source, tracking):
    method_name = "check_art_reset_key"
    known_key = False

    if tracking:
        try:
            sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                                            sqlite3.PARSE_COLNAMES)
            cursor = sqliteConnection.cursor()

            sqlite_create_table_query = art_reset_tracking_table_create_query()

            cursor = sqliteConnection.cursor()
            cursor.execute(sqlite_create_table_query)

            sqlite_select_query = """SELECT rating_key from art_reset_completed_keys where rating_key = ? and uuid = ? and source = ?"""
            cursor.execute(sqlite_select_query, (rating_key, uuid, source))
            records = cursor.fetchall()

            for row in records:
                known_key = True
        
            cursor.close()

        except sqlite3.Error as error:
            print(f"Error while working with SQLite in {method_name}: ", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

    return known_key

def reset_art_reset_tracking():
    method_name = "reset_art_reset_tracking"
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_drop_query = """DROP TABLE IF EXISTS art_reset_completed_keys;"""
        cursor.execute(sqlite_drop_query)

        sqlite_create_table_query = art_reset_tracking_table_create_query()
        cursor.execute(sqlite_create_table_query)

        cursor.close()

    except sqlite3.Error as error:
        print(f"Error while working with SQLite in {method_name}: ", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
