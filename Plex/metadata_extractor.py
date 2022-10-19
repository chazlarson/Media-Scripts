from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
import pathlib
from timeit import default_timer as timer
from helpers import booler, redact, getTID, validate_filename, getPath

# // TODO: improved error handling
# // TODO: TV Theme tunes
# // TODO: Process Music libraries
# // TODO: Process Photo libraries

# import tvdb_v4_official

start = timer()

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
TMDB_KEY = os.getenv('TMDB_KEY')
TVDB_KEY = os.getenv('TVDB_KEY')
REMOVE_LABELS = os.getenv('REMOVE_LABELS')

if REMOVE_LABELS:
    lbl_array = REMOVE_LABELS.split(",")

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

local_dir = f"{os.getcwd()}/posters"

os.makedirs(local_dir, exist_ok=True)

show_dir = f"{local_dir}/shows"
movie_dir = f"{local_dir}/movies"

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(30)))
    sys.stdout.flush()

print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = 'original'

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
print(f"getting items from [{LIBRARY_NAME}]...")
items = plex.library.section(LIBRARY_NAME).all()
item_total = len(items)
print(f"looping over {item_total} items...")
item_count = 1
for item in items:
    tmpDict = {}
    imdb_id, tmdb_id, tvdb_id = getTID(item.guids)
    item_count = item_count + 1
    try:
        progress(item_count, item_total, item.title)
        pp = None
        if item.TYPE == 'show':
            try:
                pp = tmdb.tv_show(tmdb_id).poster_path if tmdb_id else tmdb.find_by_id(tvdb_id=tvdb_id).tv_results[0].poster_path
            except:
                pp = "NONE"
            tgt_dir = show_dir
        else:
            pp = tmdb.movie(tmdb_id).poster_path
            tgt_dir = movie_dir

        if pp is not None:
            if pp == "NONE":
                posters = item.posters()
                item.setPoster(posters[0])
            else:
                ext = pathlib.Path(pp).suffix
                posterURL = f"{base_url}{size_str}{pp}"
                local_file = f"{tgt_dir}/{item.ratingKey}{ext}"
                if not os.path.exists(local_file):
                    r = requests.get(posterURL, allow_redirects=True)
                    open(f"{local_file}", 'wb').write(r.content)
                item.uploadPoster(filepath=local_file)
        else:
            progress(item_count, item_total, "unknown type: " + item.title)

        if len(lbl_array) > 0:
            removeLabels(item)

    except Exception as ex:
        progress(item_count, item_total, "EX: " + item.title)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")

#   libraryquestions: [
#     {
#       type: "confirm",
#       name: "processLibrary",
#       message: "Do you want to process this library?",
#       default: true
#     },
#     {
#       type: "confirm",
#       name: "overwriteExisting",
#       message: "Overwrite existing files?",
#       default: false,
#       when: function(answers){
#         return answers.processLibrary;
#       }
#     },
#     {
#       type: "confirm",
#       name: "savemeta",
#       message: "Save metadata file?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary;
#       }
#     },
#     {
#       type: "confirm",
#       name: "savethumbs",
#       message: "Save thumbnail image?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary;
#       }
#     }
#   ],
#   movielibraryquestions: [
#     {
#       type: "confirm",
#       name: "saveart",
#       message: "Save artwork?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary;
#       }
#     },
#     {
#       type: "confirm",
#       name: "moviesinownfolder",
#       message: "Are all movies in their own folder?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary;
#       }
#     },
#     {
#       type: "confirm",
#       name: "savefolderposter",
#       message: "Save poster.jpg from thumbnail?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.moviesinownfolder
#       }
#     },
#     {
#       type: "confirm",
#       name: "savefolderthumb",
#       message: "Save folder.jpg from thumbnail?",
#       when: function(answers){
#         return answers.processLibrary && answers.moviesinownfolder
#       }
#     },
#     {
#       type: "confirm",
#       name: "savefolderart",
#       message: "Save art.jpg from artwork?",
#       when: function(answers){
#         return answers.processLibrary && answers.moviesinownfolder
#       }
#     }
#   ],
#   tvlibraryquestions: [
#     {
#       type: "confirm",
#       name: "tvseriesinownfolder",
#       message: "Are all TV Series in their own folder?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseriesmeta",
#       message: "Save metadata for series?",
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseriesposter",
#       message: "Save show.jpg from thumbnail?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseriesfolderthumb",
#       message: "Save folder.jpg from thumbnail?",
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseriesfolderart",
#       message: "Save art.jpg from artwork?",
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseriesbanner",
#       message: "Save banner.jpg?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseriestheme",
#       message: "Save theme.mp3?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseasonmeta",
#       message: "Save metadata for season?",
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseasonposter",
#       message: "Save poster for season?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseasonart",
#       message: "Save artwork for season?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },

