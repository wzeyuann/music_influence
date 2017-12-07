# Using cover song data from SecondHandSongs, infer transmission probabilities between artists based on 
# cover song chains
# Generates a file named 'cover_graph_prob.txt', which has a directed edge and corresponding edge probability per line
#  Ex. A directed edge from node 1 to 12 with estimated transmission probability 0.5 is written as follows:
#      1 12 0.5

import numpy as np 
import pandas as pd
import networkx as nx
from tqdm import tqdm
from collections import Counter

# Load data
covers = pd.read_csv('../data/secondhandsongs/covers.csv')

# Drop any rows with missing performer, release_date, artists
covers = covers.dropna(subset=['release_date', 'performer', 'artists'])

# Group by work id, sorting by year within each group, filtering for groups larger than just 1 version
grouped_by_id = covers.sort_values('release_date').groupby('adapted_work_id').filter(lambda x: len(x) > 1)
grouped_by_id = grouped_by_id.sort_values('release_date').groupby('adapted_work_id')

# Create graph from cover songs, drawing a directed edge from each person in the cover chain
# to the next artist that covered the song chronologically
cover_graph = nx.DiGraph()

for song, song_cover_df in tqdm(grouped_by_id):
    # Get chronological series of artists that covered the song
    artists_series = song_cover_df['artist_ids'].tolist()
    
    for i, artist in enumerate(artists_series):
        if i < len(artists_series) - 1:
            # Create lists splitting on commas since there can be multiple artists
            current_artists = artists_series[i].split(', ')
            successor_artists = artists_series[i + 1].split(', ')
            
            for current_artist in current_artists:
                for successor_artist in successor_artists:
                    cover_graph.add_edge(current_artist, successor_artist)

print "Cover graph info:"
print nx.info(cover_graph)

# Write cover graph and graph with edges reversed (for PageRank) to .txt files
nx.write_edgelist(cover_graph, '../networks/cover_graph.txt')
nx.write_edgelist(cover_graph.reverse(), '../networks/cover_graph_reversed.txt')


num_nodes = len(cover_graph.nodes())

# Initialize (dict of dict) lookup tables for counts of number of activations, accesses, estimated probabilities for each edge
num_activations = {}
num_accesses  = {}
p_hat = {}

print "Initializing dict of dicts"
for i in cover_graph.nodes():
    num_activations[i] = {}
    num_accesses[i] = {}
    p_hat[i] = {}

    for j in cover_graph.neighbors(i):
        num_activations[i][j] = 0 
        num_accesses[i][j] = 0
        p_hat[i][j] = -1

print "Iterating through cover chains"
# Iterate through cover chains
for song, song_cover_df in tqdm(grouped_by_id):
    # Get chronological series of artists that covered the song
    artists_series = song_cover_df['artist_ids'].tolist()

    # Create set of initially activated nodes
    activated = set(artists_series[0].split(', '))

    # Iterate through timesteps of cover chain
    for i in range(len((artists_series))):
        # Create lists splitting on commas since there can be multiple artists
        if i < len(artists_series) - 1:
            current_artists = artists_series[i].split(', ')
            successor_artists = artists_series[i + 1].split(', ')
            
            # Update activation count for reached artists
            for current_artist in current_artists:
                for successor_artist in successor_artists:
                    num_activations[current_artist][successor_artist] += 1
                    num_accesses[current_artist][successor_artist] += 1

                    # Add successors to activated set
                    activated.add(successor_artist)

                for v in cover_graph.neighbors(current_artist):
                    if v not in activated:
                        num_accesses[current_artist][v] += 1

    # Update access values for last timestep
    for current_artist in artists_series[-1].split(', '):
        for v in cover_graph.neighbors(current_artist):
            if v not in activated:
                num_accesses[current_artist][v] += 1

print "Calculating estimates"
# Calculate estimates for influence probabilities
for i in cover_graph.nodes():
    for j in cover_graph.neighbors(i):
        # Only estimate probability if edge was accessed
        # to avoid division by 0
        if num_accesses[i][j] != 0:
            p_hat[i][j] = num_activations[i][j] / float(num_accesses[i][j])
            # Make sure this is a valid probability
            assert(p_hat[i][j] <= 1 and p_hat[i][j] >= 0)
        else:
            print num_accesses[i][j], num_activations[i][j]

print "Writing edges with probabilities to file"
# Write edges with probabilities to .txt file
with open('../networks/cover_graph_prob.txt', 'w') as f:
    for i in cover_graph.nodes():
        for j in cover_graph.neighbors(i):
            f.write('{} {} {}\n'.format(i, j, p_hat[i][j]))


