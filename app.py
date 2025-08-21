import os
from flask import Flask, render_template, redirect, url_for, request, session
from dotenv import load_dotenv
import requests

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
        'https://accounts.spotify.com/authorize?'
        f'client_id={SPOTIFY_CLIENT_ID}'
        f'&response_type=code'
        f'&redirect_uri={SPOTIFY_REDIRECT_URI}'
        f'&scope={scope.replace(" ", "+")}'
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
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
    profile_resp = requests.get('https://api.spotify.com/v1/me', headers=headers)
    if profile_resp.status_code == 200:
        user_profile = profile_resp.json()

    # Fetch user playlists from Spotify
    playlists = []
    resp = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        playlists = data.get('items', [])
    else:
        playlists = None

    # Fetch user albums from Spotify
    albums = []
    album_resp = requests.get('https://api.spotify.com/v1/me/albums?limit=20', headers=headers)
    if album_resp.status_code == 200:
        album_data = album_resp.json()
        albums = album_data.get('items', [])
    else:
        albums = None

    return render_template('dashboard.html', playlists=playlists, albums=albums, user_profile=user_profile)

from flask import jsonify

@app.route('/playlist/<playlist_id>')
def playlist_detail(playlist_id):
    if 'spotify_token' not in session:
        return redirect(url_for('login'))
    headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    # Fetch playlist details
    playlist_resp = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers)
    if playlist_resp.status_code != 200:
        return "Failed to fetch playlist", 400
    playlist = playlist_resp.json()
    # Gather all tracks (handle pagination)
    tracks = []
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track(id,name,artists,album,external_urls)),next&limit=100'
    while url:
        track_resp = requests.get(url, headers=headers)
        if track_resp.status_code != 200:
            break
        data = track_resp.json()
        for item in data.get('items', []):
            if item.get('track'):
                tracks.append(item['track'])
        url = data.get('next')
    return render_template('playlist_detail.html', playlist=playlist, tracks=tracks)

@app.route('/add_playlist_to_library/<playlist_id>', methods=['POST'])
def add_playlist_to_library(playlist_id):
    if 'spotify_token' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    # Step 1: Fetch all track IDs from the playlist (handle pagination)
    track_ids = []
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track(id)),next&limit=100'
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
        save_url = 'https://api.spotify.com/v1/me/tracks'
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
    save_url = 'https://api.spotify.com/v1/me/tracks'
    resp = requests.put(save_url, headers={**headers, 'Content-Type': 'application/json'}, json={'ids': [track_id]})
    if resp.status_code in (200, 201):
        message = 'Added to your library!'
    else:
        message = 'Failed to add track.'
    return render_template('htmx_add_result.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)

