# scrapers/scraper2/handler.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
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
SQS_QUEUE_URL = 'http://elasticmq:9324/000000000000/top30'

def send_to_sqs(data):
    try:
        response = sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(data))
        logging.info(f"Message sent to SQS with ID: {response['MessageId']}")
    except Exception as e:
        logging.error(f"Failed to send message to SQS: {e}")

# Selenium Chrome setup
chrome_options = Options()
chrome_options.add_argument("--headless")  # Enable headless mode for Docker
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)

print("Starting scraper...")

# Fetch the webpage content
url = "https://charts.youtube.com/charts/TrendingVideos/il/RightNow"
try:
    driver.get(url)
    print("Page loaded, waiting for content...")
except Exception as e:
    print(f"Error fetching the page: {e}")
    driver.quit()
    exit()

# Wait for the page to load fully using WebDriverWait
try:
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
    print("Page body loaded, waiting for JavaScript to finish loading...")
    time.sleep(10)  # Give the page additional time to fully render
except Exception as e:
    print("Error loading the content:", e)
    driver.quit()
    exit()

# Get the page source after JavaScript execution
html_content = driver.page_source
print(html_content[:500])  # Print the first 500 characters of page source for debugging

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html_content, "html.parser")

songs_data = []

# Check if the target elements are present
entries = soup.find_all('ytmc-entry-row')
if entries:
    print(f"Found {len(entries)} song entries, extracting data...")
else:
    print("No song entries found. The page may not have loaded correctly.")

# Iterate through all song entries
for entry in entries:
    song_info = {}

    # Extract rank
    rank_tag = entry.find('span', {'id': 'rank'})
    if rank_tag:
        song_info['rank'] = rank_tag.text.strip()

    # Extract song title
    title_tag = entry.find('div', {'id': 'entity-title'})
    if title_tag:
        song_info['title'] = title_tag.text.strip()

    # Extract singer's name
    artist_tag = entry.find('span', {'class': 'artistName'})
    if artist_tag:
        song_info['artist'] = artist_tag.text.strip()

    # Extract distribution date
    date_tag = entry.find('div', {'class': 'metric content center style-scope ytmc-entry-row'})
    if date_tag:
        song_info['distribution_date'] = date_tag.text.strip()

    # Extract producer name
    producer_tag = entry.find('span', string='הפקה')
    if producer_tag and producer_tag.find_next('span'):
        song_info['producer'] = producer_tag.find_next('span').text.strip()

    # Add source
    song_info['source'] = 'youtube-trend30'  # Static source for scraper2

    # Add the song info to the list
    songs_data.append(song_info)

# Send each song data to SQS
for song in songs_data:
    send_to_sqs(song)

# Close the browser when done
driver.quit()

logging.info("Scraping and sending to SQS completed.")
