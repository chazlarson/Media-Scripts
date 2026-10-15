import os
import math
import string
import time
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from plexapi.server import PlexServer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# module‑level alphabet list so we only build it once
ALPHABET = list(string.ascii_uppercase)
ALPHABET.insert(0, "0-9")

# cache of non-empty asset folders, split between poster files and background
# files, per media type. Scanning this means checking every item's folder on
# disk, which is the expensive part of this app — unlike before, this is now
# PURELY MANUAL: it is never recomputed automatically on a page view or after
# a timeout. It is only (re)computed when the "🔄 Vérifier les posters" button
# is used, or right after a download (a single, cheap, known-fresh update).
# computed_at stays None until the first manual check ever happens.
_ASSET_CACHE = {
    "movie_posters": set(),
    "movie_backgrounds": set(),
    "series_posters": set(),
    "series_backgrounds": set(),
    "computed_at": None,
}


def _scan_asset_folders(root):
    """Scan `root` (assets/movies or assets/series) and return two sets of
    folder names: those containing a poster.* file, and those containing a
    background.* file, directly inside them (files are flat, no subfolders)."""
    posters = set()
    backgrounds = set()
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                try:
                    with os.scandir(entry.path) as files:
                        for f in files:
                            if not f.is_file():
                                continue
                            name = f.name.lower()
                            if name.startswith("poster"):
                                posters.add(entry.name)
                            elif name.startswith("background"):
                                backgrounds.add(entry.name)
                except (FileNotFoundError, PermissionError):
                    pass
    except (FileNotFoundError, PermissionError):
        pass
    return posters, backgrounds


def get_asset_folders(asset_root, force=False):
    """Return the cached scan. Never scans on its own — pass force=True to
    actually (re)do the disk scan (used by the manual refresh button and
    right after a download)."""
    if force:
        _ASSET_CACHE["movie_posters"], _ASSET_CACHE["movie_backgrounds"] = _scan_asset_folders(
            os.path.join(asset_root, "movies")
        )
        _ASSET_CACHE["series_posters"], _ASSET_CACHE["series_backgrounds"] = _scan_asset_folders(
            os.path.join(asset_root, "series")
        )
        _ASSET_CACHE["computed_at"] = time.time()
    return _ASSET_CACHE


def annotate_asset_flags(items):
    """Set item.has_poster / item.has_background for each item in the list,
    from the cached scan. If no manual check has ever been run yet, both are
    set to None (meaning "unknown / not checked"), never guessed as False."""
    asset_root = os.path.join(os.getcwd(), session.get("asset_dir", "assets"))
    cache = get_asset_folders(asset_root)  # force=False: just reads, never scans
    checked = cache["computed_at"] is not None
    for item in items:
        if not checked:
            item.has_poster = None
            item.has_background = None
            continue
        try:
            if item.type == "movie":
                media_file = item.media[0].parts[0].file
                asset_name = os.path.basename(os.path.dirname(media_file))
                item.has_poster = asset_name in cache["movie_posters"]
                item.has_background = asset_name in cache["movie_backgrounds"]
            else:
                asset_name = os.path.basename(item.locations[0])
                item.has_poster = asset_name in cache["series_posters"]
                item.has_background = asset_name in cache["series_backgrounds"]
        except Exception:
            item.has_poster = False
            item.has_background = False
    return items


# cache of {section_key: {"keys": [ratingKey, ...], "scanned_at": ...}} — the
# ordered list of items missing a poster, for the "missing only" nav mode.
# Only rebuilt when it's older than the last manual asset check (i.e. right
# after the button is used, or after a download), never on a timer.
_MISSING_CACHE = {}


def get_missing_rating_keys(section, force=False):
    if _ASSET_CACHE["computed_at"] is None:
        return None  # nothing has ever been checked — caller must handle this
    key = str(section.key)
    entry = _MISSING_CACHE.get(key)
    if force or not entry or entry["scanned_at"] < _ASSET_CACHE["computed_at"]:
        items = list(section.all())
        annotate_asset_flags(items)
        entry = {
            "keys": [i.ratingKey for i in items if not i.has_poster],
            "scanned_at": time.time(),
        }
        _MISSING_CACHE[key] = entry
    return entry["keys"]


