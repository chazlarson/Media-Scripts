from alive_progress import alive_bar
import pathlib
from pathlib import Path
from git.repo.base import Repo
from PIL import Image

IMAGE_REPO = "https://github.com/Kometa-Team/Default-Images"
LOCAL_FOLDER = "Kometa-Images"
OVERLAID_FOLDER = "Kometa-Images-Overlaid"
OVERLAY_SOURCE_FOLDER = "default_collection_overlays"
OVERLAY_BASE_IMAGE = "overlay-template.png"

theRepo = None
theRepoPath = Path(LOCAL_FOLDER)
theTargetPath = Path(OVERLAID_FOLDER)

if not theRepoPath.exists():
    print(f"Cloning {IMAGE_REPO}")
    print("This may take some time with no display")
    theRepo = Repo.clone_from(IMAGE_REPO, LOCAL_FOLDER)
else:
    print(f"Fetch/Pull on {LOCAL_FOLDER}")
    theRepo = Repo(LOCAL_FOLDER)
    theRepo.remotes.origin.fetch()
    theRepo.remotes.origin.pull()

global_overlay = Path(f"{OVERLAY_SOURCE_FOLDER}/{OVERLAY_BASE_IMAGE}")
global_overlay_im = None

if global_overlay.exists():
    print(f"Using {global_overlay} as global overlay")
    global_overlay_im = Image.open(f"{global_overlay}")
    global_overlay_im = global_overlay_im.resize((2000, 3000), Image.Resampling.LANCZOS)


def skip_this(path):
    ret_val = False
    ret_val = ret_val or ".git" in path.parts
    ret_val = ret_val or ".github" in path.parts
    ret_val = ret_val or ".gitignore" in path.parts

    ret_val = ret_val or "overlays" in path.parts
    ret_val = ret_val or "logos" in path.parts

    ret_val = ret_val or ".ttf" in path.suffixes
    ret_val = ret_val or ".psd" in path.suffixes
    ret_val = ret_val or ".xcf" in path.suffixes
    ret_val = ret_val or ".md" in path.suffixes
    ret_val = ret_val or ".txt" in path.suffixes

    ret_val = ret_val or path.is_dir()

    ret_val = ret_val or "!_" in path.stem
    ret_val = ret_val or path.stem == "overlay"

    return ret_val


target_paths = []

print("building list of targets")
for path in pathlib.Path(LOCAL_FOLDER).glob("**/*"):
    if not skip_this(path):
        target_paths.append(path)

item_total = len(target_paths)

with alive_bar(item_total, dual_line=True, title="Applying overlays") as bar:
    for path in target_paths:
        bar.text(path)

        source_path = Path(path)
        target_path = Path(f"{path}".replace(LOCAL_FOLDER, OVERLAID_FOLDER))
        target_path.parent.mkdir(parents=True, exist_ok=True)

        target_group = path.parts[1]

        try:
            local_overlay = f"{OVERLAY_SOURCE_FOLDER}/{target_group}.png"
            local_overlay_im = Image.open(local_overlay)
            local_overlay_im = local_overlay_im.resize(
                (2000, 3000), Image.Resampling.LANCZOS
            )
        except:
            local_overlay_im = global_overlay_im

        source_image = Image.open(source_path)

        source_image.paste(local_overlay_im, (0, 0), local_overlay_im)
        source_image.save(target_path)

        bar()
