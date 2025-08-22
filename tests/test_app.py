import os
import sys
import pytest
from flask import session

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

def test_home_page(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Spotiplay' in resp.data

def test_login_redirect(client):
    resp = client.get('/login')
    assert resp.status_code == 302
    assert 'spotify.com/authorize' in resp.headers['Location']

@pytest.mark.parametrize('status,data', [
    (200, {'access_token': 'FAKE_TOKEN'}),
    (400, {})
])
def test_callback(client, requests_mock, status, data):
    requests_mock.post('https://accounts.spotify.com/api/token', json=data, status_code=status)
    # Mock user profile fetch after login
    requests_mock.get('https://api.spotify.com/v1/me', json={'id':'testuser'}, status_code=200)
    # Mock playlists fetch after login
    requests_mock.get('https://api.spotify.com/v1/me/playlists', json={'items': [{'name': 'Test Playlist', 'tracks': {'total': 1}}]}, status_code=200)
    # Mock albums fetch after login
    requests_mock.get('https://api.spotify.com/v1/me/albums', json={'items': [], 'total': 0}, status_code=200)
    url = '/callback?code=1234'
    resp = client.get(url, follow_redirects=True)
    if status == 200:
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert 'spotify_token' in sess
    else:
        assert resp.status_code == 400
        assert b'Spotify authorization failed' in resp.data

def test_dashboard_requires_login(client):
    resp = client.get('/dashboard', follow_redirects=False)
    assert resp.status_code == 302
    assert '/' == resp.headers['Location'] or '/?' in resp.headers['Location']

@pytest.mark.parametrize('profile_status,playlists_status', [
    (200, 200), (200, 500), (500, 200), (401, 401)
])
def test_dashboard_logged_in(client, requests_mock, profile_status, playlists_status):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    requests_mock.get('https://api.spotify.com/v1/me', json={'id':'testuser'}, status_code=profile_status)
    # Always include a tracks key for each playlist to match expected template structure
    playlist_items = [{'name': 'Test Playlist', 'tracks': {'total': 3}}] if playlists_status == 200 else []
    requests_mock.get('https://api.spotify.com/v1/me/playlists', json={'items': playlist_items}, status_code=playlists_status)
    requests_mock.get('https://api.spotify.com/v1/me/albums', json={'items': [], 'total': 0}, status_code=200)
    resp = client.get('/dashboard')
    assert resp.status_code == 200
    # Should still load dashboard, possibly with None playlists

@pytest.mark.parametrize('api_status,tracks_present', [
    (200, True), (200, False), (404, False)
])
def test_playlist_detail(client, requests_mock, api_status, tracks_present):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    playlist_id = 'PL123'
    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    playlist_json = {'name': 'Test Playlist', 'images': [], 'tracks': {'total': 1 if tracks_present else 0}}
    if api_status == 200:
        items = [{'track': {'id': 'T1', 'name': 'Track1', 'artists': [{'name': 'Artist1'}], 'album': {'images': [], 'id': 'A1'}, 'external_urls': {}}}] if tracks_present else []
        tracks_json = {'items': items, 'total': 1 if tracks_present else 0}
        requests_mock.get(playlist_url, json=playlist_json, status_code=200)
        requests_mock.get(f'{tracks_url}?fields=items(track(id,name,artists,album,external_urls)),total,next,previous&offset=0&limit=50', json=tracks_json, status_code=200)
        requests_mock.get('https://api.spotify.com/v1/me/albums/contains?ids=A1', json=[False], status_code=200)
        resp = client.get(f'/playlist/{playlist_id}')
        assert resp.status_code == 200
        if tracks_present:
            assert b'Track1' in resp.data
        else:
            assert b'No tracks found' in resp.data
    else:
        requests_mock.get(playlist_url, status_code=404)
        resp = client.get(f'/playlist/{playlist_id}')
        assert resp.status_code == 400

def test_playlist_requires_login(client):
    resp = client.get('/playlist/dummy123', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')

def test_add_playlist_to_library_success(client, requests_mock):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    playlist_id = 'PLX'
    tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track(id)),next&limit=100'
    requests_mock.get(tracks_url, json={'items': [{'track': {'id': 'T1'}}], 'next': None}, status_code=200)
    requests_mock.put('https://api.spotify.com/v1/me/tracks', status_code=200, json={})
    resp = client.post(f'/add_playlist_to_library/{playlist_id}')
    assert b'Added 1 tracks' in resp.data

def test_add_playlist_to_library_failure(client, requests_mock):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    playlist_id = 'PLX'
    tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track(id)),next&limit=100'
    requests_mock.get(tracks_url, json={'items': [{'track': {'id': 'T1'}}], 'next': None}, status_code=200)
    requests_mock.put('https://api.spotify.com/v1/me/tracks', status_code=400, json={})
    resp = client.post(f'/add_playlist_to_library/{playlist_id}')
    assert b'Some tracks may not have been added' in resp.data

def test_add_playlist_to_library_not_logged_in(client):
    playlist_id = 'PLX'
    resp = client.post(f'/add_playlist_to_library/{playlist_id}')
    assert resp.status_code == 401

def test_add_track_to_library_success(client, requests_mock):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    requests_mock.put('https://api.spotify.com/v1/me/tracks', status_code=200, json={})
    resp = client.post('/add_track_to_library/T123')
    assert b'Added to your library!' in resp.data

def test_add_track_to_library_failure(client, requests_mock):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    requests_mock.put('https://api.spotify.com/v1/me/tracks', status_code=400, json={})
    resp = client.post('/add_track_to_library/T123')
    assert b'Failed to add track' in resp.data

def test_add_track_to_library_not_logged_in(client):
    resp = client.post('/add_track_to_library/T123')
    assert resp.status_code == 401

def test_add_album_to_library_success(client, requests_mock):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    requests_mock.put('https://api.spotify.com/v1/me/albums', status_code=200, json={})
    resp = client.post('/add_album_to_library/A123')
    assert b'Album added to your library!' in resp.data

def test_add_album_to_library_failure(client, requests_mock):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'FAKE_TOKEN'
    requests_mock.put('https://api.spotify.com/v1/me/albums', status_code=400, json={})
    resp = client.post('/add_album_to_library/A123')
    assert b'Failed to add album' in resp.data

def test_add_album_to_library_not_logged_in(client):
    resp = client.post('/add_album_to_library/A123')
    assert resp.status_code == 401

def test_logout(client):
    with client.session_transaction() as sess:
        sess['spotify_token'] = 'dummy_token'
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert 'spotify_token' not in sess


