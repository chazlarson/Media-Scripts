from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
from pathlib import Path
from timeit import default_timer as timer
import time
import csv

# import tvdb_v4_official

start = timer()

load_dotenv()

plex_url = os.getenv("PLEX_URL")
plex_token = os.getenv("PLEX_TOKEN")
KOMETA_CACHE = os.getenv("KOMETA_CACHE")
INPUT_FILES = os.getenv("INPUT_FILES")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
tmdb_key = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
REMOVE_LABELS = os.getenv("REMOVE_LABELS")
DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

if REMOVE_LABELS:
    lbl_array = REMOVE_LABELS.split(",")

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

if INPUT_FILES:
    file_array = INPUT_FILES.split(",")
else:
    file_array = []

delim = "\t"

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"
IMDB_STR = "imdb://"

local_dir = f"{os.getcwd()}/posters"

os.makedirs(local_dir, exist_ok=True)

show_dir = f"{local_dir}/shows"
movie_dir = f"{local_dir}/movies"

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)


class Plex_item:
    def __init__(
        self,
        Part_File,
        Part_File_Combined,
        Title,
        Country,
        Audio_Stream_Language,
        Audio_Stream_Title,
        IMDB_ID,
        TMDB_ID,
        TVDB_ID,
    ):
        self._Part_File = Part_File
        self._Part_File_Combined = Part_File_Combined
        self._Title = Title
        self._Country = Country
        self._Audio_Stream_Language = Audio_Stream_Language
        self._Audio_Stream_Title = Audio_Stream_Title
        self._IMDB_ID = IMDB_ID
        self._TMDB_ID = TMDB_ID
        self._TVDB_ID = TVDB_ID
        self._Original_Language = None

    def __iter__(self):
        return iter(
            [
                self._Part_File,
                self._Part_File_Combined,
                self._Title,
                self._Country,
                self._Audio_Stream_Language,
                self._Audio_Stream_Title,
                self._IMDB_ID,
                self._TMDB_ID,
                self._TVDB_ID,
                self._Original_Language,
            ]
        )

    @property
    def Part_File_Combined(self):
        return self._Part_File_Combined

    @Part_File_Combined.setter
    def Part_File_Combined(self, a):
        self._Part_File_Combined = a

    @property
    def Part_File(self):
        return self._Part_File

    @Part_File.setter
    def Part_File(self, a):
        self._Part_File = a

    @property
    def Title(self):
        return self._Title

    @Title.setter
    def Title(self, a):
        self._Title = a

    @property
    def Country(self):
        return self._Country

    @Country.setter
    def Country(self, a):
        self._Country = a

    @property
    def Audio_Stream_Language(self):
        return self._Audio_Stream_Language

    @Audio_Stream_Language.setter
    def Audio_Stream_Language(self, a):
        self._Audio_Stream_Language = a

    @property
    def Audio_Stream_Title(self):
        return (self._Audio_Stream_Title,)

    @Audio_Stream_Title.setter
    def Audio_Stream_Title(self, a):
        self._Audio_Stream_Title = a

    @property
    def IMDB_ID(self):
        return (self._IMDB_ID,)

    @IMDB_ID.setter
    def IMDB_ID(self, a):
        self._IMDB_ID = a

    @property
    def TMDB_ID(self):
        return (self._TMDB_ID,)

    @TMDB_ID.setter
    def TMDB_ID(self, a):
        self._TMDB_ID = a

    @property
    def TVDB_ID(self):
        return (self._TVDB_ID,)

    @TVDB_ID.setter
    def TVDB_ID(self, a):
        self._TVDB_ID = a

    @property
    def Original_Language(self):
        return self._Original_Language

    @Original_Language.setter
    def Original_Language(self, a):
        self._Original_Language = a


def getTID(the_list):
    tmid = None
    tvid = None
    imdbid = None
    for guid in the_list:
        if TMDB_STR in guid.id:
            tmid = guid.id.replace(TMDB_STR, "")
        if TVDB_STR in guid.id:
            tvid = guid.id.replace(TVDB_STR, "")
        if IMDB_STR in guid.id:
            imdbid = guid.id.replace(IMDB_STR, "")
    return tmid, tvid, imdbid


def getHeaders():
    headers = ["Part File"]
    headers.append("Part File Combined")
    headers.append("Original Title")
    headers.append("Country")
    headers.append("Audio Stream Language")
    headers.append("Audio Stream Title")
    headers.append("IMDB ID")
    headers.append("TMDB ID")
    headers.append("TVDB ID")
    headers.append("Original Language")

    return headers


