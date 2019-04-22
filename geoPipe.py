#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 2 ######
import pandas as pd
import requests
import json
import os
import math
from tqdm import tqdm
from sqlalchemy import create_engine	
from collections import deque
import sys

# import psycopg2 as pg
## Add ability to collect user input


## HELPFUL UTILITY FUNCTIONS ##
import util
import config

DEBUG_MODE = False
region = ""
MAX_REPAIR_DIST_METERS = 150
# WAYLIMIT = 100
# requests_cache.install_cache('demo_cache')

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100000)
pd.set_option('display.width', 1000)

## IN: nothing, yet, will add parameters
## Out: nodeID, begin_lat, begin_lon, end_lat, end_lon
def queryOSM(region):
	"""Sends a get request to OSM servers > response

	Args:
		state: state to feed to util.get_state_area which returns OSM polygon of U.S. state

	Returns:
		list of elements returned from OSM
	"""

	# area = util.get_state_area_id(state)

	# Query for all of michigan

	area = util.get_area_code(region)

	query = '[out:json][timeout:100][maxsize:800000000]; \
			area({0})->.searchArea; \
			(way["highway"~"path|footway|cycleway|bridleway"]\
			["name"~"trail|Trail|Hiking|hiking"] \
			(area.searchArea););(._;>;);out;'.format(area)


	# query_by_area = '[out:json][timeout:25][maxsize:800000000]; \
	# {{{geocodeArea:{0}}}}->.searchArea; (way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
	# (area.searchArea););(._;>;);out;'.format(region)
	# print("query= " + str(query_by_area))

		# Example Query from: https://docs.google.com/document/d/17dRRiEn9U41Q7AtO6giAw15deeOHq9nOL1Pn1wWWSJg/edit?usp=sharing
	# query = '[out:json][timeout:25]; \
	# 		(way["highway"~"path|footway|cycleway|bridleway"]["name"~"trail|Trail|Hiking|hiking"] \
	# 		(44.165859765893586,-84.09587860107422,44.184542868841454,-84.0657091140747););(._;>;);out;'

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


def ways_to_trails(way_df, trail_df):
	# print("ways left = " + str(len(way_df)))
	''' once we have finished creating the trail_df, return'''
	if len(trail_df) == 0:
		'''first time around'''
	if len(way_df) == 0:
		'''last time, exit'''
		# print("completely done")
		return(way_df, trail_df)

	''' pick a way from way_df to create a trail from'''
	trail_start_way = way_df.iloc[0]
	trail_name = trail_start_way['name']
	trail_id = trail_start_way.id
	''' get all the other ways with it's same name'''
	ways_with_trail_name = way_df[way_df["name"] == trail_name]

	trail_obj = deque([trail_start_way.nodes])
	trail_tags = deque([trail_start_way.tags])



	way_df = way_df[way_df.id != trail_start_way.id]
	
	# print("repairing ways on trail: " + trail_name)
	# print("starting with way_id " + str(trail_id))

	method = ''
	# print("entering while loop")
	# if method == 'no close ways':

		# print("not entering while loop")
	while method != 'no close ways':
		method = ''
		''' always allow all remaining ways of the same name to be considered '''
		ways_with_trail_name = way_df[way_df["name"] == trail_name]
		# print('ways_with_trail_name: ' + str(len(ways_with_trail_name)))
		if len(ways_with_trail_name) == 0:

			# print("no ways found with that name")
			break
		trail_start = trail_obj[0][0]
		trail_end = trail_obj[-1][-1]

		repair_dist = MAX_REPAIR_DIST_METERS
		# print("entering for loop")

		for index, way in ways_with_trail_name.iterrows():

			# print("looking at way: " + str(way.id))
			way_id = way.id
			way_nodes = [way.nodes]

			way_start = way_nodes[0][0]
			way_end = way_nodes[-1][-1]


			prepend_dist = util.get_node_distance_meters(trail_start, way_end)
			append_dist = util.get_node_distance_meters(trail_end, way_start)

			prepend_dist_inverted = util.get_node_distance_meters(trail_start, way_start)
			append_dist_inverted = util.get_node_distance_meters(trail_end, way_end)

			# print(str(prepend_dist) + " " + str(append_dist) + " " + str(prepend_dist_inverted) + " " + str(append_dist_inverted)) 

			if prepend_dist < repair_dist:
				repair_dist = prepend_dist
				method = 'prepend'
				closest_way = way
			if append_dist < repair_dist:
				repair_dist = append_dist
				method = 'append'
				closest_way = way
			if prepend_dist_inverted < repair_dist:
				repair_dist = prepend_dist_inverted
				method = 'prepend_inverted'
				closest_way = way
			if append_dist_inverted < repair_dist:
				repair_dist = append_dist_inverted
				method = 'append_inverted'
				closest_way = way

		# print("for loop done")

		if method == '':
			method = 'no close ways'

		# if method == "no close ways":

		# 	return(ways_to_trails(way_df, trail_df))
		# print("decided to use method: " + method)
		if method == 'prepend':
			trail_obj.appendleft(closest_way.nodes)
			trail_tags.appendleft(closest_way.tags)
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))

		elif method == 'append':
			trail_obj.append(closest_way.nodes)
			trail_tags.append(closest_way.tags)
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))

		elif method == 'prepend_inverted':
			closest_way.nodes.reverse()
			trail_obj.appendleft(closest_way.nodes)
			trail_tags.appendleft(closest_way.tags)
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))

		elif method == 'append_inverted':
			closest_way.nodes.reverse()
			trail_obj.append(closest_way.nodes)
			trail_tags.append(closest_way.tags)
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))
		# print("\n")

	trail_df.append({
		'id': trail_id,
		'name': trail_name,
		'trail_obj': trail_obj,
		'tags': trail_tags})
	# print(trail_df)



	# print(ways_with_trail_name)

	# print("\n")


	return(ways_to_trails(way_df, trail_df))