def refresh_asset_check(plex, section_key=None):
    """Run a full manual check: rescan the asset folders on disk, then rebuild
    the missing-poster list for the given section (or all known sections)."""
    asset_root = os.path.join(os.getcwd(), session.get("asset_dir", "assets"))
    get_asset_folders(asset_root, force=True)
    if section_key:
        section = next(
            (s for s in plex.library.sections() if str(s.key) == section_key), None
        )
        if section:
            get_missing_rating_keys(section, force=True)


def get_plex():
    base_url = session.get("base_url")
    token = session.get("token")
    if not base_url or not token:
        return None
    return PlexServer(base_url, token)


@app.route("/", methods=["GET", "POST"])
def connect():
    if request.method == "POST":
        session["base_url"] = request.form["base_url"]
        session["token"] = request.form["token"]
        session["asset_dir"] = (
            "assets" if not request.form["asset_dir"] else request.form["asset_dir"]
        )
        return redirect(url_for("libraries"))

    # optional defaults from environment variables (set in docker-compose.yml)
    env_base_url = os.environ.get("PLEX_BASE_URL", "")
    env_token = os.environ.get("PLEX_TOKEN", "")
    env_asset_dir = os.environ.get("PLEX_ASSET_DIR", "assets")

    # if both URL and token are provided via env, skip the form entirely
    if env_base_url and env_token and not session.get("base_url"):
        session["base_url"] = env_base_url
        session["token"] = env_token
        session["asset_dir"] = env_asset_dir
        return redirect(url_for("libraries"))

    return render_template(
        "connect.html",
        default_base_url=env_base_url,
        default_token=env_token,
        default_asset_dir=env_asset_dir,
    )


@app.route("/libraries")
def libraries():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))
    sections = sorted(plex.library.sections(), key=lambda s: s.title.lower())
    return render_template("libraries.html", sections=sections)


# new paginated item picker
@app.route("/browse/<section_key>/items")
def list_items(section_key):
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    # find the right library section
    section = next(
        (s for s in plex.library.sections() if str(s.key) == section_key),
        None,
    )
    if not section:
        flash("Library not found.")
        return redirect(url_for("libraries"))

    # full list of items
    all_items_full = list(section.all())

    # give everything a global index
    global_index = 1
    for item in all_items_full:
        item.global_index = global_index
        global_index = global_index + 1

    # check which items already have a downloaded poster / background —
    # purely from the last manual check, never scans the disk itself
    annotate_asset_flags(all_items_full)
    checked = _ASSET_CACHE["computed_at"] is not None

    # separate index used when navigating within the "missing poster only" set,
    # so Next/Previous on the item page stay within that filtered subset instead
    # of jumping around based on the full library's positions
    missing_index = 1
    for item in all_items_full:
        if checked and not item.has_poster:
            item.missing_index = missing_index
            missing_index += 1
        else:
            item.missing_index = None

    # optional free-text search — takes priority over the alphabet filter
    search_query = request.args.get("q", "").strip()
    letter = request.args.get("letter", "All")
    if search_query:
        letter = "All"
        items_filtered = [
            item
            for item in all_items_full
            if item.title and search_query.lower() in item.title.lower()
        ]
    elif letter != "All":
        if letter[:1].isdigit():
            items_filtered = [
                item
                for item in all_items_full
                if item.title and item.title[:1].isdigit()
            ]
        else:
            items_filtered = [
                item
                for item in all_items_full
                if item.title and item.title.upper().startswith(letter.upper())
            ]
    else:
        items_filtered = all_items_full

    # optional "missing poster only" filter — meaningless before a check has
    # ever been run, so it's simply ignored until then
    missing_only = checked and request.args.get("missing_only") == "1"
    if missing_only:
        items_filtered = [item for item in items_filtered if not item.has_poster]

    # pagination params (based on filtered set)
    total    = len(items_filtered)
    per_page = 20
    pages    = math.ceil(total / per_page) if total else 1

    # clamp page number
    page = int(request.args.get("page", 1))
    page = max(1, min(page, pages))

    # slice out this page from filtered items
    start      = (page - 1) * per_page
    page_items = items_filtered[start : start + per_page]

    return render_template(
        "items.html",
        section=section,
        checked=checked,
        items=page_items,
        page=page,
        pages=pages,
        per_page=per_page,
        alphabet=ALPHABET,
        letter=letter,
        search_query=search_query,
        missing_only=missing_only,
        missing_count=(len([i for i in all_items_full if not i.has_poster]) if checked else 0),
    )


