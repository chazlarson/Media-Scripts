from flask import Flask, render_template, send_from_directory, jsonify, Response
from PIL import Image
import os
import shutil
import json
import re

# TODO: Store stuff in the mediascripts.sqlite
# TODO: Make it prettier
# TODO: Show/hide season/episode checkboxes on movies
# TODO: Support flat asset directories
# TODO: Allow filtering by image type
# TODO: parameterize asset directories
# TODO: deal with no library folders

# 0.1.0: Initial release
# 0.1.1: Use os.path to build paths
#        Deal with NA category as appropriate

VERSION = "0.1.1"

app = Flask(__name__    )

# Path to your 'assets' directory
ASSETS_DIR = 'assets'
ACTIVE_ASSETS_DIR = 'active_assets'

asset_path = os.path.join(app.root_path, ASSETS_DIR)
active_path = os.path.join(app.root_path, ACTIVE_ASSETS_DIR)

# JSON file for storing copied images information
TRACKING_FILE = 'copied_images.json'

# Regular expression patterns for different types of images
IMAGE_PATTERNS = {
    'item': re.compile(r'^poster.*\.(jpg|jpeg|png)$', re.IGNORECASE),
    'background': re.compile(r'^background.*\.(jpg|jpeg|png)$', re.IGNORECASE),
    'season': re.compile(r'^Season(\d{2,3}).*\.(jpg|jpeg|png)$', re.IGNORECASE),
    'season_background': re.compile(r'^Season(\d{2,3})-background.*\.(jpg|jpeg|png)$', re.IGNORECASE),
    'episode': re.compile(r'^S(\d+)E(\d+).*\.(jpg|jpeg|png)$', re.IGNORECASE),
    'episode_background': re.compile(r'^S(\d+)E(\d+)-background.*\.(jpg|jpeg|png)$', re.IGNORECASE),
}

# Target names for different types of images
ASSET_FILENAMES = {
    'item': "poster.ext",
    'background': "background.ext",
    'season': "Season##.ext",
    'season_background': "Season##_background.ext",
    'episode': "S##E##.ext",
    'episode_background': "S##E##_background.ext"
}

def directory_contains_images(path):
    """Check if the directory directly contains image files."""
    for item in os.listdir(path):
        if item.endswith(('.png', '.jpg', '.jpeg')):
            return True
    return False

def get_directories(path):
    """Return a sorted list of directories at the given path."""
    return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

@app.route('/')
def home():
    libraries = get_directories(ASSETS_DIR)
    return render_template('home.html', libraries=libraries, asset_dir=asset_path, active_dir=active_path)

def update_tracking_info(library_name, category_name, show_name, filename):
    """Update the tracking information for the current show or movie."""
    try:
        with open(TRACKING_FILE, 'r') as file:
            tracking_info = json.load(file)
    except FileNotFoundError:
        tracking_info = {}

    type_pattern = re.compile("(.*)-\d\d\d.*")
    match = type_pattern.match(filename)

    target_type = None
    if match:
        target_type = match.groups()[0]

    key = f"{library_name}/{category_name}/{show_name}"
    if key not in tracking_info:
        tracking_info[key] = {}
        tracking_info[key]['images'] = []
    new_list = []
    for img in tracking_info[key]['images']:
        match = type_pattern.match(img)

        this_type = None
        if match:
            this_type = match.groups()[0]

        if this_type != target_type:
            new_list.append(img)

    new_list.append(filename)

    tracking_info[key]['images'] = new_list

    with open(TRACKING_FILE, 'w') as file:
        json.dump(tracking_info, file)

def get_image_type(filename):
    image_type = None

    for pattern in IMAGE_PATTERNS:
        target_pattern = IMAGE_PATTERNS[pattern]
        match = target_pattern.match(filename)

        if match:
            image_type = pattern

    return image_type

def get_target_image(filename):

    image_type = get_image_type(filename)
    season_number = None
    episode_number = None
    extension = filename.split('.')[-1]
    format_key = ""
    target_format = ASSET_FILENAMES['item']

    for pattern in IMAGE_PATTERNS:
        target_pattern = IMAGE_PATTERNS[pattern]
        match = target_pattern.match(filename)

        background_pattern = re.compile(r'^.*background.*$')
        background = background_pattern.match(filename)
        # is this a background?
        if background:
            target_format = ASSET_FILENAMES['background']

        season_pattern = re.compile(r'^Season(\d{2,3})(?:[^.]*)\.(.+)$')
        episode_pattern = re.compile(r'^S(\d+)E(\d+)(?:[^.]*)\.(.+)$')

        new_filename = target_format.replace('ext', extension)

        match = season_pattern.match(filename)

        if match:
            # If the filename matches the pattern, use the matched season number and extension for the new filename
            season_number, extension = match.groups()
            # this is a season image
            target_format = ASSET_FILENAMES['season']
            if background:
                target_format = ASSET_FILENAMES['season_background']

            # 'season': "Season##.ext",
            # 'season_background': "Season##_background.ext",

            new_filename = target_format.replace('ext', extension)
            new_filename = new_filename.replace('Season##', f"Season{season_number}")

        else:
            match = episode_pattern.match(filename)
            if match:
                # this is an episode image
                # If the filename matches the pattern, use the matched season number and extension for the new filename
                season_number, episode_number, extension = match.groups()
                target_format = ASSET_FILENAMES['episode']
                if background:
                    target_format = ASSET_FILENAMES['episode_background']
            # 'episode': "S##E##.ext",
            # 'episode_background': "S##E##_background.ext"

            new_filename = target_format.replace('ext', extension)
            new_filename = new_filename.replace('S##', f"S{season_number}")
            new_filename = new_filename.replace('E##', f"E{episode_number}")

    return new_filename