#     {
#       type: "confirm",
#       name: "tvseasonsinownfolder",
#       message: "Are all Seasons in their own sub folder?",
#       default: true,
#       when: function(answers){
#         return answers.processLibrary && answers.tvseriesinownfolder;
#       }
#     },
#     {
#       type: "confirm",
#       name: "saveseasonfolderthumb",
#       message: "Save folder.jpg from thumbnail for seasons?",
#       when: function(answers){
#         return answers.processLibrary && answers.tvseasonsinownfolder;
#       }
#     },
#   ]
# }

# var configurationMode = false;

# var config = {}, libraries = {};

# var totalactions = 0;

# var discoveryprogress = new progress(
#   chalk.bgBlue(" INFO ") + " Discovered " + chalk.bold(":discovered") + " items",
#   {
#     width: 5,
#     total: 1,
#     complete: ".",
#     incomplete: " ",
#     renderThrottle: 500
#   }
# );

# var processingprogress = new progress(
#   chalk.bgBlue(" INFO ") + " Saving metadata " + chalk.bold("[:bar]") + " :percent :etas",
#   {
#     complete: "=",
#     incomplete: " ",
#     width: 20,
#     total: 1,
#     renderThrottle: 500
#   }
# )

# var discoveryqueue = async.queue(function(task, callback){
#   cursor.hide();
#   if(task.message)
#     console.log(task.message);

#   task.execute(function(){

#     // increment discoveryprogress so that it never ends!
#     discoveryprogress.total++;
#     discoveryprogress.tick({discovered: totalactions});
#     callback();
#   });
# }, throttle);

# discoveryqueue.drain = function(){
#   //console.log(chalk.bgBlue(" INFO ") + " Discovered " + chalk.bold(totalactions) + " save actions.");
#   console.log("");
#   if(totalactions <= 0){
#     done();
#   } else {
#     processingprogress.total = processingqueue.length();
#     processingqueue.resume();
#   }
# }

# var processingqueue = async.queue(function(task, callback){
#   task.execute(function(){
#     processingprogress.tick({message: task.message});
#     callback();
#   });
# }, throttle);
# processingqueue.pause();
# processingqueue.drain = function(){
#   done();
# }

# function done(){
#   console.log (chalk.bgGreen.black(" Done ") + " Finished exporting metadata! ");
#   cursor.show();
# }

# function loadConfiguration(){
#   var configstring = '';
#   if(fs.existsSync('config.json'))
#     configstring = fs.readFileSync('config.json');

#   if(configstring != ''){
#     config = JSON.parse(configstring);
#   }else{
#     console.log(chalk.bgYellow.black(" WARN ") + chalk.bold(' No configuration settings found!'));
#     configurationMode = true;
#   }
# }

# function loadLibraries(){
#   var librariesstring = ''
#   if(fs.existsSync('libraries.json'))
#     librariesstring = fs.readFileSync('libraries.json');

#   if(librariesstring != ''){
#     libraries = JSON.parse(librariesstring);
#   }
# }

# function saveConfiguration(configjson){
#   fs.writeFile('config.json', JSON.stringify(configjson, null, "  "), function(err){
#     if(err)
#       console.log(chalk.brRed(" ERR  ") + " " + err);

#     console.log(chalk.bgBlue(" INFO ") + " Configuration saved!");
#   });
# }

# function saveLibraryConfiguration(libraryjson){
#   fs.writeFile('libraries.json', JSON.stringify(libraryjson, null, "  "), function(err){
#     if(err)
#       console.log(chalk.brRed(" ERR  ") + " " + err);

#     console.log(chalk.bgBlue(" INFO ") + " Library configuration saved!");
#   });
# }

# function addToken(URL)
# {
#   return URL + "?X-Plex-Token=" + config.token
# }

# function doScrape(){
#   var rootaddr = config.protocol + "://" + config.address + ":" + config.port;

#   // http://[PMS_IP_Address]:32400/?X-Plex-Token=YourTokenGoesHere

