import ipaddress
import math
import os
import socket
import string
import time
from urllib.parse import urlparse

import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from plexapi.server import PlexServer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# module‑level alphabet list so we only build it once
ALPHABET = list(string.ascii_uppercase)
ALPHABET.insert(0, "0-9")

# Max bytes accepted for any server-side image fetch (URL upload or remote poster).
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_IMAGE_SCHEMES = {"http", "https"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}

# Per-(plex server, asset root) caches of non-empty asset folders, split between
# poster files and background files, per media type. Scanning this means
# checking every item's folder on disk, which is the expensive part of this
# app — unlike before, this is now PURELY MANUAL: it is never recomputed
# automatically on a page view or after a timeout. It is only (re)computed when
# the "Refresh posters/backgrounds" button is used, or right after a download
# (a single, cheap, known-fresh update). Each entry's computed_at stays None
# until the first manual check for that key.
_ASSET_CACHES = {}

# cache of {cache_key: {section_key: {"keys": [...], "scanned_at": ...}}} —
# ordered lists of items missing a poster, for the "missing only" nav mode.
# Only rebuilt when older than the last manual asset check for that key.
_MISSING_CACHES = {}


def _empty_asset_cache():
    return {
        "movie_posters": set(),
        "movie_backgrounds": set(),
        "series_posters": set(),
        "series_backgrounds": set(),
        "computed_at": None,
        "asset_root": None,
        "base_url": None,
    }


def sanitize_asset_dir(raw):
    """Normalize a user-supplied asset directory name/path.

    Relative paths must resolve under the process cwd (blocks ``..`` escapes).
    Absolute paths are allowed (Docker volume mounts) after realpath.
    """
    raw = (raw or "assets").strip() or "assets"
    if "\x00" in raw:
        return "assets"
    if os.path.isabs(raw):
        return os.path.realpath(raw)
    candidate = os.path.realpath(os.path.join(os.getcwd(), raw))
    cwd = os.path.realpath(os.getcwd())
    if candidate != cwd and not candidate.startswith(cwd + os.sep):
        return "assets"
    # Keep a relative form when possible so joins with cwd stay stable.
    try:
        return os.path.relpath(candidate, cwd)
    except ValueError:
        return candidate


def resolve_asset_root(asset_dir=None):
    """Absolute path of the asset tree for the current session (or override)."""
    raw = asset_dir if asset_dir is not None else session.get("asset_dir", "assets")
    raw = (raw or "assets").strip() or "assets"
    if os.path.isabs(raw):
        return os.path.realpath(raw)
    return os.path.realpath(os.path.join(os.getcwd(), raw))


def _session_cache_key(asset_root=None, base_url=None):
    """Key asset / missing caches by Plex server + asset tree."""
    root = os.path.realpath(asset_root or resolve_asset_root())
    url = (base_url if base_url is not None else session.get("base_url") or "").rstrip(
        "/"
    )
    return f"{url}|{root}"


