import pathlib
from pathlib import Path

from alive_progress import alive_bar
from git.repo.base import Repo
from PIL import Image

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


def main():
    image_repo = "https://github.com/Kometa-Team/Default-Images"
    local_folder = "Kometa-Images"
    overlaid_folder = "Kometa-Images-Overlaid"
    overlay_source_folder = "default_collection_overlays"
    overlay_base_image = "overlay-template.png"

    the_repo_path = Path(local_folder)

    if not the_repo_path.exists():
        print(f"Cloning {image_repo}")
        print("This may take some time with no display")
        Repo.clone_from(image_repo, local_folder)
    else:
        print(f"Fetch/Pull on {local_folder}")
        the_repo = Repo(local_folder)
        the_repo.remotes.origin.fetch()
        the_repo.remotes.origin.pull()

    global_overlay = Path(f"{overlay_source_folder}/{overlay_base_image}")
    global_overlay_im = None

    if global_overlay.exists():
        print(f"Using {global_overlay} as global overlay")
        global_overlay_im = Image.open(f"{global_overlay}")
        global_overlay_im = global_overlay_im.resize((2000, 3000), Image.Resampling.LANCZOS)

    target_paths = []

    print("building list of targets")
    for path in pathlib.Path(local_folder).glob("**/*"):
        if not skip_this(path):
            target_paths.append(path)

    item_total = len(target_paths)

    with alive_bar(item_total, dual_line=True, title="Applying overlays") as bar:
        for path in target_paths:
            bar.text(path)

            source_path = Path(path)
            target_path = Path(f"{path}".replace(local_folder, overlaid_folder))
            target_path.parent.mkdir(parents=True, exist_ok=True)

            target_group = path.parts[1]

            try:
                local_overlay = f"{overlay_source_folder}/{target_group}.png"
                local_overlay_im = Image.open(local_overlay)
                local_overlay_im = local_overlay_im.resize(
                    (2000, 3000), Image.Resampling.LANCZOS
                )
            except Exception:
                local_overlay_im = global_overlay_im

            source_image = Image.open(source_path)

            source_image.paste(local_overlay_im, (0, 0), local_overlay_im)
            source_image.save(target_path)

            bar()


if __name__ == "__main__":
    main()