#   console.log(chalk.bgBlue(" INFO ") + chalk.bold(" " + rootaddr));
#   console.log(chalk.bgBlue(" INFO ") + chalk.bold(" Discovering Libraries"));
#   makeGetRequest(rootaddr + '/library/sections', function(response, body){
#     parseString(body, function(error, data){
#       var libs = [];
#       var libraryconfigupdated = false;
#       async.each(data.MediaContainer.Directory, function(discoveredlibrary, itemcallback){
#         libs.push({key: discoveredlibrary.$.key, title: discoveredlibrary.$.title, type: discoveredlibrary.$.type});
#       });
#       async.eachSeries(libs, function(lib, itemcallback){
#         if(!libraries[lib.key]){
#           libraryconfigupdated = true;
#           console.log(chalk.bgBlue(" INFO ") + " New library discovered " + chalk.bold("\"" + lib.title + "\""));
#           var thislibquestions = questions.libraryquestions.slice();
#           switch(lib.type){
#             case "movie":
#               thislibquestions = thislibquestions.concat(questions.movielibraryquestions);
#               break;
#             case "show":
#               thislibquestions = thislibquestions.concat(questions.tvlibraryquestions);
#               break;
#           }
#           inquirer.prompt(thislibquestions, function(answers){
#             libraries[lib.key] = answers;
#             libraries[lib.key]["name"] = lib.title;
#             itemcallback();
#           });
#         }else{
#           itemcallback();
#         }
#       }, function(error){
#         if(error)
#           console.log(chalk.bgRed(" ERR  ") + " " + error);
#           if(libraryconfigupdated){
#             console.log(chalk.bgBlue(" INFO ") + " Library configuration changed");
#             inquirer.prompt([{type: "confirm", name: "saveLibraryConfig", message: "Save library configuration?", default: true}],
#             function(answers){
#               if(answers.saveLibraryConfig){
#                 saveLibraryConfiguration(libraries);
#               }
#               async.each(libs, function(lib, itemcallback){

#                   if(libraries[lib.key].processLibrary){
#                     processLibrary(rootaddr, lib.key, lib.type, lib.title);
#                   }
#                   itemcallback();
#               });
#             });
#           }else{
#             async.each(libs, function(lib, itemcallback){

#                 if(libraries[lib.key].processLibrary){
#                   processLibrary(rootaddr, lib.key, lib.type, lib.title);
#                 }
#                 itemcallback();
#             });
#           }
#       });

#     });
#   }, function(error){
#     console.log(chalk.bgRed.white(" Err  ") + " " + error);
#   });
# }

# function processLibrary(rootaddr, librarykey, librarytype, libraryname){
#   switch(librarytype){
#     case "movie":
#       makeGetRequestDiscovery(rootaddr + "/library/sections/" + librarykey + "/all", function(response, body){
#         parseString(body, function(error, data){
#           async.each(data.MediaContainer.Video, function(video, itemcallback){
#             processMovie(rootaddr, video.$.key);
#             itemcallback();
#           });
#         })
#       });
#       break;
#     case "show":
#       makeGetRequestDiscovery(rootaddr + "/library/sections/" + librarykey + "/all", function(response, body){
#         parseString(body, function(error, data){

#           async.each(data.MediaContainer.Directory, function(directory, itemcallback){

#             processSeries(rootaddr, directory.$.key);
#             itemcallback();
#           });
#         })
#       });
#       break;
#   }
# }

# function processMovie(rootaddr, url){
#   makeGetRequestDiscovery(rootaddr + url, function(response, body){
#     parseString(body, function(error, data){
#       var sectionid = data.MediaContainer.$.librarySectionID;
#       async.each(data.MediaContainer.Video, function(video, itemcallback){
#         var videokey = video.$.key;
#         var videotitle = video.$.title;
#         var thumburl = video.$.thumb;
#         var arturl = video.$.art;

#         var videoyear = video.$.year;
#         var videosorttitle = 'titleSort' in video ? video.$.titleSort : videotitle;
#         var videoorigtitle = 'originalTitle' in video ? video.$.originalTitle : videotitle;
#         var videotagline = video.$.tagline;
#         var videosummary = video.$.summary;

