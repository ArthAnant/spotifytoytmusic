import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic, OAuthCredentials

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

def create_youtube_music_playlist(tracks, playlist_name):
    ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id=os.getenv("YT_CLIENT_ID"), client_secret=os.getenv("YT_CLIENT_SECRET")))
    # Create playlist
    playlist_id = ytmusic.create_playlist(
        title=playlist_name,
        description="Migrated from Spotify"
    )
    print(tracks)
    for track in tracks:
        query_song = f"{track['title']} {track['artist']}"
        print(f"Searching for: {query_song}")
        search = ytmusic.search(query_song, limit=1)
        if search:
            video_id = search[0]['videoId']
            ytmusic.add_playlist_items(
                playlistId=playlist_id,
                videoIds=[video_id]
            )
            print(f"Added: {query_song}")
        else:
            print(f"Not found: {query_song}")
    
    return playlist_id
if __name__ == "__main__":
    spotify_url = input("Enter Spotify Playlist URL: ")
    playlist_name = input("Enter New Playlist Name: ")
    tracks = get_spotify_playlist_tracks(spotify_url)
    print(f"Found {len(tracks)} tracks")
    
    yt_playlist_id = create_youtube_music_playlist(tracks, playlist_name)
    print(f"Created YouTube Music playlist: https://music.youtube.com/playlist?list={yt_playlist_id}")
    # print("\nFetching Spotify playlist...")
    # tracks = get_spotify_playlist_tracks(spotify_url)
    # print(f"Found {len(tracks)} tracks")