import os

import math
import string
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from plexapi.server import PlexServer

app = Flask(__name__)
app.secret_key = os.urandom(24)

# module‑level alphabet list so we only build it once
ALPHABET = list(string.ascii_uppercase)
ALPHABET.insert(0, "0-9")

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
    return render_template("connect.html")


@app.route("/libraries")
def libraries():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))
    sections = plex.library.sections()
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

    # optional letter filter (defaults to 'All')
    letter = request.args.get("letter", "All")
    if letter != "All":
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

    # pagination params (based on filtered set)
    total    = len(items_filtered)
    per_page = 20
    pages    = math.ceil(total / per_page)

    # clamp page number
    page = int(request.args.get("page", 1))
    page = max(1, min(page, pages))

    # slice out this page from filtered items
    start      = (page - 1) * per_page
    page_items = items_filtered[start : start + per_page]

    return render_template(
        "items.html",
        section=section,
        items=page_items,
        page=page,
        pages=pages,
        per_page=per_page,
        alphabet=ALPHABET,
        letter=letter,
    )
# http://127.0.0.1:5000/browse/5?page=1&art_type=poster&art_page=1&season=3&episode=


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
    items = list(section.all())
    pages = len(items)
    item_page = int(request.args.get("page", 1))
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

    return render_template(
        "item.html",
        section=section,
        item=item,
        season_rating_key=season_rating_key,
        items=items,
        item_page=item_page,
        pages=pages,
        art_type=art_type,
        season=season,
        episode=episode,
        art_page=art_page,
    )


@app.route("/download", methods=["POST"])
def download():
    plex = get_plex()
    if not plex:
        return redirect(url_for("connect"))

    rating_key = int(request.form["rating_key"])
    try:
        season_rating_key = int(request.form["season_rating_key"])
    except:
        season_rating_key = None

    # try:
    #     episode_rating_key = int(request.form['episode_rating_key'])
    # except:
    #     episode_rating_key = None
    section_key = request.form["section_key"]
    art_type = request.form["art_type"]
    img_key = request.form["img_key"]
    season = (
        None if request.form.get("season") == "None" else request.form.get("season")
    )
    episode = (
        None if request.form.get("episode") == "None" else request.form.get("episode")
    )
    item_page = request.form.get("item_page", 1)
    art_page = request.form.get("art_page", 1)

    item = plex.fetchItem(rating_key)
    season_item = None if not season_rating_key else plex.fetchItem(season_rating_key)
    # episode_item = None if not episode_rating_key else plex.fetchItem(episode_rating_key)

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
    except:
        asset_name = item.title

    base_dir = os.path.join(
        os.getcwd(),
        session["asset_dir"],
        "movies" if item.type == "movie" else "series",
        asset_name,
    )
    os.makedirs(base_dir, exist_ok=True)

    ext = os.path.splitext(img_key)[1] or ".jpg"
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
        filename = f"{name}{suffix}{ext}"
    else:
        filename = f"{art_type}{ext}"

    if img_key.startswith("http"):
        img_url = img_key
    else:
        img_url = f"{session['base_url']}{img_key}&X-Plex-Token={session['token']}"

    resp = requests.get(img_url)
    with open(os.path.join(base_dir, filename), "wb") as f:
        f.write(resp.content)

    flash(f"Saved to {os.path.join(base_dir, filename)}")
    return redirect(
        url_for(
            "browse",
            section_key=section_key,
            page=item_page,
            art_type=art_type,
            season=season,
            episode=episode,
            art_page=art_page,
        )
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
