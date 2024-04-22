# Python 3

import socket
import urllib.request as req
import urllib.parse as p
import re
from plexapi.server import PlexServer

plex = None
PMI = None

config_dict = {"libraries":{}}

default_sections = {
"movie": {
    'metadata_path': [
        {'file': 'config/Movies.yml'},
        {'folder': 'config/Movies/'}, 
        {'pmm': 'basic'}, 
        {'pmm': 'imdb'}],
    'overlay_path': [
        {'remove_overlays': 'false'},
        {'file': 'config/Overlays.yml'},
        {'pmm': 'ribbon'}]},

"show": {
    'metadata_path': [
        {'file': 'config/TVShows.yml'},
        {'folder': 'config/TV Shows/'}, 
        {'pmm': 'basic'}, 
        {'pmm': 'imdb'}],
    'overlay_path': [
        {'remove_overlays': 'false'},
        {'file': 'config/Overlays.yml'},
        {'pmm': 'ribbon'}]},
"anime": {
    'metadata_path': [
        {'file': 'config/Anime.yml'},
        {'pmm': 'basic'}, 
        {'pmm': 'anilist'}]},
"artist": {
    'metadata_path': [
        {'file': 'config/Music.yml'}]}
}

library_section = {'libraries': {'Movies': 
{'metadata_path': [{'file': 'config/Resolutions.yml'}, {'file': 'config/Franchises.yml'}, {'file': 'config/Weekly_Lists.yml'}, {'file': 'config/Lists.yml'}, {'file': 'config/Holiday.yml'}, {'file': 'config/MovieCharts.yml'}], 'operations': {'split_duplicates': True, 'delete_unmanaged_collections': True}}}}
settings_section = {'settings': {'validate_builders': False, 'cache': True, 'cache_expiration': 60, 'asset_directory': ['/config/assets/'], 'assets_for_all': False, 'create_asset_folders': False, 'delete_below_minimum': False, 'missing_only_released': False, 'notifiarr_collection_addition': False, 'notifiarr_collection_creation': False, 'notifiarr_collection_removing': False, 'only_filter_missing': False, 'released_missing_only': False, 'run_again_delay': 2, 'save_missing': True, 'show_filtered': False, 'show_missing_assets': False, 'show_missing': False, 'show_unmanaged': True, 'sync_mode': 'sync', 'tvdb_language': 'default', 'show_missing_season_assets': False, 'delete_not_scheduled': False, 'ignore_ids': None, 'ignore_imdb_ids': None, 'asset_depth': 2, 'show_options': True, 'asset_folders': True, 'dimensional_asset_rename': True, 'minimum_items': 1, 'default_collection_order': None, 'download_url_assets': False, 'verify_ssl': True, 'item_refresh_delay': 0, 'playlist_sync_to_users': 'all', 'show_missing_episode_assets': False, 'show_asset_not_needed': True, 'custom_repo': None, 'prioritize_assets': False, 'playlist_report': True, 'check_nightly': False}}
webhooks_section = {'webhooks': {'error': 'notifiarr', 'run_start': 'notifiarr', 'run_end': 'notifiarr', 'changes': 'notifiarr', 'version': None}}
tmdb_section = {'tmdb': {'apikey': '8da985886d9f212ed7b4231960c22b49', 'language': 'en', 'cache_expiration': 60, 'region': None}}
tautulli_section = {'tautulli': {'url': None, 'apikey': '68f6d88b261b42569138f0c717f132a8'}, 'omdb': {'apikey': '9e62df51', 'cache_expiration': 60}}
notifiarr_section = {'notifiarr': {'apikey': '66fc0993-658c-475f-9827-83a7eeec01fa'}}
anidb_section = {'anidb': {'username': 'chazlarson', 'password': 'yxzPFe3H6WLC4R', 'language': 'en'}}
radarr_section = {'radarr': {'url': None, 'token': 'acad94d563a0b36acda01f3c08d1cfb36373dc29dba427e81a67369819f3e5f9', 'root_folder_path': '/movies', 'monitor': True, 'availability': 'released', 'quality_profile': 'Any', 'tag': None, 'search': False, 'add_existing': False, 'radarr_path': None, 'plex_path': None, 'add_missing': False, 'upgrade_existing': False}}
sonarr_section = {'sonarr': {'url': None, 'token': 'acad94d563a0b36acda01f3c08d1cfb36373dc29dba427e81a67369819f3e5f9', 'root_folder_path': '/tv', 'monitor': 'all', 'quality_profile': 'Any', 'language_profile': 'English', 'series_type': 'standard', 'season_folder': True, 'tag': None, 'search': False, 'cutoff_search': False, 'add_existing': False, 'sonarr_path': None, 'plex_path': None, 'add_missing': False, 'upgrade_existing': False}}
trakt_section = {'trakt': {'client_id': '075daaa5d675d407596911afbdc535fef93102af21131f9a159a0c32446688fa', 'client_secret': '4b88ffc362979ddd223216c120202e68999af02f28beb275a5c1b2f11f3c9770', 'authorization': {'access_token': '5ab3afc9fe9086e136fbaedcc3df1b3dc0b2996fbd4b583c0c268e0839e65d17', 'token_type': 'Bearer', 'expires_in': 7889238, 'refresh_token': '056c25e6fad800d296282ac228f9a4c41a5d68be47848daad140c56321b8e849', 'scope': 'public', 'created_at': 1656256216}, 'pin': None}}
mal_section = {'mal': {'client_id': '82074cc27b34ad4e921b4a65753f9777', 'client_secret': 'a9b39fcaae26becf4b0486d78e54b855c60b8de0fa6cc9ba47168e4e7c4ac928', 'localhost_url': 'http://localhost/?code=ddf502003678252c9e1ec1e385c80555645349caf838135887f5d503ebd047072e282fe2875a47446d5c017b2860dbe42db55f72e98869031592a0e3de705970f91e977fb223bc62c978f2001176835d6d1755d005210549910a589eb9009b468db5927b7bc79512b2030ac7444443fecb5f86c063736ad9ded31d6aa4ff2df51df86c869e5a5f2d2378866b808bec206f10a9ef243022103325e7a3474b9048526b4eac8100bd8ba23504fe77ba17a9414a9096edc55ca8ba5b55eb4f1a50e47ee6598274ab185ae3cd8c4672d5ae545dec6f5cc5da6b4a0f891d6fec36fa04f03cf58693e595c21690ee5ee75c559eb0134aad2bc0b63434e4c9e418bcdd9ca50dd6483d4dde0f8a1dc544506ad7bd4a3e3cbc8d497d6677502b954724ffcccb036b15f527f3528ab55cb76437471272e2f591ea53b7015ab182eeb63ed02cd1fed62b3d8e2065b1c55c5216c133eadde84a1c48bdd7b2b5fc66edd8b03f1a5182fbded468438a13b7e862dd72fa80369cf0d6d39536f09b004e92148c46618001b8b1ddc57df316b87ef98cb1dafa4c781bfc790a6b022b88800bf90e3b5fd895e08233981facf2682a29200dbdabe53d67b54a6ec07aba0c53cc4d1c8ccbf15c356b08c14d7293984636927080c7b0b8d36b06974ba79339a64e29658ddcad6fe3b5172abc0c5509', 'authorization': {'access_token': None, 'token_type': None, 'expires_in': None, 'refresh_token': None}}}

