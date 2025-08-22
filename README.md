# Spotiplay

Spotiplay is a web application that lets users log in with their Spotify account, view their playlists and albums, and quickly add songs to their personal Spotify library. Built with Flask, htmx, Alpine.js, and the Spotify Web API, the app offers a fast and interactive non-SPA interface.

## Features

- **Spotify Login**: Users authenticate securely via Spotify OAuth.
- **Dashboard**: See your Spotify display name and profile picture, with lists of all your playlists and saved albums.
- **Playlist Details**: Click a playlist to view all its tracks.
- **Add to Library**:
  - Add *all* tracks in a playlist to your Spotify library with one click.
  - Add *individual* tracks to your library from the playlist detail page.
- **Albums**: View your saved albums with cover art and artist info.
- **Interactive UI**: All actions use htmx and Alpine.js for a dynamic, responsive experience without needing a single-page app framework.

## Setup & Installation

1. **Clone the Repository**

   ```bash
   git clone <your-repo-url>
   cd spotiplay
   ```

2. **Create a Spotify Developer App**
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
   - Register a new app and note your **Client ID** and **Client Secret**
   - Set your Redirect URI to: `http://localhost:5000/callback`

3. **Configure Environment Variables**
   - Copy the provided `.env` template:
     ```bash
     cp .env.example .env
     ```
   - Or create a `.env` file with:
     ```env
     SPOTIFY_CLIENT_ID=your_spotify_client_id_here
     SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
     SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
     ```

4. **Install Python Requirements**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the App**
   ```bash
   python app.py
   ```
   Visit [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

- Click **Login with Spotify** and authorize the app.
- On the dashboard, browse playlists.
- Click any playlist to see all its songs.
- Use the **Add All Tracks to Library** button to quickly save everything in a playlist to your Spotify library, or use the individual buttons to save specific tracks.

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: HTML (Jinja templates), htmx, Alpine.js
- **APIs**: Spotify Web API

## Notes
- No data is stored server-side—only in your own Spotify account.
- The app uses Spotify's official scopes and APIs for full privacy and security.

## License
MIT