def main():
	sys.setrecursionlimit(5000)
	region = "Ontario"

	""" Executes pipeline logic
	Process:
			1) queries OSM 
			2) splits OSM elements by type (way or node), then creates dataframes for each
			3) For each node in each way, replace the node ID with an dict object of: ID, lat, lon
			4) Names each trail from tags
	"""
	print("Requesting trails for {}".format(region))


	# tqdm means "progress" in Arabic, this guy wraps iterables and predicts the time it'll take to run. 
	# Because we're doing all our transformations with cython functions, we dont need to touch code in the functions
	# to change tqdm's behavior. 
	tqdm.pandas()

	# 1. query OSM and get list of elements
	print("querying ways from OSM")
	osmElements = queryOSM(region)

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

	# 5. Form new dataframe of trails, repair the ways within them
	# trail_df_initial = pd.DataFrame(columns=['id', 'name', 'trail_obj', 'tags'])
	print("converting ways to trails, this may take a while...")
	trail_df_initial = []
	trail_df_list = ways_to_trails(way_df, trail_df_initial)[1]
	trail_df = pd.DataFrame(trail_df_list)


	# 7. Get geoJSON objects for each trail
	print("converting to geoJSON LineString")
	trail_df = trail_df.apply(util.get_MultiLineString, axis=1)
	print("converting to geoJSON MultiLineString")
	trail_df = trail_df.apply(util.get_LineString, axis=1)


	# 8. Encode polyline
	print("encoding polyline")
	trail_df = trail_df.progress_apply(util.get_polyline, axis=1)


	# for index,trail in trail_df.iterrows():
	# 	print(trail['name'])
	# 	print(trail['polyline'])
	# 	print(trail['LineString'])

	# 9. Repair tags
	print("repairing tags")
	trail_df = trail_df.apply(util.repair_tags, axis=1)

	# 10. Get trail endpoints
	print("getting trail endpoints")
	trail_df = trail_df.apply(util.pop_endpoints, axis=1)
	# 11. Calculate distance of trail (using LineString)
	print("calculating trail distances")
	trail_df = trail_df.progress_apply(util.get_distance, axis=1)

	# 12. Determine trail shape
	print("determining trail shape")
	trail_df = trail_df.apply(util.is_loop, axis=1)

	# 13. Calculate Distance

	# 14. Calculate elevation via totago API call

	# 15. Find bus stops
	print("finding bus stops")
	trail_df = trail_df.progress_apply(util.get_bus, axis=1)

	print(trail_df.columns)
	print(trail_df)






	## Make sure everything is double quotes for geoJSON

	# Final. Insert everything into database
	# Convert all types to string, makes db insertion easier
	tablename = 'destination_' + str(location.lower())
	trail_df = trail_df.applymap(lambda x: str(x))
	print("inserting into database...")
	engine = create_engine('postgresql://'+ config.username +':'+config.password+'@'+ \
			config.host+':'+'5432'\
			+'/'+'totago',echo=False)
	con = engine.connect()
	
	trail_df.to_sql(name=tablename, con=con, if_exists = 'replace', index=False)
	data = pd.read_sql('SELECT * FROM {}'.format(tablename), engine)
	print(data)





if __name__ == '__main__':
	main()