def writeResults(itemList, lib):

    output_name = f"./{lib}-output.txt"

    with open(output_name, "wt") as csv_file:
        wr = csv.writer(csv_file, delimiter=delim)
        wr.writerow(list(getHeaders()))
        for item in itemList:
            wr.writerow(list(item))


def getPlexItem(
    fname, full_path, title, countries, streams, streamTitles, imdb_id, tmdb_id, tvdb_id
):
    pi = Plex_item(
        fname,
        full_path,
        title,
        countries,
        streams,
        streamTitles,
        imdb_id,
        tmdb_id,
        tvdb_id,
    )

    tmThing = getTMDBItem(pi)

    if tmThing is not None:
        pi.Original_Language = tmThing.original_language
    else:
        pi.Original_Language = "UNKNOWN"

    return pi


def getTMDBItem(theItem):

    isShow = False
    try:
        isShow = theItem.TYPE == "show"
    except:
        isShow = not ("movie" in theItem.Part_File_Combined)

    tmdbItem = None
    try:
        if isShow:
            try:
                tmdbItem = (
                    tmdb.tv_show(theItem.TMDB_ID[0])
                    if item.TMDB_ID
                    else tmdb.find_by_id(tvdb_id=theItem.TVDB_ID[0]).tv_results[0]
                )
            except:
                if theItem.tvdb_id is not None:
                    tmdbItem = tmdb.find_by_id(tvdb_id=theItem.TVDB_ID[0]).tv_results[0]
                else:
                    tmdbItem = None
        else:
            if tmdb_id is not None:
                tmdbItem = tmdb.movie(theItem.TMDB_ID[0])
    except:
        tmdbItem = None
    return tmdbItem


# def getOriginalLanguage(theItem):

#     output_name = f"./{lib}-output.txt"


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(30)))
    sys.stdout.flush()


print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = "original"

item_count = 1
plex_items = []

if len(file_array) > 0:
    for fn in file_array:
        print(f"{os.linesep}getting items from [{fn}]...")
        item_total = sum(1 for i in open(fn, "rb"))
        print(f"looping over {item_total} items...")
        with open(fn) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter="\t")
            item_count = 0
            for row in csv_reader:
                if item_count == 0:
                    item_count += 1
                else:
                    fName = row[0]
                    fPath = row[1]
                    title = row[2]
                    countries = row[3].split("%")
                    audioStreams = row[4].split("%")
                    audioStreamTitles = row[5].split("%")
                    imdb_id = row[6]
                    tmdb_id = row[7]
                    tvdb_id = row[8]

                    pi = getPlexItem(
                        fName,
                        fPath,
                        title,
                        countries,
                        audioStreams,
                        audioStreamTitles,
                        imdb_id,
                        tmdb_id,
                        tvdb_id,
                    )

                    item_count += 1

                    plex_items.append(pi)

                    progress(item_count, item_total, pi.Title)

        writeResults(plex_items, Path(fn).stem)

else:
    for lib in lib_array:
        print(f"connecting to {PLEX_URL}...")
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)

        print(f"{os.linesep}getting items from [{lib}]...")
        items = plex.library.section(lib).all()
        item_total = len(items)
        print(f"looping over {item_total} items...")

        for item in items:
            tmpDict = {}
            countries = []
            audioStreams = []
            audioStreamTitles = []
            if len(item.guids) > 0:
                tmdb_id, tvdb_id, imdb_id = getTID(item.guids)
                item_count = item_count + 1
                title = item.title
                if item.originalTitle is not None:
                    title = item.originalTitle

                try:
                    for country in item.countries:
                        countries.append(country.tag)
                    media_item = item.media[0]
                    media_part = media_item.parts[0]
                    filePath = media_part.file

                    streams = media_part.streams
                    for stream in streams:
                        if stream.STREAMTYPE == 2:
                            audioStreams.append(stream.language)
                            audioStreamTitles.append(stream.displayTitle)

                    pi = getPlexItem(
                        Path(filePath).name,
                        filePath,
                        title,
                        countries,
                        audioStreams,
                        audioStreamTitles,
                        imdb_id,
                        tmdb_id,
                        tvdb_id,
                    )

                    plex_items.append(pi)

                    progress(item_count, item_total, pi.title)

                except Exception as ex:
                    progress(item_count, item_total, f"EX: {ex} {item.title}")

                # Wait between items in case hammering the Plex server turns out badly.
                time.sleep(DELAY)

    writeResults(plex_items, lib)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
