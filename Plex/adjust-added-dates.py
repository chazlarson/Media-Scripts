import json
import logging
import os
import pickle
import platform
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path

import filetype
import piexif
import piexif.helper
import plexapi
import requests
from alive_progress import alive_bar, alive_it
from dotenv import load_dotenv
from helpers import (booler, get_all, get_ids, get_letter_dir, get_plex,
                     get_size, redact, validate_filename)
from pathvalidate import ValidationError, validate_filename
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download
from plexapi.video import Episode

SCRIPT_NAME = Path(__file__).stem
VERSION = "0.1.0"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
DOWNLOAD_LOG = f"{SCRIPT_NAME}-dl.log"

def setup_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    fileHandler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fileHandler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(fileHandler)

def setup_dual_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    fileHandler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(fileHandler)
    log_setup.addHandler(streamHandler)

def logger(msg, level, logfile):
    if logfile == 'a'   : log = logging.getLogger('activity_log')
    if logfile == 'd'   : log = logging.getLogger('download_log') 
    if level == 'info'    : log.info(msg) 
    if level == 'warning' : log.warning(msg)
    if level == 'error'   : log.error(msg)

def plogger(msg, level, logfile):
    if logfile == 'a'   : log = logging.getLogger('activity_log')
    if logfile == 'd'   : log = logging.getLogger('download_log') 
    if level == 'info'    : log.info(msg) 
    if level == 'warning' : log.warning(msg)
    if level == 'error'   : log.error(msg)
    print(msg)

def blogger(msg, level, logfile, bar):
    if logfile == 'a'   : log = logging.getLogger('activity_log')
    if logfile == 'd'   : log = logging.getLogger('download_log') 
    if level == 'info'    : log.info(msg) 
    if level == 'warning' : log.warning(msg)
    if level == 'error'   : log.error(msg)
    bar.text(msg)

setup_logger('activity_log', ACTIVITY_LOG)
setup_logger('download_log', DOWNLOAD_LOG)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if os.path.exists(".env"):
    load_dotenv()
else:
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")

plex = get_plex(PLEX_URL, PLEX_TOKEN)

logger("connection success", 'info', 'a')

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:
    try:
        
        plogger(f"Loading {lib} ...", 'info', 'a')
        the_lib = plex.library.section(lib)
        lib_size = the_lib.totalViewSize()
        
        # items = get_all(plex, the_lib, 'episode', {"addedAt>>": "2023-12-30"})
        items = get_all(plex, the_lib, None, {"addedAt>>": "2023-12-30"})
 
        item_total = len(items)
        if item_total > 0:
            logger(f"looping over {item_total} items...", 'info', 'a')
            item_count = 0

            plex_links = []
            external_links = []

            with alive_bar(item_total, dual_line=True, title=f"Adjust added dates {the_lib.title}") as bar:
                for item in items:
                    try:
                        blogger(f"Starting {item.title}", 'info', 'a', bar)
                        orig_date = item.originallyAvailableAt
                        item.editField("addedAt",orig_date,False)

                    except Exception as ex:
                        plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                    bar()
                    
            plogger(f"Processed {item_count} of {item_total}", 'info', 'a')

        progress_str = "COMPLETE"
        logger(progress_str, 'info', 'a')

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, 'info', 'a')