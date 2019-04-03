#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 2 ######
import pandas as pd
import requests
import json
import os
import math
from tqdm import tqdm


## Add ability to collect user input


## HELPFUL UTILITY FUNCTIONS ##
import util

DEBUG_MODE = True
STATE = "Michigan"
# WAYLIMIT = 100
# requests_cache.install_cache('demo_cache')

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100000)
pd.set_option('display.width', 1000)

## IN: nothing, yet, will add parameters
## Out: nodeID, begin_lat, begin_lon, end_lat, end_lon
def queryOSM(state):

	area = util.get_state_area_id(state)

		# big query
	# query = '[out:json][timeout:25]; \
	# 		area(3600165789)->.searchArea; (way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
	# 		(area.searchArea););(._;>;);out;'
		# lil testing query
	# query = '[out:json][timeout:25];  \
	# 		(way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
	# 		(44.14575420090964,-84.83779907226562,44.583620922396136,-84.04129028320312););(._;>;);out;'

		# Example Query from: https://docs.google.com/document/d/17dRRiEn9U41Q7AtO6giAw15deeOHq9nOL1Pn1wWWSJg/edit?usp=sharing
	query = '[out:json][timeout:25]; \
			(way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
			(44.165859765893586,-84.09587860107422,44.184542868841454,-84.0657091140747););(._;>;);out;'
	## the following queries get relations, and treat relations as ways.
	# query = '[out:json][timeout:25]; area({0})->.searchArea; (way["highway"~"path|footway|cycleway|bridleway"]\
	# ["name"~"trail|Trail|Hiking|hiking"](area.searchArea);<;);(._;>;);out;'.format(area)
	# query = '[out:json][timeout:25];area(3600165789)->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'
	# query = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
	
	pckg = {'data':query}
	r = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	osmResponse = json.loads(r.text)
	osmElements = osmResponse['elements']
	return osmElements

def splitElements(osmElements):
	nodes = []
	ways = []
	garbage = []
	for element in osmElements:
		if element['type'] == 'node':
			nodes.append(element)
		elif element['type'] == 'way':
			ways.append(element)
		else:
			garbage.append(element)

	if DEBUG_MODE == True:
		print('splitElements returned \n' + 
			str(len(ways)) + " ways, " + str(len(nodes)) + " nodes, and " 
			+ str(len(garbage)) + " bad elements")

	return((ways, nodes))


def injectNodes(c, node_df):
	"""Replaces each node ID within each way's 'nodes' list with the actual node (ID, lat, lon)

	Args:
		c: an iterable cython object representing a row in a dataframe
		node_df: a dataframe of nodes

	Returns:
		new column 'nodes' containing list of nodes dicts 

	Example:
		
		[2873296545, 2873296546] 
						to
		[{'id': 2873296545, 'lat': 44.554065, 'lon': -84.619785 }, 
		{'id': 2873296546, 'lat': 44.553882, 'lon': -84.621017}]

	"""
	node_objs = []
	for node in c['nodes']:
		n = node_df.loc[node_df['id'] == node]
		node_objs.append({
			'id': int(n['id']),
			'lat': float(n['lat']),
			'lon': float(n['lon'])
			})
	c['nodes'] = node_objs
	return c

def get_name(c):
	try:
		name = c['tags']['name']
	except Exception as e: 
		print('ERROR, '+ e + "on trail: " + c)
	c['name'] = str(name)
	return c

def main():

	print("Requesting trails for {}".format(STATE))

	# tqdm means "progress" in Arabic, this guy wraps iterables and predicts the time it'll take to run. 
	# Because we're doing all our transformations with cython functions, we dont need to touch code in the functions
	# to change tqdm's behavior. 
	tqdm.pandas()

	# 1. query OSM and get list of elements
	print("querying ways from OSM")
	osmElements = queryOSM(STATE)

	#2. split OSM elements into ways and nodes
	ways_and_nodes = splitElements(osmElements)
	ways = ways_and_nodes[0]
	nodes = ways_and_nodes[1]

	way_df = pd.DataFrame(ways)
	node_df = pd.DataFrame(nodes)



	# get all nodes lat and lon for each way
	print("injecting node coordinates into ways")
	trail_df = way_df.progress_apply(injectNodes, node_df=node_df, axis=1)

	# name each trail:
	print("naming trails")
	trail_df = trail_df.progress_apply(get_name, axis=1)
	print(trail_df.columns)
	print(trail_df.loc[trail_df['name'] == 'Warren K. Wells Nature Trail'])






if __name__ == '__main__':
	main()




'''
DISCUSSION
1. Is what OSM returns geoJSON? 
2. How do we define trailstart and trailend (maybe w bustop proximity, tho we're using the default rel start and end vals)
3. How to me plot this, given the current data structure (rel_df)? 
'''



