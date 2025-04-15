import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic, OAuthCredentials
import json
from pathlib import Path
import time
import random

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(
                    client_id=os.getenv("YT_CLIENT_ID"), 
                    client_secret=os.getenv("YT_CLIENT_SECRET")
))

DB_FILE = Path('playlist_db.json')

def init_db():
    if not DB_FILE.exists():
        with open(DB_FILE, 'w') as f:
            json.dump({"playlists": {}}, f)

def get_db():
    with open(DB_FILE) as f:
        return json.load(f)
    
def update_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def delay():
    return random.uniform(1.25, 1.75)

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

def create_youtube_music_playlist(spotify_url, playlist_name):
    init_db()
    db = get_db()

    #Check if playlist already exists
    playlist_data = db['playlists'].get(playlist_name, {
        'yt_playlist_id': None,
        'added_tracks': []
    })

    spotify_tracks = get_spotify_playlist_tracks(spotify_url)
    print(f"Found {len(spotify_tracks)} Spotify tracks")
    
    #Create playlist
    if not playlist_data['yt_playlist_id']:
        playlist_id = ytmusic.create_playlist(title=playlist_name, description="Migrated from Spotify")
        playlist_data['yt_playlist_id'] = playlist_id
        print("Created new YouTube Music playlist", playlist_name)
    else:
        playlist_id = playlist_data['yt_playlist_id']
        print("Resuming work on existing playlist",  playlist_name)
    
    #Adding tracks to playlist
    existing_tracks = {f"{t['title']}: {t['artist']}" for t in playlist_data['added_tracks']}
    new_tracks = [
        t for t in spotify_tracks 
        if f"{t['title']}|{t['artist']}" not in existing_tracks
    ]
    if not new_tracks:
        print("No new tracks to add.")
        return playlist_id
    
    print(f"Found {len(new_tracks)} new tracks to add")

    added_number = 0
    for track in new_tracks:
        query_song = f"{track['title']} {track['artist']}"
        print(f"Searching for: {query_song}")
        time.sleep(delay())
        try:
            search = ytmusic.search(query_song, filter="songs", limit=1)
            if search:
                video_id = search[0]['videoId']
                ytmusic.add_playlist_items(
                    playlistId=playlist_id,
                    videoIds=[video_id]
                )
                time.sleep(delay())
                #update databse with added song
                playlist_data['added_tracks'].append({
                    'title': track['title'],
                    'artist': track['artist'],
                    'video_id': video_id
                })
                added_number += 1
                print("Added:", query_song)
            else:
                print("Not found:", query_song)
        except Exception as e:
            print(f"Error adding {query_song}: {str(e)}")
    
    #save database state
    db['playlists'][playlist_name] = playlist_data
    update_db(db)
    print(f"\nAdded {added_number} new tracks to playlist")
    return playlist_id

if __name__ == "__main__":
    spotify_url = input("Enter Spotify Playlist URL: ")
    playlist_name = input("Enter New Playlist Name: ")
    yt_playlist_id = create_youtube_music_playlist(spotify_url, playlist_name)
    print(f"Created YouTube Music playlist: https://music.youtube.com/playlist?list={yt_playlist_id}")
    # print("\nFetching Spotify playlist")
    # tracks = get_spotify_playlist_tracks(spotify_url)
    # print(f"Found {len(tracks)} tracks")