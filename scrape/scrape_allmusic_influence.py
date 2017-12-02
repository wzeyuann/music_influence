# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import csv
from time import sleep
from random import choice
import sys
from collections import deque

# Use Bjork's page as root (to ensure we're dealing with unicode correctly)
BASE_URL = 'https://www.allmusic.com/artist/bj%C3%B6rk-mn0000769444'

# Path to files
artist_file = "data/allmusic/artists.txt"
influence_file = "data/allmusic/influences.txt"

# List of headers to spoof
headers = ["Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0",
          "Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
          ]

artist_out = open(artist_file, 'w')
influence_out = open(influence_file, 'w')
artist_writer = csv.writer(artist_out)
influence_writer = csv.writer(influence_out)

# Explored set
explored = set()

# Place root page onto the queue
url_queue = deque([BASE_URL])

# Run Breadth First Search on musician pages
while len(url_queue) != 0:
    print "Size of queue:", len(url_queue)
    print "Artists explored:", len(explored)

    current_base_url = url_queue.popleft()
    current_url = current_base_url + '/related'

    try:
        session = requests.Session()

        # Spoof a random header
        session.headers.update({'User-Agent': choice(headers)})
        page = session.get(current_url)

        # Sleep for random number of seconds
        sleep(choice([4,5]))
        soup = BeautifulSoup(page.content.decode('utf-8'), 'html.parser')

        # Extract Name
        try:
            name = soup.find_all('h1', class_='artist-name')[0].text.strip()
        except:
            print "Name Extraction Failure", current_url
            name = "NA"

        # Extract Active Period
        try:
            active = soup.find_all('div', class_='active-dates')[0].find_all('div')[0].text
        except:
            print "Active Period Extraction Failure", current_url
            active = "NA"

        # Extract the genres associated with the musician
        try:
            genre_tags = soup.find_all('div', class_='genre')[0].find_all('div')[0]
            genres = ('|').join([genre.string for genre in genre_tags if not genre.string.isspace()])
        except:
            print "Genre Extraction Failure", current_url
            genres = "NA"

        # Extract the list of styles associated with the musician       
        try:
            style_tags = soup.find_all('div', class_='styles')[0].find_all('div')[0]
            styles = ('|').join([style.string for style in style_tags if not style.string.isspace()])
        except:
            print "Style Extraction Failure", current_url
            styles = "NA"

        # Extract the musician's influencers (musicians who were influenced him)
        try:
            influencers_list = soup.find_all('section', attrs={'class':'related influencers'})[0]\
            .find_next('ul')\
            .find_all('li')

            for influencer_item in influencers_list:
                influencer_name = influencer_item.text.strip()
                influencer_link = influencer_item.a.attrs['href']

                influence_relationship = [influencer_name.encode('utf-8'), influencer_link.encode('utf-8'), name.encode('utf-8'), current_base_url.encode('utf-8')]
                print influence_relationship
                influence_writer.writerow(influence_relationship)

                if influencer_link not in explored:
                    explored.add(influencer_link)
                    url_queue.append(influencer_link)
        except:
                print "Influencers Extraction Failure", current_url

        # Extract the musician's followers (musicians who were influenced by him)
        try:
            followers_list = soup.find_all('section', attrs={'class':'related followers'})[0]\
            .find_next('ul')\
            .find_all('li')

            for follower_item in followers_list:
                follower_name = follower_item.text.strip()
                follower_link = follower_item.a.attrs['href']

                follower_relationship = [name.encode('utf-8'), current_base_url.encode('utf-8'), follower_name.encode('utf-8'), follower_link.encode('utf-8')]
                print follower_relationship
                influence_writer.writerow(follower_relationship)

                if follower_link not in explored:
                    explored.add(follower_link)
                    url_queue.append(follower_link)
        except:
            print "Followers Extraction Failure", current_url

        influence_out.flush()


        # Write artist information
        try:
            artist_info = [name.encode('utf-8'), current_base_url.encode('utf-8'), active.encode('utf-8'), genres.encode('utf-8'), styles.encode('utf-8')]
            print artist_info
            artist_writer.writerow(artist_info)
            artist_out.flush()
        except:
            print "Failure writing artist information", current_url

    except:
        # Sleep for just over an hour if blocked by server
        print "Request Failure: Sleeping for an hour..."
        sleep(60 * 61)

    