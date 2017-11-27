# Implementation of the greedy algorithm for influence maximization (Kleinberg et al.)
# to use on the inferred cover song network from SecondHandSongs to identify the k most
# influential artists

import networkx as nx
import numpy as np
from random import random
from tqdm import tqdm
from joblib import Parallel, delayed

def loadGraph(filename):
	'''Load in .txt file containing u v p per line as a NetworkX DiGraph
	Args:
		filename (str): name of file
	Returns:
		networkX Digraph
	'''

	G = nx.DiGraph()

	for line in open(filename, 'r'):
		u, v, p = [x for x in line.split(" ")]
		u = int(u)
		v = int(v)
		p = float(p)

		G.add_edge(u, v, weight=p)
	
	return G

def genRandGraph(weights):
	'''Return a randomly realized graph from a directed graph with weights designating
	the probability of edges realizing
	Args:
		weights : networkX DiGraph where each edge has a probability attribute
	Returns:
		Randomly realized subgraph of weights
	'''
	# Initialize subgraph
	subgraph = nx.DiGraph()

	for u,v,d in weights.edges_iter(data=True):
		# Realize each edge with probability corresponding to its weight
		if random() < d['weight']:
			subgraph.add_edge(u, v)

	return subgraph

def sampleInfluence(G, S, m):
	'''Run the sample influence algorithm to estimate the influence f(S) of S
	Args:
		G: weighted graph
		S: A list of nodes to compute influence for
		m: limit to number of samples to generate
	Returns:
		An estimate of the influence of the set S
	'''
	# Store number of reachable nodes for each sample
	R = np.zeros(m)

	for i in range(m):
		# Generate random graph
		subgraph = genRandGraph(G)

		reachable = set()

		# Calculate number of nodes reachable from any node in S in the generated subgraph
		for s in S:
			# Sometimes a node in S is not in the subgraph, in which case just pass over it
			try:
				reachable = reachable.union(nx.descendants(subgraph, s))
			except:
				pass

		R[i] = len(reachable)

	# Average the number of reachable nodes per trial to get an influence estimate
	influence_estimate = R.mean()

	return influence_estimate

def greedyAlgorithm(G, m=10, k=5):
	'''Run the greedy algorithm to estimate a set of size k to maximize influence
	Args:
		G: weighted graph
		m: limit to number of samples to generate
		k: Size of set of initial adopters
	Returns:
		A list with k members
	'''

	# With nothing in S, f(S) is 0
	# We'll append to this list as we add members to S and use this to calculate
	# the marginal contributions
	f_by_iteration = [0]
	S = []

	for i in range(k):
		# Store estimates for f(S) in a dictionary keyed by node number
		f = {}

		# Estimate f(s) for each of the nodes in the graph
		for a in tqdm(G.nodes_iter()):
			f_a = sampleInfluence(G, S + [a], m)
			f[a] = f_a

		# Add the element with the highest estimated contribution to S
		S.append(max(f, key=lambda node: f[node]))
		f_by_iteration.append(max(f.values()))
		# Print marginal contribution at each step
		print "f_S(a) at step", i + 1, "is", f_by_iteration[-1] - f_by_iteration[-2]

	return S

# Load network
print('Loading network')
G = loadGraph('../graphs/cover_graph_prob.txt')

# 5d. Pick 5 initial adopters to maximize the expected number of adoptions using the modified Greedy algorithm
print greedyAlgorithm(G, m=10, k=5)