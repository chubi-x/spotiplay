import os
from flask import Flask, render_template, redirect, url_for, request, session
from dotenv import load_dotenv
import requests

# Spotify API URLs
SPOTIFY_API = {
    'auth': {
        'authorize': 'https://accounts.spotify.com/authorize',
        'token': 'https://accounts.spotify.com/api/token'
    },
    'user': {
        'profile': 'https://api.spotify.com/v1/me',
        'playlists': 'https://api.spotify.com/v1/me/playlists',
        'albums': 'https://api.spotify.com/v1/me/albums',
        'tracks': 'https://api.spotify.com/v1/me/tracks',
        'check_saved_albums': 'https://api.spotify.com/v1/me/albums/contains'
    },
    'playlists': {
        'get': 'https://api.spotify.com/v1/playlists/{playlist_id}',
        'tracks': 'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    }
}

def fetch_spotify_items_with_pagination(endpoint, token, offset=0, limit=20, item_key="items"):
    """
    Utility to fetch paginated data from Spotify API.
    Returns: items, total, next_offset, prev_offset
    """
    headers = {'Authorization': f"Bearer {token}"}
    resp = requests.get(f"{endpoint}?limit={limit}&offset={offset}", headers=headers)
    if resp.status_code != 200:
        return [], 0, None, None
    data = resp.json()
    items = data.get(item_key, [])
    total = data.get('total', 0)
    next_offset = offset + limit if offset + limit < total else None
    prev_offset = offset - limit if offset - limit >= 0 else (0 if offset > 0 else None)
    return items, total, next_offset, prev_offset

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random session secret

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login')
def login():
    scope = 'user-library-read user-library-modify playlist-read-private user-read-email'
    auth_url = (
        f'{SPOTIFY_API["auth"]["authorize"]}?'
        f'client_id={SPOTIFY_CLIENT_ID}'
        f'&response_type=code'
        f'&redirect_uri={SPOTIFY_REDIRECT_URI}'
        f'&scope={scope.replace(" ", "+")}'
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = SPOTIFY_API['auth']['token']
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        session['spotify_token'] = response.json()['access_token']
        return redirect(url_for('dashboard'))
    else:
        return 'Spotify authorization failed', 400

@app.route('/dashboard')
def dashboard():
    if 'spotify_token' not in session:
        return redirect(url_for('index'))

    headers = {'Authorization': f"Bearer {session['spotify_token']}"}

    # Fetch user profile from Spotify
    user_profile = None
    profile_resp = requests.get(SPOTIFY_API['user']['profile'], headers=headers)
    if profile_resp.status_code == 200:
        user_profile = profile_resp.json()

    # Fetch user playlists from Spotify
    playlists = []
    resp = requests.get(SPOTIFY_API['user']['playlists'], headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        playlists = data.get('items', [])
    else:
        playlists = None

    # Paginate user albums
    try:
        album_offset = int(request.args.get('album_offset', 0))
    except ValueError:
        album_offset = 0
    album_limit = 20
    albums, total_albums, next_album_offset, prev_album_offset = fetch_spotify_items_with_pagination(
        SPOTIFY_API['user']['albums'],
        session['spotify_token'],
        offset=album_offset, limit=album_limit, item_key='items')

    return render_template(
        'dashboard.html',
        playlists=playlists,
        albums=albums,
        user_profile=user_profile,
        album_offset=album_offset,
        album_limit=album_limit,
        total_albums=total_albums,
        next_album_offset=next_album_offset,
        prev_album_offset=prev_album_offset
    )

from flask import jsonify

@app.route('/playlist/<playlist_id>')
def playlist_detail(playlist_id):
    if 'spotify_token' not in session:
        return redirect(url_for('login'))
    headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    # Get pagination params
    try:
        offset = int(request.args.get('offset', 0))
    except ValueError:
        offset = 0
    limit = 50
    # Fetch playlist details
    playlist_resp = requests.get(SPOTIFY_API['playlists']['get'].format(playlist_id=playlist_id), headers=headers)
    if playlist_resp.status_code != 200:
        return "Failed to fetch playlist", 400
    playlist = playlist_resp.json()
    # Fetch just one page of tracks
    tracks_url = f"{SPOTIFY_API['playlists']['tracks'].format(playlist_id=playlist_id)}?fields=items(track(id,name,artists,album,external_urls)),total,next,previous&offset={offset}&limit={limit}"
    track_resp = requests.get(tracks_url, headers=headers)
    tracks = []
    total_tracks = 0
    next_offset = None
    prev_offset = None
    saved_albums = {}
    if track_resp.status_code == 200:
        data = track_resp.json()
        for item in data.get('items', []):
            if item.get('track'):
                tracks.append(item['track'])
        total_tracks = playlist['tracks']['total']
        # Pagination
        if offset + limit < total_tracks:
            next_offset = offset + limit
        if offset - limit >= 0:
            prev_offset = offset - limit
        elif offset > 0:
            prev_offset = 0
        
        # Extract unique album IDs to check if they're in the user's library
        unique_album_ids = []
        seen_album_ids = set()
        for track in tracks:
            album = track.get('album')
            if album and album.get('id') and album['id'] not in seen_album_ids:
                unique_album_ids.append(album['id'])
                seen_album_ids.add(album['id'])
        
        # Check which albums are in the user's library
        saved_albums = {}
        if unique_album_ids:
            # Spotify API allows checking up to 50 IDs at once
            for i in range(0, len(unique_album_ids), 50):
                batch = unique_album_ids[i:i+50]
                check_url = f"https://api.spotify.com/v1/me/albums/contains?ids={','.join(batch)}"
                check_resp = requests.get(check_url, headers=headers)
                if check_resp.status_code == 200:
                    results = check_resp.json()
                    for album_id, is_saved in zip(batch, results):
                        saved_albums[album_id] = is_saved
    
    return render_template(
        'playlist_detail.html', 
        playlist=playlist, 
        tracks=tracks, 
        offset=offset, 
        limit=limit, 
        total_tracks=total_tracks, 
        next_offset=next_offset, 
        prev_offset=prev_offset,
        saved_albums=saved_albums
    )

@app.route('/add_playlist_to_library/<playlist_id>', methods=['POST'])
def add_playlist_to_library(playlist_id):
    if 'spotify_token' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    # Step 1: Fetch all track IDs from the playlist (handle pagination)
    track_ids = []
    url = f"{SPOTIFY_API['playlists']['tracks'].format(playlist_id=playlist_id)}?fields=items(track(id)),next&limit=100"
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            return render_template('htmx_add_result.html', message='Failed to fetch playlist tracks.')
        data = resp.json()
        for item in data.get('items', []):
            track = item.get('track')
            if track and track.get('id'):
                track_ids.append(track['id'])
        url = data.get('next')
    # Step 2: Add tracks to user's library in batches of 50
    batch_size = 50
    failed = False
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i+batch_size]
        save_url = SPOTIFY_API['user']['tracks']
        save_resp = requests.put(save_url, headers={**headers, 'Content-Type': 'application/json'}, json={'ids': batch})
        if save_resp.status_code not in (200, 201):
            failed = True
    message = f"Added {len(track_ids)} tracks to your library!" if not failed else "Some tracks may not have been added."
    return render_template('htmx_add_result.html', message=message)

@app.route('/add_track_to_library/<track_id>', methods=['POST'])
def add_track_to_library(track_id):
    if 'spotify_token' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    save_url = SPOTIFY_API['user']['tracks']
    resp = requests.put(save_url, headers={**headers, 'Content-Type': 'application/json'}, json={'ids': [track_id]})
    if resp.status_code in (200, 201):
        message = 'Added to your library!'
    else:
        message = 'Failed to add track.'
    return render_template('htmx_add_result.html', message=message)

@app.route('/add_album_to_library/<album_id>', methods=['POST'])
def add_album_to_library(album_id):
    if 'spotify_token' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    save_url = SPOTIFY_API['user']['albums']
    resp = requests.put(save_url, headers={**headers, 'Content-Type': 'application/json'}, json={'ids': [album_id]})
    if resp.status_code in (200, 201):
        message = 'Album added to your library!'
    else:
        message = 'Failed to add album.'
    return render_template('htmx_add_result.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)

