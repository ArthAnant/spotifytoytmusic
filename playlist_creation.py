import os
from dotenv import load_dotenv
from ytmusicapi import YTMusic, OAuthCredentials
import json
from pathlib import Path
import time
import random
from spot_play_tracks import get_spotify_playlist_tracks
from concurrent.futures import ThreadPoolExecutor, as_completed


ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(
                    client_id=os.getenv("YT_CLIENT_ID"), 
                    client_secret=os.getenv("YT_CLIENT_SECRET")
))

load_dotenv()
THREAD_AMOUNT = 5
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

def search_song(track):
    query = f"{track['title']} {track['artist']}"
    try:
        delay()
        results = ytmusic.search(query, filter="songs", limit=1)
        return {
            'original_track': track,
            'video_id': results[0]['videoId'] if results else None
        }
    except Exception as e:
        print(f"Search failed for {query}: {str(e)}")
        return {'original_track': track, 'video_id': None}


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
        if f"{t['title']}: {t['artist']}" not in existing_tracks
    ]
    if not new_tracks:
        print("No new tracks to add.")
        return playlist_id
    
    print(f"Found {len(new_tracks)} new tracks")

    video_ids = []
    #seaching for tracks in parallel
    with ThreadPoolExecutor(max_workers=THREAD_AMOUNT) as executor:
        futures = {executor.submit(search_song, track): i for i, track in enumerate(new_tracks)}
        
        for future in as_completed(futures):
            #track = futures[future]
            result = future.result()
            video_ids.append((futures[future], result))
    ordered_results = [res for (i, res) in sorted(video_ids, key=lambda x: x[0])]

    #Adding tracks to playlist
    added_number = 0
    for result in ordered_results:
        track = result['original_track']
        video_id = result['video_id']
        if not video_id:
            print(f"Not found: {track['title']}: {track['artist']}")
            continue
        try:
            ytmusic.add_playlist_items(playlist_id, [video_id])
            playlist_data['added_tracks'].append({
                'title': track['title'],
                'artist': track['artist'],
                'video_id': video_id
            })
            added_number += 1
            print(f"Added ({added_number}/{len(new_tracks)}): {track['title']}")
            delay()
        except Exception as e:
            print(f"Failed to add {track['title']}: {str(e)}")

    #save database state
    db['playlists'][playlist_name] = playlist_data
    update_db(db)
    print(f"\nAdded {added_number}/{len(new_tracks)} new tracks to playlist")
    return playlist_id