# Usage: python crawl_secondhandsongs.py [FIRST_INDEX] [LAST_INDEX]

import requests
from bs4 import BeautifulSoup
from time import sleep
from random import choice
import sys

# First and last indices to query
FIRST_INDEX = int(sys.argv[1])
LAST_INDEX = int(sys.argv[2])

# To get a table of all versions of a work, request BASE_URL + id + "/versions"
BASE_URL = "https://secondhandsongs.com/work/"

# Path to data directory
SAVE_DIR = "data/secondhandsongs/"

# List of headers to spoof
headers = ["Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0",
          "Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
          ]

# Counter for how many works explored (non-error pages)
counter = 0

for i in range(FIRST_INDEX, LAST_INDEX + 1):  
    try:
        current_url = BASE_URL + str(i) + '/versions'

        session = requests.Session()

        # Spoof a random header
        session.headers.update({'User-Agent': choice(headers)})
        page = session.get(current_url)

        # Sleep for 4 seconds to avoid overloading the server
        sleep(4)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Check whether the work actually exists
        # jumbotron pops up if the work does not
        work_exists = not soup.find(class_="jumbotron")

        # Write html to file if work exists
        if work_exists:
            with open(SAVE_DIR + str(i) + '.html', 'w') as file:
                file.write(str(soup))

            counter += 1
            print "Count of works successfully scraped:", counter
            print "Current index:", i
        else:
            print i, "DOES NOT EXIST"
    except:
        # Sleep for just over an hour if blocked by server
        print "Request Failure: Sleeping for an hour..."
        sleep(60 * 61)