@app.route("/refresh_assets/<section_key>")
def refresh_assets(section_key):
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    refresh_asset_check(plex, section_key)
    flash("Vérification des posters/backgrounds effectuée.")

    # bounce back to wherever the person was (list or item page), keeping
    # whatever letter/search/page/missing_only state was already in the URL
    return_to = request.args.get("return_to", "list")
    if return_to == "item":
        return redirect(
            url_for(
                "browse",
                section_key=section_key,
                page=request.args.get("page", 1),
                letter=request.args.get("letter", "All"),
                art_type=request.args.get("art_type", "poster"),
                season=request.args.get("season"),
                episode=request.args.get("episode"),
                art_page=request.args.get("art_page", 1),
                missing_only=request.args.get("missing_only"),
            )
        )
    return redirect(
        url_for(
            "list_items",
            section_key=section_key,
            page=request.args.get("page", 1),
            letter=request.args.get("letter", "All"),
            q=request.args.get("q") or None,
            missing_only=request.args.get("missing_only"),
        )
    )


@app.route("/browse/<section_key>")
def browse(section_key):
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))
    section = next(
        (s for s in plex.library.sections() if str(s.key) == section_key), None
    )
    if not section:
        flash("Library not found.")
        return redirect(url_for("libraries"))
    missing_only = request.args.get("missing_only") == "1"
    if missing_only:
        missing_keys = get_missing_rating_keys(section)
        if missing_keys is None:
            flash("Lance d'abord une vérification des posters avant d'utiliser ce filtre.")
            return redirect(url_for("list_items", section_key=section.key))
        pages = len(missing_keys)
        if not pages:
            flash("Tous les items ont déjà un poster \u2014 filtre \u00absans poster\u00bb retiré.")
            return redirect(
                url_for("list_items", section_key=section.key, missing_only=1)
            )
        item_page = int(request.args.get("page", 1))
        item_letter = request.args.get("letter", "All")
        item_page = max(1, min(item_page, pages))
        item = plex.fetchItem(missing_keys[item_page - 1])
    else:
        items = list(section.all())
        pages = len(items)
        item_page = int(request.args.get("page", 1))
        item_letter = request.args.get("letter", "All")
        item_page = max(1, min(item_page, pages))
        item = items[item_page - 1]

    art_type = request.args.get("art_type", "poster")
    season = request.args.get("season")
    try:
        season_rating_key = item.season(int(season)).ratingKey
    except:
        season_rating_key = None

    episode = request.args.get("episode")
    art_page = int(request.args.get("art_page", 1))

    # check if a local asset already exists for this item (pending a Kometa run)
    try:
        if item.type == "movie":
            media_file = item.media[0].parts[0].file
            asset_name = os.path.basename(os.path.dirname(media_file))
        else:
            asset_name = os.path.basename(item.locations[0])
        subfolder = "movies" if item.type == "movie" else "series"
        asset_root = os.path.join(os.getcwd(), session.get("asset_dir", "assets"))
        item_dir = os.path.join(asset_root, subfolder, asset_name)
        has_local_asset = os.path.isdir(item_dir) and any(os.scandir(item_dir))
    except Exception:
        has_local_asset = False

    # direct link to this item's page in the Plex web app
    try:
        plex_web_url = (
            f"{session['base_url']}/web/index.html#!/server/"
            f"{plex.machineIdentifier}/details?key=%2Flibrary%2Fmetadata%2F{item.ratingKey}"
        )
    except Exception:
        plex_web_url = None

    # IMDb link, if Plex has an IMDb guid for this item
    imdb_url = None
    try:
        for guid in item.guids:
            if guid.id.startswith("imdb://"):
                imdb_url = f"https://www.imdb.com/title/{guid.id.replace('imdb://', '')}/"
                break
    except Exception:
        pass

    return render_template(
        "item.html",
        section=section,
        item=item,
        season_rating_key=season_rating_key,
        item_page=item_page,
        item_letter=item_letter,
        pages=pages,
        art_type=art_type,
        season=season,
        episode=episode,
        art_page=art_page,
        missing_only=missing_only,
        has_local_asset=has_local_asset,
        plex_web_url=plex_web_url,
        imdb_url=imdb_url,
    )


