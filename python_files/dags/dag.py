import urllib
import urllib.request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import sys
import base64 
from requests import post, get 
import airflow
from airflow import DAG
# Update the usage of deprecated operators
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
#from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
import boto3
import json 
#from airflow.hooks.S3_hook import S3Hook
import os 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from dotenv import load_dotenv

#Using Spotify's API 
redirect_uri = "http://localhost:5000/callback"
scope = 'user-top-read'


load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
print(client_id, client_secret)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

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
            'id': artist['id'],
            'genres': artist['genres'],
            'popularity': artist['popularity']

        }
        artist_info_list.append(artist_info)
    return artist_info_list

# Function to append top albums to the artist info list
def append_top_albums(artist_info_list, sp):
    for artist_info in artist_info_list:
        artist_id = artist_info['id']
        top_albums = sp.artist_albums(artist_id, album_type='album', limit=5)
        artist_info['top_albums'] = [{
            'name': album['name'],
            'id': album['id'],
            'release_date': album['release_date'],
            'total_tracks': album['total_tracks']
        } for album in top_albums['items']]
    return artist_info_list

def append_top_tracks(artist_info_list, sp):
    for artist_info in artist_info_list:
        artist_id = artist_info['id']
        top_tracks = sp.artist_top_tracks(artist_id, country='US')  # You can specify a different country
        artist_info['top_tracks'] = []

        for track in top_tracks['tracks']:
            audio_analysis = sp.audio_analysis(track['id'])
            track_info = {
                'name': track['name'],
                'duration_min_sec': milliseconds_to_minutes_seconds(track['duration_ms']),
                'BPM': audio_analysis['track']['tempo'],
                'mode': 'major' if audio_analysis['track']['mode'] == 1 else 'minor'
            }
            artist_info['top_tracks'].append(track_info)

    return artist_info_list

def milliseconds_to_minutes_seconds(milliseconds):
    seconds = milliseconds / 1000
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02}:{int(seconds):02}"
#sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))


# artist_info_list = extract_artist_info(top_artists)
# artist_info_list = append_top_albums(artist_info_list, sp)
# artist_info_list = append_top_tracks(artist_info_list, sp)

# output_file = "top_artists_info.json"

# with open(output_file, "w") as json_file:
#     json.dump(artist_info_list, json_file, indent=4)


# print(f"Artist information saved to {output_file}")

# Save artist information to a JSON file



#Save artist information to a JSON file
#Begin Dag configuration 
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 3),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
def extract_data():
    top_artists = get_top_artists()
    artist_info_list = extract_artist_info(top_artists)

    file_path = '/tmp/output.json'  
    with open(file_path, "w") as json_file:
        json.dump(artist_info_list, json_file, indent=4)

    return file_path 

def top_albums(**kwargs):
    ti = kwargs['ti']
    artist_info_list = ti.xcom_pull(task_ids='extract_data')  # Pulling data from the previous task
    with open(artist_info_list, 'r') as json_file:
        artist_info_list = json.load(json_file)

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))


    
    append_top_albums(artist_info_list, sp)  

    # Write the updated data back to the file
    file_path = '/tmp/output.json'  
    with open(file_path, "w") as json_file:
        json.dump(artist_info_list, json_file, indent=4)

    return file_path

def top_tracks(**kwargs):
    ti = kwargs['ti']
    artist_info_list = ti.xcom_pull(task_ids='top_albums')  # Pull the data from the previous task
    with open(artist_info_list, 'r') as json_file:
        artist_info_list = json.load(json_file)

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))


    
    append_top_tracks(artist_info_list, sp)  

    # Write the updated data back to the file
    file_path = '/tmp/output.json'  
    with open(file_path, "w") as json_file:
        json.dump(artist_info_list, json_file, indent=4)

    return file_path

def load_data_to_s3(bucket_name, s3_file_name, **kwargs):
    ti = kwargs['ti']
    file_path = ti.xcom_pull(task_ids='top_tracks')
    
    s3_hook = S3Hook(aws_conn_id='aws_s3_conn')  # Use AWS connection ID configured on Airflow UI
    s3_hook.load_file(filename=file_path, bucket_name=bucket_name, key=s3_file_name, replace=True)


dag = DAG(
    'etl_top_artists_to_s3',
    default_args=default_args,
    description='ETL job to load top_artists_info.json to S3',
    schedule_interval= None,
    catchup=False
)

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag,
)
top_albums_task = PythonOperator(
    task_id='top_albums',
    python_callable=top_albums,
    provide_context=True,
    dag=dag,
)
top_tracks_task = PythonOperator(
    task_id='top_tracks',
    python_callable=top_tracks,
    provide_context=True,
    dag=dag,
)


load_task = PythonOperator(
    task_id='load_data_to_s3',
    python_callable=load_data_to_s3,
    op_kwargs={'bucket_name': 'spotifyetlbucket',
               's3_file_name': 'top_artists_info.json'},
    provide_context=True,  
    dag=dag,
)

extract_task >> top_albums_task >> top_tracks_task >> load_task