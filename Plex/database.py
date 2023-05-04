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