def is_valid_regex(str):
    try:
        re.compile(str)
        is_valid = True
    except re.error:
        is_valid = False
    return is_valid

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def is_url_or_path(url):
    if is_url(url):
        return test_url(url)
    else:
        return open(sys.argv[1])

def is_url(url):
    return p.urlparse(url).scheme in ('http', 'https',)

def test_plex(plex_url, plex_token):
    global plex
    try:
        print(f"Connecting to {plex_url} with token {plex_token}...")
        plex = PlexServer(plex_url, plex_token)
        PMI = plex.machineIdentifier
        print(f"Success: retrieved machine Identifier {PMI}")
        return True
    except Exception as ex:
        print(f"Issue while loading: {ex}")
        return False

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def yes_or_no(question):
    answer = input(question + "(y/n): ").lower().strip()
    print("")
    while not(answer == "y" or answer == "yes" or \
    answer == "n" or answer == "no"):
        print("Input yes or no")
        answer = input(question + "(y/n):").lower().strip()
        print("")
    if answer[0] == "y":
        return True
    else:
        return False

def tag_menu():
    return tag_only_menu() + "    5. no tag; filter on entire row \r\n"

def tag_only_menu():
    return "\r\n\
    1. tvg-id \r\n\
    2. tvg-name \r\n\
    3. tvg-logo \r\n\
    4. group-title \r\n"

def print_libraries(plex_sections):
    idx = 1
    for plex_section in plex_sections:
        print (f"{idx}. {plex_section.title}")
        idx += 1
    print (f"{idx}. Show list again")
    print (f"{idx+1}. Exit")
    print (67 * "-")
  
