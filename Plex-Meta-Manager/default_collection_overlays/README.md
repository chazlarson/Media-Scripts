The `overlay-default-posters.py` will use images from this directory as overlays on the default collection posters.

The files here are intended as examples and were used during testing.  Most likely, you want to replace them with your own images.

Assumptions:
1. these images are 2000x3000 pixels [or a 1:1.5 aspect ratio; they are scaled to 2000x3000 at runtime]
2. these images are named for the "groups" of collections as defined in the images repo [`aspect`, `audio_language`, etc]:
```
Plex-Meta-Manager-Images
├── aspect
├── audio_language
├── award
├── based
├── chart
├── content_rating
├── country
├── decade
├── franchise
├── genre
├── network
├── playlist
├── resolution
├── seasonal
├── separators
├── streaming
├── studio
├── subtitle_language
├── universe
└── year
```

The image called `overlay-template.png` will be used as the fallback overlay in the event that one is missing.

This means that if you want to apply the same overlay to all the default collections, you should delete all these files except for `overlay-template.png`.

`generator.sh` is an example of a script that will generate the files from a template.
