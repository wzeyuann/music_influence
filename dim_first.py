import logging
import os
from gensim import corpora, utils
from gensim.models.wrappers.dtmmodel import DtmModel
import numpy as np
import pandas as pd
from time import time
import pickle

# Set path to dtm binary
dtm_path = "/n/home09/hxue/dtm/dtm/dtm"
# Get paths to bow directories for each artist
BOW_DIR = '/n/regal/rush_lab/xue/bow_1000/'

# Model settings
NUM_TOPICS = 5
MODEL_SAVE_NAME = 'dim_bow1000_{}topics_firsttrack_songreleasedate'.format(NUM_TOPICS)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.debug("test")

# Load song info
songs = pd.read_csv('data/artist_song_list_years_cleaned.csv')

# Add a column with a ".npy" extension
songs['name_ext'] = songs['name_no_ext'].apply(lambda x: (x + '.npy')).str.decode('utf-8')

# list of (artist_id, path, year) tuples
bow_path_by_artist = []

ids_in_songs = set(songs['artist_id'])

for artist_id in os.listdir(BOW_DIR):
    song_filename = os.listdir(BOW_DIR + artist_id)[0].decode('utf-8')
    
    # Check if song year is missing or artist is missing from song df
    if int(artist_id) in ids_in_songs and songs[songs['name_ext'] == song_filename]['year'].iloc[0] != 0:
        # save (artist_id, path, year) tuple
        bow_path_by_artist.append((int(artist_id), artist_id + '/', songs[songs['name_ext'] == song_filename]['year'].iloc[0]))

print "Number of songs:", len(bow_path_by_artist)

# Order list by year
bow_path_by_artist.sort(key= lambda x: songs[songs['artist_id'] == x[0]]['year'].iloc[0])

# Create counter for number of songs for each year 
year_counter = {int(k) : 0 for k in np.unique(zip(*bow_path_by_artist)[2])}

for id, path, year in bow_path_by_artist:
    year_counter[year] += 1

# Lookup table for time_slice index v. year
time_slice_dict = {idx : year for (idx, year) in enumerate(sorted(year_counter))}
# List of counts for each time slice for DIM
time_seq = [year_counter[key] for key in sorted(year_counter.keys())]

print "Count of artists per each time slice:"
print time_seq

# Save list of paths
pickle.dump(bow_path_by_artist, open(MODEL_SAVE_NAME + "bow_paths.pk", "wb" ))

class BoWCorpus(object):
    def __iter__(self, bow_path_by_artist=bow_path_by_artist):
        for artist_id, artist_path, year in bow_path_by_artist:
            # Extract features for first song in the directory
            bow = np.load(BOW_DIR + artist_path + os.listdir(BOW_DIR + artist_path)[0])
            # Convert to sparse encoding
            bow_sparse = [(idx, count) for (idx, count) in enumerate(bow) if count > 0]
            yield bow_sparse

corpus = BoWCorpus()

start = time()

model = DtmModel(dtm_path,
                 corpus,
                 time_seq,
                 num_topics=NUM_TOPICS,
                 initialize_lda=True,
                 model='fixed')

# Save model
model.save(MODEL_SAVE_NAME)

print 'Model fit in', ((time() - start) / 60.) / 60., 'hours'