def process_library(plex_section):
    print (f"{plex_section.title} library type: {plex_section.type}")
    if yes_or_no("Include the standard example config for this library? "):
        config_dict["libraries"][plex_section.title] = default_sections[plex_section.type]
    else:
        print (f"Here's where we will ask about defaults")

my_ip = get_ip()
config_file_name="telly.config.toml"
empty_string = ""
ffmpeg_on = "FFMpeg = true"
ffmpeg_off = empty_string

# "http://irislinks.net:83/get.php?username=11111111&password=22222222&type=m3u_plus&output=ts"
# "http://irislinks.net:83/xmltv.php?username=11111111&password=22222222"

disc_vars   = { 'disc-device-auth': "telly123", 'disc-device-id': 12345678, 'disc-device-uuid': "", 'disc-device-firmware-name': "hdhomeruntc_atsc", 'disc-device-firmware-version': "20150826", 'disc-device-friendly-name': "telly", 'disc-device-manufacturer': "silicondust" , 'disc-device-model-number': "hdtc-2us", 'disc-ssdp': "true" }
iptv_vars   = { 'iptv-streams': 1, 'iptv-starting-channel': 10000, 'iptv-xmltv-channels': "true", 'iptv-ffmpeg': ffmpeg_on }
log_vars    = { 'log-level': "info", 'log-requests': "true" }
web_vars    = { 'web-base': my_ip, 'web-listen': "0.0.0.0", 'web-port': 6077 }
source_vars = { 'source-name': "TellyTV", 'source-provider': "Custom", 'source-m3u': "IPTV_M3U", 'source-epg': "IPTV_M3U", 'source-filter': "UNDEFINED_FILTER", 'source-filterkey': "group-title", 'source-filterraw': "false", 'source-sort': "group-title" }

print("We're going to generate a basic PMM config file. \r\n\r\n\
You will need these bits of information: \r\n\
    1. Your Plex URL and token \r\n\
    2. A TMDB API Key \r\n\r\n\
You MAY need these bits of information: \r\n\
    1. Trakt Client ID, Secret, and PIN \r\n\
    2. MyAnimeList Client ID, Secret\r\n\
    3. Radarr URL and API key \r\n\
    4. Sonarr URL and API key \r\n\
    5. Tautulli URL and API key \r\n\
    5. IMDB ID of a movie in your Plex  \r\n\
     \r\n")

if yes_or_no("Do you have the two required things available? "):
    print("Cool.\n")
else:
    print("I am sorry, but I cannot continue.")
    exit()

while True:
    # plex_url = input("Plex server URL: " )
    # plex_token = input("Plex token: " )

    plex_url = "https://cp1.chazbox.com"
    plex_token = "Cap2GofDpKDjezntT2dx"

    if test_plex(plex_url, plex_token):
        config_dict['plex'] = {
            'url': plex_url, 
            'token': plex_token, 
            'timeout': 720, 
            'clean_bundles': False, 
            'empty_trash': False, 
            'optimize': False}
        break
    else:
        print("Error! Something's not right with that URL. Try again.")
        plex = None
        if yes_or_no("Do you want ot use it as is? "):
            config_dict['plex'] = {
                'url': plex_url, 
                'token': plex_token, 
                'timeout': 720, 
                'clean_bundles': False, 
                'empty_trash': False, 
                'optimize': False}
            break
        else:
            config_dict['plex'] = {}

if plex:
    plex_sections = plex.library.sections()
    print_libraries(plex_sections)

    loop=True      
    
    while loop:
        raw_input = input("Select a Library to configure: ")
        try:
            choice = int(raw_input)-1
            if choice < 0 or choice > len(plex_sections)+1:
                raise Exception
            if choice==(len(plex_sections)+1):     
                loop=False
            elif choice==(len(plex_sections)):     
                print_libraries(plex_sections)
            else:
                the_lib = plex_sections[choice]
                process_library(the_lib)

        except:
            print("Invalid input. Try again..")
else:
    print("No Plex defined, what to do?")

while True:
    epg_url = input("IPTV Provider EPG URL or path: " )

    if test_url(epg_url):
        source_vars['source-epg'] = epg_url
        break
    else:
        print("Error! Something's not right with that URL.")


while True:
    try:
        test4num = int(input("How many simultaneous connections does your IPTV provider allow? " ))

    except ValueError:
        print("Error! This is not a number. Try again.")

    else:
        iptv_vars['iptv-streams'] = test4num
        break

print("The IP address of this machine is: " + my_ip)

if yes_or_no("Is this the IP where Plex is going to find telly? "):
    print("Cool.\n")