def compute_asset_base_dir(item, season_item):
    try:
        asset_name = None
        if item.type == "movie":
            media_file = item.media[0].parts[0].file
        elif item.type == "show" or season_item:
            media_file = item.locations[0]
            asset_name = os.path.basename(media_file)
        elif item.type == "episode":
            media_file = item.media[0].parts[0].file
        else:
            media_file = None
        if not asset_name:
            asset_name = os.path.basename(os.path.dirname(media_file))
    except Exception:
        asset_name = item.title

    return os.path.join(
        os.getcwd(),
        session["asset_dir"],
        "movies" if item.type == "movie" else "series",
        asset_name,
    )


def compute_asset_filename(item, art_type, season, episode, ext):
    if item.type == "show":
        if episode:
            s, e = int(season), int(episode)
            name = f"S{s:02d}E{e:02d}"
        elif season:
            s = int(season)
            name = f"Season {s:02d}"
        else:
            name = art_type
        suffix = (
            f"_{art_type}" if art_type == "background" and (season or episode) else ""
        )
        return f"{name}{suffix}{ext}"
    return f"{art_type}{ext}"


def get_download_context(form):
    """Shared form fields used by /download, /upload_url and /upload_file."""
    rating_key = int(form["rating_key"])
    try:
        season_rating_key = int(form["season_rating_key"])
    except:
        season_rating_key = None
    return {
        "rating_key": rating_key,
        "season_rating_key": season_rating_key,
        "section_key": form["section_key"],
        "art_type": form["art_type"],
        "season": None if form.get("season") == "None" else form.get("season"),
        "episode": None if form.get("episode") == "None" else form.get("episode"),
        "item_page": form.get("item_page", 1),
        "art_page": form.get("art_page", 1),
        "missing_only": form.get("missing_only") == "1",
    }


@app.route("/download", methods=["POST"])
def download():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    ctx = get_download_context(request.form)
    img_key = request.form["img_key"]

    item = plex.fetchItem(ctx["rating_key"])
    season_item = (
        None if not ctx["season_rating_key"] else plex.fetchItem(ctx["season_rating_key"])
    )

    base_dir = compute_asset_base_dir(item, season_item)
    os.makedirs(base_dir, exist_ok=True)

    ext = os.path.splitext(img_key)[1] or ".jpg"
    filename = compute_asset_filename(item, ctx["art_type"], ctx["season"], ctx["episode"], ext)

    if img_key.startswith("http"):
        img_url = img_key
    else:
        img_url = f"{session['base_url']}{img_key}&X-Plex-Token={session['token']}"

    resp = requests.get(img_url)
    with open(os.path.join(base_dir, filename), "wb") as f:
        f.write(resp.content)

    # a new file just landed on disk — refresh the cached "has poster" sets right
    # away instead of waiting for the TTL, so the badge is correct immediately
    get_asset_folders(
        os.path.join(os.getcwd(), session.get("asset_dir", "assets")), force=True
    )
    if _ASSET_CACHE["computed_at"] is not None:
        refresh_asset_check(plex, ctx["section_key"])

    flash(f"Saved to {os.path.join(base_dir, filename)}")
    return redirect(
        url_for(
            "browse",
            section_key=ctx["section_key"],
            page=ctx["item_page"],
            art_type=ctx["art_type"],
            season=ctx["season"],
            episode=ctx["episode"],
            art_page=ctx["art_page"],
            missing_only=1 if ctx["missing_only"] else None,
        )
    )