#         var pmm_metadata = 'metadata:{os.linesep}' +
#             '  "' + videotitle + '":{os.linesep}' +
#             '    title: "' + videotitle + '"{os.linesep}' +
#             '    year: ' + videoyear + '{os.linesep}' +
#             '    sort_title: "' + videosorttitle + '"{os.linesep}' +
#             '    original_title: "' + videoorigtitle + '"{os.linesep}' +
#             '    tagline: "' + videotagline + '"{os.linesep}' +
#             '    summary: "' + videosummary + '"{os.linesep}'

#         totalactions++;
#         async.each(video.Media, function(media, mediaitemcallback){
#           if(!media.$.target){
#             async.each(media.Part, function(part, partitemcallback){
#               var parentpath = path.dirname(part.$.file)

#               var targetpath = part.$.file;
#               var targetparent = parentpath;

#               if(config.mediaBasePath != ''){
#                 if(config.metadataPath != ''){
#                   targetpath = part.$.file.replace(config.mediaBasePath, config.metadataPath);
#                   targetparent = path.dirname(targetpath);
#                   fs.mkdirSync(targetparent, { recursive: true })
#                 }
#               }

#               if(libraries[sectionid].savemeta){
#                 if(!fs.existsSync(targetpath + ".meta.xml") || libraries[sectionid].overwriteExisting){
#                   downloadmetadata(rootaddr + videokey, targetpath + ".meta.xml");
#                 }
#               }
#               if(libraries[sectionid].savethumbs){
#                 if(!fs.existsSync(targetpath + ".thumb.jpg") || libraries[sectionid].overwriteExisting){
#                   downloadfile(rootaddr + thumburl, targetpath + ".thumb.jpg");
#                 }
#               }
#               if(libraries[sectionid].savethumbs){
#                 if(!fs.existsSync("folder.jpg") || libraries[sectionid].overwriteExisting){
#                   downloadfile(rootaddr + thumburl, path.join(targetparent, "folder.jpg"));
#                 }
#               }
#               if(libraries[sectionid].savethumbs){
#                 pmm_metadata = pmm_metadata + '    file_poster: "' + path.join(targetparent, "poster.jpg") + '"{os.linesep}'
#                 if(!fs.existsSync(path.join(targetparent, "poster.jpg")) || libraries[sectionid].overwriteExisting){
#                   downloadfile(rootaddr + thumburl, path.join(targetparent, "poster.jpg"));
#                 }
#               }
#               if(libraries[sectionid].saveart){
#                 if(!fs.existsSync(targetpath + '.art.jpg') || libraries[sectionid].overwriteExisting){
#                   downloadfile(rootaddr + arturl, targetpath + ".art.jpg");
#                 }
#               }
#               if(libraries[sectionid].savefolderart){
#                 pmm_metadata = pmm_metadata + '    file_background: "' + path.join(targetparent, "art.jpg") + '"{os.linesep}'

#                 if(!fs.existsSync(path.join(targetparent, "art.jpg")) || libraries[sectionid].overwriteExisting){
#                   downloadfile(rootaddr + arturl, path.join(targetparent, "art.jpg"));
#                 }
#               }
#               // write pmm-metadata.yml
#               fs.writeFile(path.join(targetparent, "pmm-metadata.yml"), pmm_metadata, (error) => {
#                   // In case of a error throw err exception.
#                   if (error) throw err;
#               })
#               partitemcallback();
#             });
#           }
#           mediaitemcallback();
#         });
#         itemcallback();
#       });
#     });
#   });
# }

# function processSeries(rootaddr, url){

#   makeGetRequestDiscovery(rootaddr + url, function(request, body){
#     parseString(body, function(error, data){
#       async.each(data.MediaContainer.Directory,
#         function(directory, directorycallback){

#           if(directory.$.type !== undefined && directory.$.type == "season"){
#             processSeason(rootaddr, directory.$.key);
#           }

#           directorycallback();
#         },
#         function(err){
#           // TODO: improved error handling
#         }
#       );
#     });
#   });
# }
# function processSeason(rootaddr, url){
#   makeGetRequestDiscovery(rootaddr + url, function(request, body){
#     parseString(body, function(error, data){

#       var seasonfolder = "";
#       var seriesfolder = "";

#       var librarySectionID = data.MediaContainer.$.librarySectionID;

#       var seasonfolders = [];

#       async.each(data.MediaContainer.Video,
#         function(video, videocallback){

#           var videokey = video.$.key;
#           var thumburl = video.$.thumb;
#           var arturl = video.$.art;

