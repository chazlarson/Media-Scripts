# Plex Image Picker

You want a simple way to choose which Plex-supplied image you want in your asset directory.

This presents a web UI that lets you scroll through the images that plex provides for each item [movie, show, season, episode], selecting the one you want by clicking a button.

When you click on an image, it is downloaded to a file system rooted at `assets` with the correct pathing and naming for the Kometa asset directory.

You can then copy that `assets` directory to the Kometa config dir ready for use.

This script does not use anything from the `.env`, but it does make some assumptions:

## Requirements

1. A system that can run Python 3.12 or newer
1. [uv](https://docs.astral.sh/uv/) installed
1. A basic knowledge of how to run Python scripts.
1. You can run a web server on the machine that listens on port 5000

## Setup

### if you use [`direnv`](https://github.com/direnv/direnv):
1. clone the repo
1. cd into the repo dir
1. cd into the app directory [`cd plex-image-picker`]
1. run `direnv allow` as the prompt will tell you to
1. direnv runs `uv sync` and activates `.venv`

Ha ha only serious.

To set it up without those things:

#### Python

1. clone repo
   ```
   git clone https://github.com/chazlarson/Media-Scripts.git
   ```
1. cd to repo directory
   ```
   cd Media-Scripts
   ```
1. cd to application directory
   ```
   cd plex-image-picker
   ```
1. Install the locked dependencies with `uv sync`
1. Run with `uv run flask run`
1. Go to one of the URLs presented.

#### Docker

1. build the docker image:
   ```
   docker build -t plex-image-picker .
   ```
2. run the container:
   ```
   docker run -p 5000:5000 -v /opt/Media-Scripts/plex_art_app/assets:/assets:rw plex-image-picker
   ```
   Change the port and path as needed, of course.
3. Go to one of the URLs presented, as appropriate.

#### Interface

You'll be asked to enter connection details. You can change the directory where the images will go on this initial setup screen:

![](images/connect.png)

Then you will choose a library:

![](images/libraries.png)

You'll see a grid displaying all posters available for the first item in the library:

![](images/movies-posters.png)

You can choose to view backgrounds instead of posters:

![](images/movies-backgrounds.png)

When you click the Download button, the file will be downloaded to the asset directory; a flash message will report the path:

![](images/movies-download.png)

Click through the movies/shows with the top row of buttons; click through pages of images with the lower set of buttons.

Navigate to a specific page of posters with the dropdown on the right.

Clicking the title in the upper left will take you back to the library list.

In a Show library, you will be able to choose to view posters/backgrounds for shows, seasons, or episodes:

![](images/shows-posters.png)
![](images/seasons-posters.png)
![](images/episodes-posters.png)
