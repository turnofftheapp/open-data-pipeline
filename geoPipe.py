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

DEBUG_MODE = False
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
	"""Sends a get request to OSM servers > response

	Args:
		state: state to feed to util.get_state_area which returns OSM polygon of U.S. state

	Returns:
		list of elements returned from OSM
	"""

	area = util.get_state_area_id(state)

		# Query for all of michigan
	# query = '[out:json][timeout:25]; \
	# 		area({0})->.searchArea; (way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
	# 		(area.searchArea););(._;>;);out;'.format(area)
		# Query for small subset
	# query = '[out:json][timeout:25];  \
	# 		(way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
	# 		(44.14575420090964,-84.83779907226562,44.583620922396136,-84.04129028320312););(._;>;);out;'

		# Example Query from: https://docs.google.com/document/d/17dRRiEn9U41Q7AtO6giAw15deeOHq9nOL1Pn1wWWSJg/edit?usp=sharing
	query = '[out:json][timeout:25]; \
			(way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
			(44.165859765893586,-84.09587860107422,44.184542868841454,-84.0657091140747););(._;>;);out;'

	pckg = {'data':query}
	r = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	osmResponse = json.loads(r.text)
	osmElements = osmResponse['elements']
	return osmElements

def splitElements(osmElements):
	"""Splits returned OSM elements into list of ways and list of nodes

	Args:
		osmElements: list of nodes and ways returned from OSM query

	Returns:
		tuple containing (list of ways, list of nodes)
	"""
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

def group_trails(way_df):
	''' creates new dataframe, 1 row for each name contianing lists of tags and ways for each old dataframe row,
	id from first way

	'''
	new_trails = []
	trail_df = pd.DataFrame(columns=['id', 'name', 'ways', 'tags'])
	for trail_name in way_df.name.unique():
		ways_with_trail_name = way_df[way_df["name"] == trail_name]

		trail_ways = list(ways_with_trail_name.nodes)
		trail_tags = list(ways_with_trail_name.tags)
		trail_id = list(ways_with_trail_name.id)[0]

		# print("trail: " + trail_name + "\n" 
		# 	+ "ways: " + str(trail_ways) + "\n"
		# 	+ "tags: " + str(trail_tags) + "\n"
		# 	+ "id: " + str(trail_id) + "\n")
		# print("-----------------------------------------")

		new_trail = {
					'id': trail_id, 
					'name': trail_name,
					'ways': trail_ways,
					'tags': trail_tags
					}

		new_trails.append(new_trail)
	
	trail_df = pd.DataFrame(new_trails)
	return trail_df

def repair_ways(c):
	way_list = c.ways
	trail_obj = [way_list[0]]
	way_list = way_list[1:]
	o = util.order_ways(trail_obj, way_list)
	c['ways_ordered'] = o[0]
	return c


def main():
	""" Executes pipeline logic
	Process:
			1) queries OSM 
			2) splits OSM elements by type (way or node), then creates dataframes for each
			3) For each node in each way, replace the node ID with an dict object of: ID, lat, lon
			4) Names each trail from tags
	"""
	print("Requesting trails for {}".format(STATE))

	# tqdm means "progress" in Arabic, this guy wraps iterables and predicts the time it'll take to run. 
	# Because we're doing all our transformations with cython functions, we dont need to touch code in the functions
	# to change tqdm's behavior. 
	tqdm.pandas()

	# 1. query OSM and get list of elements
	print("querying ways from OSM")
	osmElements = queryOSM(STATE)

	# 2. split OSM elements into ways and nodes
	print("splitting elements")
	ways_and_nodes = splitElements(osmElements)
	ways = ways_and_nodes[0]
	nodes = ways_and_nodes[1]

	way_df = pd.DataFrame(ways)
	node_df = pd.DataFrame(nodes)


	# 3. 
	# get all nodes lat and lon for each way
	print("injecting node coordinates into ways")
	way_df = way_df.progress_apply(injectNodes, node_df=node_df, axis=1)

	# 4. name each trail
	print("naming trails")
	way_df = way_df.progress_apply(util.get_name, axis=1)
	# print(trail_df.loc[trail_df['name'] == 'Warren K. Wells Nature Trail'])

	# 5. Form new dataframe of trails
	trail_df = group_trails(way_df)

	# 6. Order ways within each trail
	print("transforming ways to trail geojsons")
	trail_df = trail_df.progress_apply(repair_ways, axis=1)

	# 7. Get geoJSON objects for each trail
	trail_df = trail_df.apply(util.get_MultiLineString, axis=1)
	trail_df = trail_df.apply(util.get_LineString, axis=1)

	# 8. Encode polyline
	trail_df = trail_df.progress_apply(util.get_polyline, axis=1)
	print(trail_df.columns)
	print(trail_df)
	# trail_df.to_csv('polyline_check_max_dist_10.csv', columns=['id', 'name', 'polyline'], index=False, header=['id', 'name', 'polyline'])

	





if __name__ == '__main__':
	main()