#           async.each(video.Media,
#             function(media, mediaitemcallback){
#               if(!media.$.target){
#                 // when a media has a target, it is an optimized version!
#                 async.each(media.Part,
#                   function(part, partitemcallback){

#                     totalactions++;

#                     var seasonfolder = path.dirname(part.$.file);
#                     var seriesfolder = seasonfolder;
#                     if(libraries[librarySectionID].tvseasonsinownfolder){
#                       seriesfolder = path.normalize(path.join(seriesfolder, "/.."));

#                     }
#                     if(seasonfolders.indexOf(seasonfolder) < 0){
#                       seasonfolders.push(seasonfolder)
#                       downloadseasonassets(rootaddr, video.$.parentKey, seasonfolder);
#                     }

#                     if(libraries[librarySectionID].savemeta){
#                       if(!fs.existsSync(part.$.file + ".meta.xml") || libraries[librarySectionID].overwriteExisting){
#                         downloadmetadata(rootaddr + videokey, part.$.file + ".meta.xml");
#                       }
#                     }

#                     if(libraries[librarySectionID].savethumbs){
#                       if(!fs.existsSync(part.$.file + ".thumb.jpg") || libraries[librarySectionID].overwriteExisting){
#                         downloadfile(rootaddr + thumburl, part.$.file + ".thumb.jpg");
#                       }
#                     }


#                     partitemcallback();
#                   }
#                 );
#               }
#               mediaitemcallback();
#             }
#           );


#           videocallback();
#         },
#         function(err){
#           // TODO: improved error handling


#         }
#       );

#     });
#   });
# }
# function downloadseasonassets(rootaddr, url, folderpath){
#   makeGetRequestDiscovery(rootaddr + url, function(request, body){
#     parseString(body, function(error, data){
#       var librarySectionID = data.MediaContainer.$.librarySectionID;
#       async.each(data.MediaContainer.Directory, function(directory, callback){
#         var seasonName = directory.$.title;
#             seasonName = seasonName.replace(/[^a-zA-Z0-9]/g, "-")
#         if(libraries[librarySectionID].saveseasonmeta){
#           if(!fs.existsSync(path.join(folderpath, seasonName + ".meta.xml")) || libraries[librarySectionID].overwriteExisting){
#             downloadmetadata(rootaddr + directory.$.key, path.join(folderpath, seasonName + ".meta.xml"));
#           }
#         }
#         if(libraries[librarySectionID].saveseasonfolderthumb){
#           if(!fs.existsSync(path.join(folderpath, "folder.jpg")) || libraries[librarySectionID].overwriteExisting){
#             downloadfile(rootaddr + directory.$.thumb, path.join(folderpath, "folder.jpg"));
#           }
#         }
#         if(libraries[librarySectionID].saveseasonposter){

#             if(!fs.existsSync(path.join(folderpath, seasonName + ".jpg")) || libraries[librarySectionID].overwriteExisting){
#               downloadfile(rootaddr + directory.$.thumb, path.join(folderpath, seasonName + ".jpg"));
#             }
#         }

#         if(libraries[librarySectionID].saveseasonart){
#           if(!fs.existsSync(path.join(folderpath, seasonName + "-art.jpg")) || libraries[librarySectionID].overwriteExisting){
#             downloadfile(rootaddr + directory.$.art, path.join(folderpath, seasonName + "-art.jpg"));
#           }
#         }

#         var seriespath = ""
#         if(libraries[librarySectionID].tvseasonsinownfolder){
#           seriespath = path.normalize(path.join(folderpath, "/.."));
#         }else{
#           seriespath = folderpath;
#         }

#         downloadseriesassets(rootaddr, directory.$.parentKey, seriespath);

#         callback();
#       });
#     });
#   });

