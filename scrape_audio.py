# -*- coding: utf-8 -*-

# Usage: python scrape_audio.py [FIRST_INDEX] [LAST_INDEX]

import numpy as np
import pandas as pd
import requests, json
from random import choice
from time import sleep
from six.moves import urllib
import ssl
from tqdm import tqdm
import os
import sys

from collections import Counter
 
ssl._create_default_https_context = ssl._create_unverified_context

# First and last indices to query
FIRST_INDEX = int(sys.argv[1])
LAST_INDEX = int(sys.argv[2])

# Directory to write scraped data to
WRITE_DIR = 'data/audio/'

# Base URL for json containing links to audio files
BASE_URL = 'https://www.allmusic.com/artist/MN{}/samples.json'

# List of headers to spoof
headers = ["Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0",
          "Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
          ]

# Read artist information
artists = pd.read_csv('data/allmusic/artists.txt', header=None, names=['name', 'url', 'active_period', 'genres', 'styles'], encoding='utf-8')

# Create list of AllMusic ids (unique identifier) for each artist
# Unique because AM has some duplicates due to slight naming differences
ids = np.unique([url.split('-mn')[-1] for url in artists['url']])
print "Number of unique ids:", len(ids)

# Iterate over artists
for i in tqdm(range(FIRST_INDEX, LAST_INDEX + 1)):
    try:
        # Sleep 4-5 seconds between requests
        sleep(choice([4,5]))
        session = requests.Session()

        # Spoof a random header
        session.headers.update({'User-Agent': choice(headers)})
        page = session.get(BASE_URL.format(ids[i]))
        
        # Only attempt to scrape if response is ok
        if page.ok:
            json_obj = json.loads(page.content.decode('utf-8'))

            # Check if there's any data for the artist
            if len(json_obj) > 0:
                # Create a directory for the artist id
                try:
                    os.makedirs(WRITE_DIR + str(ids[i]))
                except Exception as e:
                    print "Error making directory:", e

                for item in json_obj:
                    sample_url = item['sample']
                    title = item['title']

                    # Download mp3 and save to folder corresponding to artist's id
                    # Remove / from filenames since it's an illegal character
                    try:
                        urllib.request.urlretrieve(sample_url, WRITE_DIR + '{}/{}.mp3'.format(ids[i], title.encode('utf-8').replace('/', '')))
                    except Exception as e:
                        print "Error downloading and writing mp3", title.encode('utf-8'), ids[i]
        # Otherwise sleep for an hour if error is anything other than 404
        elif page.status_code != 404:
            # Sleep for just over an hour
            print "Abnormal Status Code: Sleeping for an hour..."
            print page.status_code
            sleep(60 * 61)
    except Exception as e:
        print ids[i], e
        # Sleep for just over an hour if blocked by server
        print "Request Failure: Sleeping for an hour..."
        sleep(60 * 61)
        