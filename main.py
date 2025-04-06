import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))
#ytmusic = YTMusic("headers_auth.json")

def get_spotify_playlist_tracks(playlist_url):
    #Extract track names and artists from a Spotify playlist.
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    results = sp.playlist_tracks(playlist_id)
    
    tracks = []
    while results:
        for item in results['items']:
            track = item['track']
            tracks.append({
                'title': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name']
            })
        results = sp.next(results) if results['next'] else None
    
    return tracks

if __name__ == "__main__":
    spotify_url = input("Enter Spotify Playlist URL: ")
    print("\nFetching Spotify playlist...")
    tracks = get_spotify_playlist_tracks(spotify_url)
    print(f"Found {len(tracks)} tracks")