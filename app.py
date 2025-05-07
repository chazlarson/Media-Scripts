from flask import Flask, render_template, request, redirect, url_for, session, flash
from plexapi.server import PlexServer
import os
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_plex():
    base_url = session.get('base_url')
    token = session.get('token')
    if not base_url or not token:
        return None
    return PlexServer(base_url, token)

@app.route('/', methods=['GET', 'POST'])
def connect():
    if request.method == 'POST':
        session['base_url'] = request.form['base_url']
        session['token'] = request.form['token']
        return redirect(url_for('libraries'))
    return render_template('connect.html')

@app.route('/libraries')
def libraries():
    plex = get_plex()
    if not plex:
        return redirect(url_for('connect'))
    sections = plex.library.sections()
    return render_template('libraries.html', sections=sections)

@app.route('/gallery/<section_key>')
def gallery(section_key):
    plex = get_plex()
    if not plex:
        return redirect(url_for('connect'))
    # find section by key
    section = next((s for s in plex.library.sections() if str(s.key) == section_key), None)
    if not section:
        flash('Library not found.')
        return redirect(url_for('libraries'))
    page = int(request.args.get('page', 1))
    art_type = request.args.get('art_type', 'poster')
    items = list(section.all())
    total = len(items)
    per_page = 10
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return render_template('gallery.html', section=section, items=page_items,
                           page=page, pages=pages, art_type=art_type)

@app.route('/download', methods=['POST'])
def download():
    plex = get_plex()
    if not plex:
        return redirect(url_for('connect'))
    rating_key = request.form['rating_key']
    art_type = request.form['art_type']
    section_key = request.form['section_key']
    page = request.form.get('page', 1)
    item = plex.fetchItem(rating_key)
    # Determine asset name (folder)
    try:
        media_file = item.media[0].parts[0].file
        asset_name = os.path.basename(os.path.dirname(media_file))
    except:
        # Fallback for seasons: use show title
        asset_name = item.title
    # Build directory
    base_dir = os.path.join(os.getcwd(), 'assets', 'movies' if item.type == 'movie' else 'series', asset_name)
    os.makedirs(base_dir, exist_ok=True)
    # Choose URL and filename
    url = item.posterUrl if art_type == 'poster' else item.artUrl
    if item.type == 'season':
        filename = f"Season {item.index:02d}.jpg"
    elif item.type == 'episode':
        s = item.seasonNumber
        e = item.index
        filename = f"S{s:02d}E{e:02d}.jpg"
    else:
        filename = f"{art_type}.jpg"
    # Download and save
    resp = requests.get(f"{session['base_url']}{url}", headers={'X-Plex-Token': session['token']})
    with open(os.path.join(base_dir, filename), 'wb') as f:
        f.write(resp.content)
    flash(f"Saved to {os.path.join(base_dir, filename)}")
    return redirect(url_for('gallery', section_key=section_key, page=page, art_type=art_type))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
