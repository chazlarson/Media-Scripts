""" Module puts overlays on all default Kometa collection posters """
import pathlib
from pathlib import Path
from git.repo.base import Repo
from PIL import Image
from alive_progress import alive_bar

IMAGE_REPO = "https://github.com/Kometa-Team/Default-Images"
LOCAL_FOLDER = "Kometa-Images"
OVERLAID_FOLDER = "Kometa-Images-Overlaid"
OVERLAY_SOURCE_FOLDER = "default_collection_overlays"
OVERLAY_BASE_IMAGE = "overlay-template.png"

SRC_REPO = None
theRepoPath = Path(LOCAL_FOLDER)
theTargetPath = Path(OVERLAID_FOLDER)

if not theRepoPath.exists():
    print(f"Cloning {IMAGE_REPO}")
    print("This may take some time with no display")
    SRC_REPO = Repo.clone_from(IMAGE_REPO, LOCAL_FOLDER)
else:
    print(f"Fetch/Pull on {LOCAL_FOLDER}")
    SRC_REPO = Repo(LOCAL_FOLDER)
    SRC_REPO.remotes.origin.fetch()
    SRC_REPO.remotes.origin.pull()

global_overlay = Path(f"{OVERLAY_SOURCE_FOLDER}/{OVERLAY_BASE_IMAGE}")
GLOBAL_OVERLAY_IM = None

if global_overlay.exists():
    print(f"Using {global_overlay} as global overlay")
    GLOBAL_OVERLAY_IM = Image.open(f"{global_overlay}")
    GLOBAL_OVERLAY_IM = GLOBAL_OVERLAY_IM.resize((2000, 3000), Image.Resampling.LANCZOS)

def skip_this(tgt_path):
    """ Skip files that we don't want to overlay """
    ret_val = False
    ret_val = ret_val or '.git' in tgt_path.parts
    ret_val = ret_val or '.github' in tgt_path.parts
    ret_val = ret_val or '.gitignore' in tgt_path.parts

    ret_val = ret_val or 'overlays' in tgt_path.parts
    ret_val = ret_val or 'logos' in tgt_path.parts

    ret_val = ret_val or '.ttf' in tgt_path.suffixes
    ret_val = ret_val or '.psd' in tgt_path.suffixes
    ret_val = ret_val or '.xcf' in tgt_path.suffixes
    ret_val = ret_val or '.md' in tgt_path.suffixes
    ret_val = ret_val or '.txt' in tgt_path.suffixes

    ret_val = ret_val or tgt_path.is_dir()

    ret_val = ret_val or '!_' in tgt_path.stem
    ret_val = ret_val or tgt_path.stem == 'overlay'

    return ret_val

target_paths = []

print("building list of targets")
for path in pathlib.Path(LOCAL_FOLDER).glob('**/*'):
    if not skip_this(path):
        target_paths.append(path)

ITEM_TOTAL = len(target_paths)

with alive_bar(ITEM_TOTAL, dual_line=True, title='Applying overlays') as bar:
    for path in target_paths:
        bar.text(path)

        source_path = Path(path)
        target_path = Path(f"{path}".replace(LOCAL_FOLDER, OVERLAID_FOLDER))
        target_path.parent.mkdir(parents=True, exist_ok=True)

        target_group = path.parts[1]

        try:
            LOCAL_OVERLAY = f"{OVERLAY_SOURCE_FOLDER}/{target_group}.png"
            local_overlay_im = Image.open(LOCAL_OVERLAY)
            local_overlay_im = local_overlay_im.resize((2000, 3000), Image.Resampling.LANCZOS)
        except: # pylint: disable=bare-except
            local_overlay_im = GLOBAL_OVERLAY_IM

        source_image = Image.open(source_path)

        source_image.paste(local_overlay_im, (0,0), local_overlay_im)
        source_image.save(target_path)

        bar() # pylint: disable=not-callable