@app.route('/library/<library_name>/')
def library(library_name):
    library_path = os.path.join(ASSETS_DIR, library_name)
    directories = get_directories(library_path)

    # Check if the first directory contains images, indicating direct show/movie directories
    if directories and directory_contains_images(os.path.join(library_path, directories[0])):
        shows = directories
        return render_template('direct_shows.html', library_name=library_name, shows=shows)
    else:
        categories = directories
        return render_template('library.html', library_name=library_name, categories=categories, asset_dir=ASSETS_DIR, active_dir=ACTIVE_ASSETS_DIR)

@app.route('/library/<library_name>/<category_name>/')
def category(library_name, category_name):
    category_path = os.path.join(ASSETS_DIR, library_name, category_name)
    shows = get_directories(category_path)
    return render_template('category.html', library_name=library_name, category_name=category_name, shows=shows)

def get_active_image_list(target_key):
    try:
        with open(TRACKING_FILE, 'r') as file:
            active_images = json.load(file)
    except Exception as e:
        return None

    image_list = active_images.get(target_key)

    return image_list

@app.route('/active_images/<library_name>/<category_name>/<show_name>')
def get_active_images(library_name, category_name, show_name):
    """Retrieve the active images for a show/movie, if any."""
    key = f"{library_name}/{category_name}/{show_name}"
    data = {'status': 'not_found', 'key': key}

    image_list = get_active_image_list(key)

    if image_list is not None:
        data = {'status': 'success', 'images': image_list}

    return jsonify(data)

@app.route('/copy_image/<library_name>/<category_name>/<show_name>/<filename>')
def copy_image(library_name, category_name, show_name, filename):

    image_type = get_image_type(filename)

    # Ensure the image type is valid
    if image_type not in IMAGE_PATTERNS:
        return jsonify({'status': 'error', 'message': 'Invalid image type'}), 400

    new_filename = get_target_image(filename)

    source_path = os.path.join(ASSETS_DIR, library_name, category_name, show_name, filename)
    target_dir = os.path.join(ACTIVE_ASSETS_DIR, library_name, category_name, show_name)
    if category_name == 'NA':
        source_path = os.path.join(ASSETS_DIR, library_name, show_name, filename)
        target_dir = os.path.join(ACTIVE_ASSETS_DIR, library_name, show_name)

    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, new_filename)

    shutil.copy2(source_path, target_path)
    update_tracking_info(library_name, category_name, show_name, filename)

    key = f"{library_name}/{category_name}/{show_name}"
    image_list = get_active_image_list(key)

    return jsonify({'status': 'success', 'images': image_list})

def get_copied_image(library_name, category_name, show_name):
    """Retrieve the copied image for a show/movie, if any."""
    try:
        with open(TRACKING_FILE, 'r') as file:
            copied_images = json.load(file)
    except FileNotFoundError:
        return None

    key = f"{library_name}/{category_name}/{show_name}"
    return copied_images.get(key)

@app.route('/show/<library_name>/<category_name>/<show_name>/')
def show(library_name, category_name, show_name):
    show_path = os.path.join(ASSETS_DIR, library_name, category_name, show_name)
    category_path = os.path.join(ASSETS_DIR, library_name, category_name)
    image_url = f"{library_name}/{category_name}/{show_name}"
    if category_name == 'NA':
        show_path = os.path.join(ASSETS_DIR, library_name, show_name)
        category_path = os.path.join(ASSETS_DIR, library_name)
        image_url = f"{library_name}/{show_name}"

    images_info = []
    for img in os.listdir(show_path):
        if img.endswith(('png', 'jpg', 'jpeg')):
            img_path = os.path.join(show_path, img)
            img_type = get_image_type(img)
            with Image.open(img_path) as im:
                width, height = im.size
                images_info.append({'name': img, 'width': width, 'height': height, 'type': img_type})

    new_images_info = sorted(images_info, key=lambda x: x['name'])

    shows = sorted(os.listdir(category_path))  # Ensure shows are sorted alphabetically
    current_index = shows.index(show_name)
    prev_show = shows[current_index - 1] if current_index > 0 else None

    next_show = shows[current_index + 1] if current_index < len(shows) - 1 else None

    return render_template('show.html', library_name=library_name, category_name=category_name, show_name=show_name, images_info=new_images_info, prev_show=prev_show, next_show=next_show, image_url=image_url)

@app.route('/images/<library_name>/<category_name>/<show_name>/<filename>')
def image(library_name, category_name, show_name, filename):
    image_path = os.path.join(ASSETS_DIR, library_name, category_name, show_name)
    if category_name == 'NA':
        image_path = os.path.join(ASSETS_DIR, library_name, show_name)

    return send_from_directory(image_path, filename)

@app.route('/loader')
def loader():
    image_path = os.path.join(".")

    return send_from_directory(image_path, "loading.gif")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

