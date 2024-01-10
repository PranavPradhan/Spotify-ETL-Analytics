import urllib
import urllib.request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import sys
from dotenv import load_dotenv
import os 
import base64 
from requests import post, get 
import json

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
print(client_id, client_secret)

redirect_uri = "http://localhost:5000/callback"
scope = 'user-top-read'


def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization" : "Basic " + auth_base64, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {"grant_type" : "client_credentials"}
    result = post(url, headers=headers, data = data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token 

def get_auth_header(token):
    return {"Authorization" : "Bearer " + token}

def get_top_artists(): 
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id= client_id, client_secret= client_secret, redirect_uri= redirect_uri, scope=scope))
    results = sp.current_user_top_artists(time_range='short_term', limit=50) 
    return results 

top_artists = get_top_artists()

def extract_artist_info(top_artists):
    artist_info_list = []

    for artist in top_artists['items']:
        artist_info = {
            'name': artist['name'],
            'genres': artist['genres'],
            'popularity': artist['popularity']
        

        }
         # Fetch artist's top albums
        top_albums = sp.artist_albums(artist['id'], album_type='album', limit=5)  # Limit to 5 albums for brevity
        artist_info['top_albums'] = []

        for album in top_albums['items']:
            album_info = {
                'name': album['name'],
                'id': album['id'],
                'release_date': album['release_date'],
                'total_tracks': album['total_tracks'],
            }
            artist_info['top_albums'].append(album_info)


        # Fetch artist's top tracks
        top_tracks = sp.artist_top_tracks(artist['id'], country='US')  # You can specify a different country
        artist_info['top_tracks'] = []
        for track in top_tracks['tracks']:
                # Fetch audio analysis for each track
            audio_analysis = sp.audio_analysis(track['id'])
            track_info = {
                'name': track['name'],
                'duration_min_sec': milliseconds_to_minutes_seconds(track['duration_ms']),
                'BPM': audio_analysis['track']['tempo'],
                'mode': 'major' if audio_analysis['track']['mode'] == 1 else 'minor'
            }
            
            artist_info['top_tracks'].append(track_info)

        appears_on = sp.artist_albums(artist['id'], album_type='appears_on', limit=5)  # Limit to 5 albums for brevity
        artist_info['appears_on'] = [album['name'] for album in appears_on['items']]

    


        artist_info_list.append(artist_info)

    return artist_info_list

def milliseconds_to_minutes_seconds(milliseconds):
    seconds = milliseconds / 1000
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02}:{int(seconds):02}"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

artist_info_list = extract_artist_info(top_artists)
# if isinstance(artist_info_list, list) and artist_info_list:
#         artist_info_list = artist_info_list[:]




# Save artist information to a JSON file
output_file = "top_artists_info.json"

with open(output_file, "w") as json_file:
    json.dump(artist_info_list, json_file, indent=4)


print(f"Artist information saved to {output_file}")

