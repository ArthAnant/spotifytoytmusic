import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic, OAuthCredentials
import json
from pathlib import Path
import time
import random
from spot_play_tracks import get_spotify_playlist_tracks
from playlist_creation import *

load_dotenv()

if __name__ == "__main__":
    spotify_url = input("Enter Spotify Playlist URL: ")
    playlist_name = input("Enter New Playlist Name: ")
    start_time = time.time()
    yt_playlist_id = create_youtube_music_playlist(spotify_url, playlist_name)
    print(f"Created YouTube Music playlist: https://music.youtube.com/playlist?list={yt_playlist_id}")
    print(f"Time taken: {time.time() - start_time} seconds")