@app.route("/upload_url", methods=["POST"])
def upload_url():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    ctx = get_download_context(request.form)
    image_url = request.form.get("image_url", "").strip()

    if not image_url:
        flash("Aucune URL fournie.")
        return redirect(
            url_for(
                "browse",
                section_key=ctx["section_key"],
                page=ctx["item_page"],
                art_type=ctx["art_type"],
                season=ctx["season"],
                episode=ctx["episode"],
                art_page=ctx["art_page"],
            missing_only=1 if ctx["missing_only"] else None,
            )
        )

    item = plex.fetchItem(ctx["rating_key"])
    season_item = (
        None if not ctx["season_rating_key"] else plex.fetchItem(ctx["season_rating_key"])
    )

    base_dir = compute_asset_base_dir(item, season_item)
    os.makedirs(base_dir, exist_ok=True)

    ext = os.path.splitext(image_url.split("?")[0])[1] or ".jpg"
    filename = compute_asset_filename(item, ctx["art_type"], ctx["season"], ctx["episode"], ext)

    try:
        resp = requests.get(image_url, timeout=15)
        resp.raise_for_status()
        with open(os.path.join(base_dir, filename), "wb") as f:
            f.write(resp.content)
        get_asset_folders(
            os.path.join(os.getcwd(), session.get("asset_dir", "assets")), force=True
        )
        if _ASSET_CACHE["computed_at"] is not None:
            refresh_asset_check(plex, ctx["section_key"])
        flash(f"Saved to {os.path.join(base_dir, filename)}")
    except Exception as e:
        flash(f"Échec du téléchargement depuis l'URL : {e}")

    return redirect(
        url_for(
            "browse",
            section_key=ctx["section_key"],
            page=ctx["item_page"],
            art_type=ctx["art_type"],
            season=ctx["season"],
            episode=ctx["episode"],
            art_page=ctx["art_page"],
            missing_only=1 if ctx["missing_only"] else None,
        )
    )


@app.route("/upload_file", methods=["POST"])
def upload_file():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    ctx = get_download_context(request.form)
    uploaded = request.files.get("image_file")

    if not uploaded or uploaded.filename == "":
        flash("Aucun fichier sélectionné.")
        return redirect(
            url_for(
                "browse",
                section_key=ctx["section_key"],
                page=ctx["item_page"],
                art_type=ctx["art_type"],
                season=ctx["season"],
                episode=ctx["episode"],
                art_page=ctx["art_page"],
            missing_only=1 if ctx["missing_only"] else None,
            )
        )

    item = plex.fetchItem(ctx["rating_key"])
    season_item = (
        None if not ctx["season_rating_key"] else plex.fetchItem(ctx["season_rating_key"])
    )

    base_dir = compute_asset_base_dir(item, season_item)
    os.makedirs(base_dir, exist_ok=True)

    ext = os.path.splitext(uploaded.filename)[1] or ".jpg"
    filename = compute_asset_filename(item, ctx["art_type"], ctx["season"], ctx["episode"], ext)

    uploaded.save(os.path.join(base_dir, filename))

    get_asset_folders(
        os.path.join(os.getcwd(), session.get("asset_dir", "assets")), force=True
    )
    if _ASSET_CACHE["computed_at"] is not None:
        refresh_asset_check(plex, ctx["section_key"])
    flash(f"Saved to {os.path.join(base_dir, filename)}")

    return redirect(
        url_for(
            "browse",
            section_key=ctx["section_key"],
            page=ctx["item_page"],
            art_type=ctx["art_type"],
            season=ctx["season"],
            episode=ctx["episode"],
            art_page=ctx["art_page"],
            missing_only=1 if ctx["missing_only"] else None,
        )
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)