def _is_blocked_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_outbound_image_url(url):
    """Reject non-http(s) URLs and hosts that resolve to private/local addresses.

    Raises ValueError when the URL must not be fetched server-side.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_IMAGE_SCHEMES:
        raise ValueError("Only http and https image URLs are allowed")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")
    # Block literal private IPs before DNS.
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass  # hostname is not an IP literal
    else:
        if _is_blocked_ip(hostname):
            raise ValueError("URL host is a private or local address")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        addrinfos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve host: {exc}") from exc
    if not addrinfos:
        raise ValueError("Cannot resolve host")
    for info in addrinfos:
        if _is_blocked_ip(info[4][0]):
            raise ValueError("URL resolves to a private or local address")
    return url


def _read_response_bounded(resp):
    content_length = resp.headers.get("Content-Length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_DOWNLOAD_BYTES:
                raise ValueError("Remote file exceeds size limit")
        except ValueError as exc:
            if "size limit" in str(exc):
                raise
            # Non-numeric Content-Length — ignore and enforce while reading.
    chunks = []
    total = 0
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_DOWNLOAD_BYTES:
            raise ValueError("Remote file exceeds size limit")
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_image_bytes(url, timeout=15):
    """Fetch an arbitrary image URL with SSRF checks and a hard size cap."""
    validate_outbound_image_url(url)
    with requests.get(url, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        return _read_response_bounded(resp)


def fetch_plex_media(img_key, timeout=15):
    """Fetch a relative Plex media path from the session's configured server.

    Plex is often on a LAN address, so this path intentionally skips the
    private-IP SSRF block used for arbitrary URL uploads. The request is still
    size-bounded and locked to the session base_url host.
    """
    if not img_key.startswith("/"):
        raise ValueError("Plex media path must start with /")
    base = (session.get("base_url") or "").rstrip("/")
    token = session.get("token") or ""
    if not base or not token:
        raise ValueError("Plex connection is not configured")
    url = f"{base}{img_key}"
    sep = "&" if "?" in url else "?"
    if "X-Plex-Token=" not in url:
        url = f"{url}{sep}X-Plex-Token={token}"

    parsed = urlparse(url)
    base_parsed = urlparse(base)
    if (
        parsed.scheme != base_parsed.scheme
        or parsed.hostname != base_parsed.hostname
        or parsed.port != base_parsed.port
    ):
        raise ValueError("Refusing to fetch outside the configured Plex server")

    with requests.get(url, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        return _read_response_bounded(resp)


def safe_image_ext(path_or_url):
    """Return a safe image extension from a path/URL, defaulting to .jpg."""
    path = path_or_url.split("?", 1)[0]
    ext = os.path.splitext(path)[1].lower()
    if ext in ALLOWED_IMAGE_EXTS:
        return ext
    return ".jpg"


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


def get_asset_folders(asset_root=None, force=False):
    """Return the cached scan for this session's Plex server + asset root.

    Never scans on its own — pass force=True to actually (re)do the disk scan
    (used by the manual refresh button and right after a download).
    """
    root = os.path.realpath(asset_root or resolve_asset_root())
    key = _session_cache_key(root)
    cache = _ASSET_CACHES.setdefault(key, _empty_asset_cache())
    if force:
        cache["movie_posters"], cache["movie_backgrounds"] = _scan_asset_folders(
            os.path.join(root, "movies")
        )
        cache["series_posters"], cache["series_backgrounds"] = _scan_asset_folders(
            os.path.join(root, "series")
        )
        cache["computed_at"] = time.time()
        cache["asset_root"] = root
        cache["base_url"] = (session.get("base_url") or "").rstrip("/")
    return cache


def annotate_asset_flags(items):
    """Set item.has_poster / item.has_background for each item in the list,
    from the cached scan. If no manual check has ever been run yet for this
    session key, both are set to None (meaning "unknown / not checked"),
    never guessed as False."""
    asset_root = resolve_asset_root()
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


def get_missing_rating_keys(section, force=False):
    asset_root = resolve_asset_root()
    cache_key = _session_cache_key(asset_root)
    asset_cache = get_asset_folders(asset_root)
    if asset_cache["computed_at"] is None:
        return None  # nothing has ever been checked — caller must handle this
    section_map = _MISSING_CACHES.setdefault(cache_key, {})
    key = str(section.key)
    entry = section_map.get(key)
    if force or not entry or entry["scanned_at"] < asset_cache["computed_at"]:
        items = list(section.all())
        annotate_asset_flags(items)
        entry = {
            "keys": [i.ratingKey for i in items if not i.has_poster],
            "scanned_at": time.time(),
        }
        section_map[key] = entry
    return entry["keys"]


def refresh_asset_check(plex, section_key=None):
    """Run a full manual check: rescan the asset folders on disk, then rebuild
    the missing-poster list for the given section (or all known sections)."""
    asset_root = resolve_asset_root()
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


def _browse_redirect(ctx, flash_message=None):
    if flash_message:
        flash(flash_message)
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


@app.route("/", methods=["GET", "POST"])
def connect():
    if request.method == "POST":
        session["base_url"] = request.form["base_url"]
        session["token"] = request.form["token"]
        session["asset_dir"] = sanitize_asset_dir(request.form.get("asset_dir"))
        return redirect(url_for("libraries"))

    # optional defaults from environment variables (set in docker-compose.yml)
    env_base_url = os.environ.get("PLEX_BASE_URL", "")
    env_token = os.environ.get("PLEX_TOKEN", "")
    env_asset_dir = sanitize_asset_dir(os.environ.get("PLEX_ASSET_DIR", "assets"))

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
    checked = get_asset_folders()["computed_at"] is not None

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
    total = len(items_filtered)
    per_page = 20
    pages = math.ceil(total / per_page) if total else 1

    # clamp page number
    page = int(request.args.get("page", 1))
    page = max(1, min(page, pages))

    # slice out this page from filtered items
    start = (page - 1) * per_page
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
        missing_count=(
            len([i for i in all_items_full if not i.has_poster]) if checked else 0
        ),
    )


@app.route("/refresh_assets/<section_key>")
def refresh_assets(section_key):
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    refresh_asset_check(plex, section_key)
    flash("Poster/background check complete.")

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
            flash("Run a poster check first before using this filter.")
            return redirect(url_for("list_items", section_key=section.key))
        pages = len(missing_keys)
        if not pages:
            flash('Every item already has a poster — "missing poster" filter cleared.')
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
    except Exception:
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
        asset_root = resolve_asset_root()
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
                imdb_url = (
                    f"https://www.imdb.com/title/{guid.id.replace('imdb://', '')}/"
                )
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

    # Basename-only: drop any path separators that could escape the asset tree.
    asset_name = os.path.basename(str(asset_name).replace("\\", "/")) or "unknown"

    base = os.path.join(
        resolve_asset_root(),
        "movies" if item.type == "movie" else "series",
        asset_name,
    )
    # Final guard: resolved path must stay under the asset root.
    asset_root = resolve_asset_root()
    real_base = os.path.realpath(base)
    if not real_base.startswith(asset_root + os.sep) and real_base != asset_root:
        real_base = os.path.join(asset_root, "movies" if item.type == "movie" else "series", "unknown")
    return real_base


def compute_asset_filename(item, art_type, season, episode, ext):
    ext = safe_image_ext(ext if ext.startswith(".") else f".{ext}")
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
    except Exception:
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


def _mark_asset_fresh(plex, section_key):
    get_asset_folders(force=True)
    if get_asset_folders()["computed_at"] is not None:
        refresh_asset_check(plex, section_key)


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

    ext = safe_image_ext(img_key)
    filename = compute_asset_filename(
        item, ctx["art_type"], ctx["season"], ctx["episode"], ext
    )

    try:
        if img_key.startswith("http://") or img_key.startswith("https://"):
            content = fetch_image_bytes(img_key)
        elif img_key.startswith("/"):
            content = fetch_plex_media(img_key)
        else:
            raise ValueError("Unsupported image key")
    except Exception as exc:
        return _browse_redirect(ctx, f"Download failed: {exc}")

    with open(os.path.join(base_dir, filename), "wb") as f:
        f.write(content)

    # a new file just landed on disk — refresh the cached "has poster" sets
    _mark_asset_fresh(plex, ctx["section_key"])

    return _browse_redirect(ctx, f"Saved to {os.path.join(base_dir, filename)}")


@app.route("/upload_url", methods=["POST"])
def upload_url():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    ctx = get_download_context(request.form)
    image_url = request.form.get("image_url", "").strip()

    if not image_url:
        return _browse_redirect(ctx, "No URL provided.")

    item = plex.fetchItem(ctx["rating_key"])
    season_item = (
        None if not ctx["season_rating_key"] else plex.fetchItem(ctx["season_rating_key"])
    )

    base_dir = compute_asset_base_dir(item, season_item)
    os.makedirs(base_dir, exist_ok=True)

    ext = safe_image_ext(image_url)
    filename = compute_asset_filename(
        item, ctx["art_type"], ctx["season"], ctx["episode"], ext
    )

    try:
        content = fetch_image_bytes(image_url)
        with open(os.path.join(base_dir, filename), "wb") as f:
            f.write(content)
        _mark_asset_fresh(plex, ctx["section_key"])
        return _browse_redirect(ctx, f"Saved to {os.path.join(base_dir, filename)}")
    except Exception as exc:
        return _browse_redirect(ctx, f"Failed to download from URL: {exc}")


@app.route("/upload_file", methods=["POST"])
def upload_file():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    ctx = get_download_context(request.form)
    uploaded = request.files.get("image_file")

    if not uploaded or uploaded.filename == "":
        return _browse_redirect(ctx, "No file selected.")

    item = plex.fetchItem(ctx["rating_key"])
    season_item = (
        None if not ctx["season_rating_key"] else plex.fetchItem(ctx["season_rating_key"])
    )

    base_dir = compute_asset_base_dir(item, season_item)
    os.makedirs(base_dir, exist_ok=True)

    ext = safe_image_ext(uploaded.filename)
    filename = compute_asset_filename(
        item, ctx["art_type"], ctx["season"], ctx["episode"], ext
    )

    dest = os.path.join(base_dir, filename)
    uploaded.save(dest)

    _mark_asset_fresh(plex, ctx["section_key"])
    return _browse_redirect(ctx, f"Saved to {dest}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
