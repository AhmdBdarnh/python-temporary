#processor/handler.py
import boto3
import json
import logging
from botocore.config import Config
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from crud.handler import insert_song_data, connect_to_db, close_connection  # Import necessary functions from the CRUD handler

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure SQS connection to ElasticMQ
sqs = boto3.client(
    'sqs',
    region_name='us-west-2',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    endpoint_url='http://elasticmq:9324',
    config=Config(retries={'max_attempts': 0}, connect_timeout=5, read_timeout=60)
)

# Queue URLs for the SQS queues
SQS_QUEUE_URLS = {
    'top30': 'http://elasticmq:9324/000000000000/top30',
    'youtube-trend100': 'http://elasticmq:9324/000000000000/youtube_trend_100'
}

# Configure Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id='70b7e8fc478247949322b609c0201a95',
    client_secret='b42d215b97b845a3a63118e544cec385'
))

# Function to fetch additional information from Spotify
def fetch_spotify_data(song_title, artist_name):
    try:
        results = sp.search(q=f"track:{song_title} artist:{artist_name}", type='track', limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            artist_id = track['artists'][0]['id']

            artist = sp.artist(artist_id)
            genres = ', '.join(artist['genres']) if artist['genres'] else 'Unknown'

            return {
                'genre': genres,
                'duration_ms': track['duration_ms'],
                'spotify_link': track['external_urls']['spotify']
            }
        else:
            return None
    except Exception as e:
        logging.error(f"Error fetching Spotify data: {e}")
        return None

# Function to fetch artist details from MusicBrainz API
def fetch_artist_data(artist_name):
    try:
        url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{artist_name}&fmt=json"
        response = requests.get(url)
        data = response.json()

        if data['artists']:
            artist_info = data['artists'][0]
            return {
                'artist_name': artist_info.get('name', 'Unknown'),
                'country': artist_info.get('country', 'Unknown'),
                'gender': artist_info.get('gender', 'Unknown'),
                'disambiguation': artist_info.get('disambiguation', 'None'),
                'aliases': ', '.join(alias['name'] for alias in artist_info.get('aliases', [])),
                'tags': ', '.join(tag['name'] for tag in artist_info.get('tags', []))
            }
        else:
            return None
    except Exception as e:
        logging.error(f"Error fetching artist data: {e}")
        return None

# Function to process messages from SQS
def process_message(message, source):
    conn, cursor = connect_to_db()  # Open a database connection
    try:
        # Parse the JSON data from the message
        song_data = json.loads(message['Body'])
        logging.info(f"Processing song: {song_data['title']} from source: {source}")

        # Fetch additional data from Spotify
        spotify_data = fetch_spotify_data(song_data['title'], song_data['artist'])
        genre = spotify_data['genre'] if spotify_data else 'Unknown'
        duration_ms = spotify_data['duration_ms'] if spotify_data else None
        spotify_link = spotify_data['spotify_link'] if spotify_data else None

        # Fetch artist data from MusicBrainz
        artist_data = fetch_artist_data(song_data['artist'])

        # Log the processed song data
        logging.info(json.dumps({
            "id": song_data.get("id", "Unknown"),
            "rank": song_data.get("rank", "Unknown"),
            "title": song_data.get("title", "Unknown"),
            "artist": song_data.get("artist", "Unknown"),
            "distribution_date": song_data.get("distribution_date", "Unknown"),
            "genre": genre,
            "duration_ms": duration_ms,
            "spotify_link": spotify_link,
            "source": source
        }, indent=4))

        # Call the CRUD function to insert the data into the database
        insert_song_data(conn, cursor, song_data, artist_data, genre, duration_ms, spotify_link, source)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        conn.rollback()
    finally:
        close_connection(conn, cursor)  # Ensure the connection is closed

# Polling SQS for messages from multiple queues
def poll_sqs():
    while True:
        for source, queue_url in SQS_QUEUE_URLS.items():
            try:
                response = sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20
                )

                if 'Messages' in response:
                    for message in response['Messages']:
                        logging.info(f"Received message from {source}: {message}")
                        process_message(message, source)
                        # Delete message after processing
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                else:
                    logging.info(f"No messages to process from queue: {source}.")
            except Exception as e:
                logging.error(f"Error polling SQS queue {queue_url}: {e}")

# The handler function for AWS Lambda
def handler(event, context):
    for record in event['Records']:
        process_message(record, 'lambda-source')  # You can set a different source for Lambda invocations
    return {
        'statusCode': 200,
        'body': json.dumps('Messages processed successfully')
    }

if __name__ == "__main__":
    try:
        logging.info("Starting processor for multiple queues...")
        poll_sqs()
    except KeyboardInterrupt:
        logging.info("Stopping the processor.")