# }
# function downloadseriesassets(rootaddr, url, folderpath){
#   makeGetRequestDiscovery(rootaddr + url, function(request, body){
#     parseString(body, function(error, data){
#       var librarySectionID = data.MediaContainer.$.librarySectionID;
#       async.each(data.MediaContainer.Directory, function(directory, callback){
#         if(libraries[librarySectionID].saveseriesmeta){
#           if(!fs.existsSync(path.join(folderpath, "show.meta.xml")) || libraries[librarySectionID].overwriteExisting){
#             downloadmetadata(rootaddr + url, path.join(folderpath, "show.meta.xml"));
#           }
#         }
#         if(libraries[librarySectionID].saveseriesposter){
#           if(!fs.existsSync(path.join(folderpath, "show.jpg")) || libraries[librarySectionID].overwriteExisting){
#             if(directory.$.thumb !== undefined)
#               downloadfile(rootaddr + directory.$.thumb, path.join(folderpath, "show.jpg"));
#           }
#         }
#         if(libraries[librarySectionID].saveseriesfolderthumb){
#           if(!fs.existsSync(path.join(folderpath, "folder.jpg")) || libraries[librarySectionID].overwriteExisting){
#             if(directory.$.thumb !== undefined)
#               downloadfile(rootaddr + directory.$.thumb, path.join(folderpath, "folder.jpg"));
#           }
#         }

#         if(libraries[librarySectionID].saveseriesfolderart){
#           if(!fs.existsSync(path.join(folderpath, "art.jpg")) || libraries[librarySectionID].overwriteExisting){
#             if(directory.$.art !== undefined)
#               downloadfile(rootaddr + directory.$.art, path.join(folderpath, "art.jpg"));
#           }
#         }
#         if(libraries[librarySectionID].saveseriesbanner){
#           if(!fs.existsSync(path.join(folderpath, "banner.jpg")) || libraries[librarySectionID].overwriteExisting){
#             if(directory.$.banner !== undefined)
#               downloadfile(rootaddr + directory.$.banner, path.join(folderpath, "banner.jpg"));
#           }
#         }
#         if(libraries[librarySectionID].saveseriestheme){
#           if(!fs.existsSync(path.join(folderpath, "theme.mp3")) || libraries[librarySectionID].overwriteExisting){
#             console.log(directory.$.theme);
#             if(directory.$.theme !== undefined)
#               downloadfile(rootaddr + directory.$.theme, path.join(folderpath, "theme.mp3"));
#           }
#         }
#       });
#     });
#   });
# }

# function downloadmetadata(url, filepath){
#   var task = {
#     message: "",
#     execute: function(callback){
#       request(url, function(error, response, body){
#         if(!error && response.statusCode == 200){
#           console.log("writing " + filepath);
#           fs.writeFile(filepath, body);
#           callback();
#         }else{
#           if(error){
#             if(errorcallback)
#               // TODO: improved error handling
#               callback();
#           }else{
#             // TODO: process additional response codes
#             callback();
#           }
#         }
#       });
#     }
#   };
#   processingqueue.push(task);
# }

# function downloadfile(url, filepath){

#   var task = {
#     message: "",
#     execute: function(callback){

#       request(addToken(url)).pipe(fs.createWriteStream(filepath)).on('close', function(){
#         callback();
#       });
#     }
#   };
#   processingqueue.push(task);
# }

# function makeGetRequest(url, successcallback, errorcallback){
#   request(addToken(url), function(error, response, body){
#     if(!error && response.statusCode == 200){
#       successcallback(response, body);
#     }else{
#       if(error){
#         if(errorcallback)
#           errorcallback(error);
#       }else{
#         console.log(chalk.bgBlue(" INFO ") + chalk.bold(response.statusCode + " from " + url ));
#         // TODO: process additional response codes
#       }
#     }
#   });
# }
# function makeGetRequestDiscovery(url, successcallback, errorcallback){

#   var task = {
#     message: null,
#     execute: function(callback){
#       request(addToken(url), function(error, response, body){
#         if(!error && response.statusCode == 200){
#           successcallback(response, body);
#           callback();
#         }else{
#           if(error){
#             if(errorcallback)
#               errorcallback(error);
#               callback();
#           }else{
#             // TODO: process additional response codes
#             callback();
#           }
#         }
#       });
#     }
#   };
#   discoveryqueue.push(task);
# }

# // load from saved settings when available
# loadConfiguration();
# loadLibraries();

# // process command line and build configuration object
# process.argv.forEach(function (val, index, array) {
#   if(val == '--configure'){
#     // enter configuration module
#     configurationMode = true;
#   }
# });

# // configuration mode - read settings from user input
# if(configurationMode){
#   console.log(chalk.bgBlue(" INFO ") + chalk.bold(" Entering configuration mode for PlexMetadataExtractor"))
#   inquirer.prompt(questions.configquestions, function(answers){
#     saveConfiguration(answers);
#     config = answers;
#     doScrape();
#   });
# }else{
#   doScrape();
# }