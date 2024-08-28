# scrapers/scraper1/handler.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import os
import time
import boto3
from botocore.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure SQS connection to ElasticMQ
sqs = boto3.client(
    'sqs',
    region_name='us-west-2',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    endpoint_url='http://elasticmq:9324',  # Use the Docker service name instead of localhost
    config=Config(retries={'max_attempts': 0}, connect_timeout=5, read_timeout=60)
)

# Queue URL for the SQS queue created in ElasticMQ
SQS_QUEUE_URL = 'http://elasticmq:9324/000000000000/youtube_trend_100'

def send_to_sqs(data):
    try:
        response = sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(data))
        logging.info(f"Message sent to SQS with ID: {response['MessageId']}")
    except Exception as e:
        logging.error(f"Failed to send message to SQS: {e}")

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensures Chrome runs headless
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")  # Applicable if running in Docker
chrome_options.add_argument("--remote-debugging-port=9222")  # Port for remote debugging

# Automatically download and set up ChromeDriver
service = Service(ChromeDriverManager().install())

# Set up WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

def scrape_youtube_trending():
    # Navigate to YouTube Trending Page
    url = "https://charts.youtube.com/charts/TopVideos/IL/weekly"
    driver.get(url)
    time.sleep(10)  # Adjust this depending on the page load time

    # Parse the HTML content
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, "html.parser")

    songs_data = []
    entries = soup.find_all('ytmc-entry-row')
    if not entries:
        logging.warning("No entries found on the page.")
    else:
        logging.info(f"Found {len(entries)} entries.")
    
    for entry in entries:
        try:
            song = {}
            # Extract the rank
            rank_tag = entry.find('span', id='rank')
            if rank_tag:
                song['rank'] = rank_tag.text.strip()
            
            # Extract the title
            title_tag = entry.find('div', class_='title')
            if title_tag:
                song['title'] = title_tag.text.strip()
            
            # Extract the artist names
            artist_tags = entry.find_all('span', class_='artistName')
            song['artist'] = [artist.text.strip() for artist in artist_tags]
            
            # Extract the distribution date (if available)
            distribution_date_tag = entry.find('span', class_='detailed-view-content detailed-view-release-date')
            if distribution_date_tag:
                song['distribution_date'] = distribution_date_tag.text.strip()
            else:
                song['distribution_date'] = "2024-08-23"  # Fallback static date

            # Add a static source
            song['source'] = 'youtube-trend100'
            
            logging.info(f"Scraped song: {song}")
            songs_data.append(song)
        except Exception as e:
            logging.error(f"Error processing entry: {e}")

    # Send each song data to SQS
    for song in songs_data:
        send_to_sqs(song)

    logging.info("Scraping and sending to SQS completed.")

# Run the scraper
try:
    scrape_youtube_trending()
finally:
    driver.quit()