else:
    while True:
        telly_ip = input("IP Address of machine where telly is running: " )
        if is_valid_ipv4_address(telly_ip):
            web_vars['web-base'] = telly_ip
            break
        else:
            print("Error! That's not an IP. Try again.")

if yes_or_no("Do you want to turn ffmpeg buffering OFF? "):
    iptv_vars['iptv-ffmpeg'] = ffmpeg_off
else:
    print("Cool.\n")

if yes_or_no("Running telly on the default port [6077]? "):
    print("Cool.\n")
else:
    while True:
        try:
            test4num = int(input("Which port do you want to use? " ))

        except ValueError:
            print("Error! This is not a number. Try again.")
        else:
            web_vars['web-port'] = test4num
            break

while True:
    filter_string = input("Filter: " )

    if is_valid_regex(filter_string):
        source_vars['source-filter'] = filter_string
        break
    else:
        print("Error! That's not a valid regex. Try again.")

if yes_or_no("Use default options for other filter details [most likely yes]? "):
    print("Cool.\n")
else:
    if yes_or_no("Filtering on default tag [group-title]? "):
        print("Cool.\n")
    else:
        while True:
            try:
                print("Tag to filter on? ")
                print(tag_menu())
                filter_tag_num = int(input("=> " ))
                if (filter_tag_num < 1) or (filter_tag_num > 5):
                    raise ValueError
                if (filter_tag_num == 5):
                    source_vars['source-filterkey'] = ""
                    source_vars['source-filterraw'] = "true"
                else:
                    source_vars['source-filterkey'] = get_tag(filter_tag_num)
            except ValueError:
                print("Error! This is not a valid number. Try again.")
            else:
                break

    if yes_or_no("Sorting on default tag [group-title]? "):
        print("Cool.\n")
    else:
        while True:
            try:
                print("\r\nTag to sort on? ")
                print(tag_only_menu())
                filter_tag_num = int(input("=> " ))
                if (filter_tag_num < 1) or (filter_tag_num > 4):
                    raise ValueError
                source_vars['source-sort'] = get_tag(filter_tag_num)
            except ValueError:
                print("Error! This is not a valid number. Try again.")
            else:
                break

def getDiscoveryTemplate():
  return " \
[Discovery] \n\
  Device-Auth = \"{disc-device-auth}\" \n\
  Device-ID = {disc-device-id} \n\
  Device-UUID = \"{disc-device-uuid}\" \n\
  Device-Firmware-Name = \"{disc-device-firmware-name}\" \n\
  Device-Firmware-Version = \"{disc-device-firmware-version}\" \n\
  Device-Friendly-Name = \"{disc-device-friendly-name}\" \n\
  Device-Manufacturer = \"{disc-device-manufacturer}\"  \n\
  Device-Model-Number = \"{disc-device-model-number}\" \n\
  SSDP = {disc-ssdp} \n\
 \n";

def getIPTVTemplate():
  return " \
[IPTV] \n\
  Streams = {iptv-streams} \n\
  Starting-Channel = {iptv-starting-channel} \n\
  XMLTV-Channels = {iptv-xmltv-channels} \n\
  {iptv-ffmpeg} \n\
 \n";

def getLogTemplate():
  return " \
[Log] \n\
  Level = \"{log-level}\" \n\
  Requests = {log-requests} \n\
 \n";

def getWebTemplate():
  return " \
[Web] \n\
  Base-Address = \"{web-base}:{web-port}\" \n\
  Listen-Address = \"{web-listen}:{web-port}\" \n\
 \n";

def getSourceTemplate():
  return " \
[[Source]] \n\
  Name = \"{source-name}\" \n\
  Provider = \"{source-provider}\" \n\
  M3U = \"{source-m3u}\" \n\
  EPG = \"{source-epg}\" \n\
  Filter = \"{source-filter}\" \n\
  FilterKey = \"{source-filterkey}\" \n\
  FilterRaw = {source-filterraw} \n\
  Sort = \"{source-sort}\"\
 \n";

f = open(config_file_name, "w")

disc_out = getDiscoveryTemplate().format(**disc_vars)
f.write(disc_out)

iptv_out = getIPTVTemplate().format(**iptv_vars)
f.write(iptv_out)

log_out = getLogTemplate().format(**log_vars)
f.write(log_out)

web_out = getWebTemplate().format(**web_vars)
f.write(web_out)

source_out = getSourceTemplate().format(**source_vars)
f.write(source_out)

f.close()

print("= Config file contents [telly.config.toml in this directory] ===========================")
f = open(config_file_name, "r")
print(f.read())
print("========================================================================================")

print("All done.")
