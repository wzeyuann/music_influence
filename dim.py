import logging
import os
from gensim import corpora, utils
from gensim.models.wrappers.dtmmodel import DtmModel
import numpy as np
import pandas as pd
from time import time

# Set path to dtm binary
dtm_path = "/n/home09/hxue/dtm/dtm/main"
# Get paths to bow directories for each artist
BOW_DIR = '/n/regal/rush_lab/xue/bow_500/'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.debug("test")

# Load artist info
artists = pd.read_csv('data/allmusic/artists_cleaned.csv')

# list of (artist_id, path) tuples
bow_path_by_artist = []

for artist_id in os.listdir(BOW_DIR):
    # Check if active_start is missing
    if int(np.isnan(float(artists[artists['id'] == int(artist_id)] ['active_start']))) == 0:
        # save (artist_id, path, active_start) tuple
        bow_path_by_artist.append((int(artist_id), BOW_DIR + artist_id + '/', int(artists[artists['id'] == int(artist_id)] ['active_start'])))

# Order list by active period start for artist
bow_path_by_artist.sort(key= lambda x: int(artists[artists['id'] == x[0]] ['active_start']))

# Create counter for number of songs for each decade of active_start
decade_counter = {int(k) : 0 for k in np.unique(artists['active_start'][~np.isnan(artists['active_start'])])}

for id, path, year in bow_path_by_artist:
    decade_counter[year] += len(os.listdir(path))

# Lookup table for time_slice index v. decade
time_slice_dict = {idx : year for (idx, year) in enumerate(sorted(decade_counter))}
# List of counts for each time slice for DIM
time_seq = [decade_counter[key] for key in sorted(decade_counter.keys())]

class BoWCorpus(object):
    def __iter__(self, bow_path_by_artist=bow_path_by_artist):
        for artist_id, artist_path, year in bow_path_by_artist:
            # Stream one feature vector at a time
            for bow_file in os.listdir(artist_path):
                bow = np.load(artist_path + bow_file)
                # Convert to sparse encoding
                bow_sparse = [(idx, count) for (idx, count) in enumerate(bow) if count > 0]
                yield bow_sparse

corpus = BoWCorpus()

start = time()

model = DtmModel(dtm_path,
                 corpus,
                 time_seq,
                 num_topics=5,
                 initialize_lda=True,
                 model='fixed')

# Save model
model.save('dim_bow500')

print 'Model fit in', ((time() - start) / 60.) / 60., 'hours'