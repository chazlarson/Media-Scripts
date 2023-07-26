import datetime
import sqlite3

def table_create_query():
    return '''CREATE TABLE IF NOT EXISTS last_run_by_library (
                                        uuid TEXT NOT NULL, 
                                        level TEXT NOT NULL, 
                                        name TEXT,
                                        last_run_date TIMESTAMP,
                                        PRIMARY KEY (uuid, level)
                                        );'''

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

def url_tracking_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS url_tracking (
                                        url TEXT,
                                        uuid TEXT,
                                        title TEXT,
                                        retrieved TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (url, uuid)
                                        );'''

def completion_tracking_table_create_query():
    return '''CREATE TABLE IF NOT EXISTS completed_keys (
                                        rating_key TEXT,
                                        uuid TEXT,
                                        completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                        PRIMARY KEY (rating_key, uuid)
                                        );'''

def add_last_run(uuid, name, level, last_run_date):
    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = table_create_query()

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
        print("Error while working with SQLite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def get_last_run(uuid, level):
    last_run_date = None

    try:
        sqliteConnection = sqlite3.connect('mediascripts.sqlite',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()

        sqlite_create_table_query = table_create_query()

        cursor = sqliteConnection.cursor()
        cursor.execute(sqlite_create_table_query)

        sqlite_select_query = """SELECT last_run_date from last_run_by_library where uuid = ? and level = ?"""
        cursor.execute(sqlite_select_query, (uuid, level, ))
        records = cursor.fetchall()

        for row in records:
            last_run_date = row[0]
    
        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

    return last_run_date

def add_media_details(path, title, type, height, width, aspect_ratio, aspect_ratio_calc):
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
        print("Error while working with SQLite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def add_url(url, uuid, title):
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
        print("Error while working with SQLite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def check_url(url, uuid):
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
        print("Error while working with SQLite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

    return known_url

def add_key(rating_key, uuid, tracking):
    if not tracking:
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
            print("Error while working with SQLite", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

def check_key(rating_key, uuid, tracking):
    known_key = False

    if not tracking:
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
            print("Error while working with SQLite", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()

    return known_key

