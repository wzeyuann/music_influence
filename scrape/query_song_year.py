import pandas as pd
import discogs_client
import os
from time import sleep
from tqdm import tqdm

# Need to have credentials.py with str variable containing user token for Discogs API
from credentials import USER_TOKEN

# # Load artist info
# artists = pd.read_csv('data/allmusic/artists_cleaned.csv')
# # Drop rows with missing artist id or name
# artists = artists.dropna(subset=['name', 'id'])
# # Create lookup dictionaries between artist id and name
# id_to_name = {id : name for (id, name) in zip(artists['id'], artists['name'])}

# AUDIO_DIR = '/Volumes/thesis/audio/'

# artist_song_df = pd.DataFrame(columns=['artist_id', 'artist_name', 'song_name'])

# # Create df of artist names and song names we have audio for
# for id in os.listdir(AUDIO_DIR):
#     if int(id) in id_to_name.keys():
#         for song_name in os.listdir(AUDIO_DIR + id):
#             artist_song_df = artist_song_df.append({'artist_id': int(id), 'artist_name': id_to_name[int(id)], 'song_name': song_name.split('_')[1].split('.mp3')[0]}, ignore_index=True)
        
# artist_song_df.to_csv('data/artist_song_list.csv', index=False)

artist_song_df = pd.read_csv('../data/artist_song_list.csv')

# Add column for year
artist_song_df['year'] = None

# Initialize client
d = discogs_client.Client('HarryXueThesis/0.1', user_token=USER_TOKEN)

for index, row in tqdm(artist_song_df.iterrows()):    
    # Query Discogs API for artist and song name
    try:
        results = d.search(u'{} - {}'.format(unicode(row['artist_name'], 'utf-8'), unicode(row[u'song_name'], 'utf-8')), type='release')
        
    # Get year corresponding to first result
        if len(results) > 0:
            artist_song_df.loc[index, 'year'] = results[0].year
            
    except Exception as e:
        print 'Exception:', e
        print row['artist_name'], row[u'song_name']
    
    sleep(1)

# Save dataframe
artist_song_df.to_csv('../data/artist_song_list_years.csv', index=False)
