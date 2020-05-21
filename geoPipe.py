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
import psycopg2 as pg
#from shapely.geometry import Polygon
import geopandas

## Add ability to collect user input


## HELPFUL UTILITY FUNCTIONS ##
import util
import config

# WAYLIMIT = 100
# requests_cache.install_cache('demo_cache')

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100000)
pd.set_option('display.width', 1000)


# CONFIGURATION VALUES

MIN_PATH_DIST_METERS = 200
MAX_REPAIR_DIST_METERS = 150
BUS_RADIUS_METERS = 800
LOOP_COMPLETION_THRESHOLD_METERS = 20

# Test region queries here: https://nominatim.openstreetmap.org/search.php
REGION = "Southeast Michigan" # Good for testing since its small
## specify country in cases where multiple same-named regions exist
COUNTRY = ""

TYPE = "foot" # foot or bicycle
where_query = "Park_Size_Acres>20"
# Dearborn area (SW corner) to St. Claire Shores (NE corner)
geometry_query = "-83.280879,42.268401,-82.806811,42.659880" 

POLYGON_SIMPLIFICATION_THRESHOLD = 0.0004

# History:
# Park_Size_Acres>5+AND+Park_Size_Acres<10 ... offset: 25

# ArcGIS UI for API

# https://server3.tplgis.org/arcgis3/rest/services/ParkServe/ParkServe_Shareable/MapServer/0/query?where=Park_Size_Acres+%3E+5+AND+Park_Size_Acres+%3C+10&text=&objectIds=&time=&geometry=-83.280879%2C42.268401%2C-82.806811%2C42.659880&geometryType=esriGeometryEnvelope&inSR=%7B%22wkid%22+%3A+4326%7D&spatialRel=esriSpatialRelEnvelopeIntersects&relationParam=&outFields=Park_Name%2CPark_Local_Owner%2CPark_Local_Manager%2CPark_Size_Acres&returnGeometry=true&returnTrueCurves=true&maxAllowableOffset=&geometryPrecision=&outSR=%7B%22wkid%22+%3A+4326%7D&having=&returnIdsOnly=false&returnCountOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=true&returnM=false&gdbVersion=&historicMoment=&returnDistinctValues=false&resultOffset=1&resultRecordCount=500&queryByDistance=&returnExtentOnly=false&datumTransformation=&parameterValues=&rangeValues=&quantizationParameters=&f=html

#################

# type must be "bicycle" or "foot"
def getOSMQueryByPolygon(type, polygon, min_path_dist_meters):
	if type == 'foot': 
		return '[out:json][timeout:1000]; \
			(\
				way["highway"~"path|footway|footpath|bridleway"]\
				["footway"!~"sidewalk|crossing"] \
				["bicycle"!~"yes|designated"]\
				(poly:"{}");\
			);(._;>;);out;'.format(polygon)

	if type == 'bicycle':
		return '[out:json][timeout:25]; \
			(\
				way["highway"~"path|footway|footpath|bridleway"]\
				["footway"!~"sidewalk|crossing"]\
				["bicycle"~"yes|designated"]\
				(poly:"{}");\
				way["highway"~"cycleway"]\
				(poly:"{}");\
			);(._;>;);out;'.format(polygon, polygon)
	
	raise Exception("Invalid type parameter value")

# type must be "bicycle" or "foot"
def getOSMQueryByRegion(type, region_code, min_path_dist_meters):
	# #osmfilter $FILE_NAME.osm --keep="type=way highway=path highway=footpath route=hiking route=foot" --drop="footway=sidewalk" > $FILE_NAME-trails.osm

	# Example queries in: https://docs.google.com/document/d/17dRRiEn9U41Q7AtO6giAw15deeOHq9nOL1Pn1wWWSJg/edit?usp=sharing

	# TRY BBOX: (-83.27293,42.35854,-83.09097,42.29509)
	# maxsize: 2073741824 = big (2074 MB)
	# maxsize: 536870912 = Overpass default maxsize (536 MB)
	# For much more conservative, add: ["name"~"trail|Trail|Hiking|hiking"]
	
	if type == 'foot': 
		return '[out:json][timeout:3000][maxsize:2073741824]; \
			area({})->.searchArea; \
			(\
				way["highway"~"path|footway|footpath|bridleway"]\
				["footway"!~"sidewalk|crossing"] \
				["bicycle"!~"yes|designated"]\
				(if:length() > {})\
				(area.searchArea);\
			);(._;>;);out;'.format(region_code, str(min_path_dist_meters))


	# @todo:
	# Extract values from "surface" tag and publish (what happens when multiple are stitched together?)
	if type == 'bicycle':
		return '[out:json][timeout:25]; \
			area({})->.searchArea; \
			(\
				way["highway"~"path|footway|footpath|bridleway"]\
				["footway"!~"sidewalk|crossing"]\
				["bicycle"!~"yes|designated"]\
				(if:length() > {})\
				(area.searchArea);\
				way["highway"~"cycleway"]\
				(if:length() > {})\
				(area.searchArea);\
			);(._;>;);out;'.format(region_code, str(min_path_dist_meters), str(min_path_dist_meters))
	
	raise Exception("Invalid type parameter value")


## IN: nothing, yet, will add parameters
## Out: nodeID, begin_lat, begin_lon, end_lat, end_lon
def queryOSM(query):
	"""Sends a get request to OSM servers > response

	Args:
		state: state to feed to util.get_state_area which returns OSM polygon of U.S. state

	Returns:
		list of elements returned from OSM
	"""

	pckg = {'data':query}
	r = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	try:
		osmResponse = json.loads(r.text)
		osmElements = osmResponse['elements']
		return osmElements
	except Exception as e:
		print(r.text)
		raise Exception("Overpass API query failed: likely API limit exceeded or server too busy, please try again later")

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

	# if DEBUG_MODE == True:
	# 	print('splitElements returned \n' + 
	# 		str(len(ways)) + " ways, " + str(len(nodes)) + " nodes, and " 
	# 		+ str(len(garbage)) + " bad elements")

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


def ways_to_trails(way_df, trail_list, MAX_REPAIR_DIST_METERS):
	# print("ways left = " + str(len(way_df)))
	''' once we have finished creating the trail_list, return'''

	''' if we have exhausted all ways in way_df, we are done, return way_df and trail_list ''' 
	if len(way_df) == 0:
		'''last time, exit'''
		# print("completely done")
		return(way_df, trail_list)

	''' pick a way from way_df to create a trail from'''
	trail_start_way = way_df.iloc[0]
	trail_name = trail_start_way['name']
	trail_id = trail_start_way.id

	'''a deque object is a list that can be prepended to'''
	trail_obj = deque([trail_start_way.nodes])
	trail_tags = deque([trail_start_way.tags])


	''' remove start way from way_df ''' 
	way_df = way_df[way_df.id != trail_start_way.id]
	
	# print("repairing ways on trail: " + trail_name)
	# print("starting with way_id " + str(trail_id))

	''' set method to empty so while loop runs''' 
	method = ''
	# print("entering while loop")
	# if method == 'no close ways':

		# print("now entering while loop")
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

		''' iterate through list of ways sharing a trail name, at the end of the loop you should have:
		    a repair method, a closest_way, and a repair_distance for the nearest way in the list'''
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

		# Using the method and closest_way determined in the loop thru ways_with_trail_name, perform the given 
		# append/prepend on the trail_obj, then remove the way appended/prepended from the way_df
		# if no close ways were found in the for loop, the method will remain blank. In this case, set the method to
		# 'no close ways' so that the while loop will exit
		if method == '':
			method = 'no close ways'

		if method == 'prepend':
			trail_obj.appendleft(closest_way.nodes)
			trail_tags.appendleft(closest_way.tags)
			'''remove used way from way_df'''
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))

		elif method == 'append':
			trail_obj.append(closest_way.nodes)
			trail_tags.append(closest_way.tags)
			'''remove used way from way_df'''
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))

		elif method == 'prepend_inverted':
			closest_way.nodes.reverse()
			trail_obj.appendleft(closest_way.nodes)
			trail_tags.appendleft(closest_way.tags)
			'''remove used way from way_df'''
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))

		elif method == 'append_inverted':
			closest_way.nodes.reverse()
			trail_obj.append(closest_way.nodes)
			trail_tags.append(closest_way.tags)
			'''remove used way from way_df'''
			way_df = way_df[way_df.id != closest_way.id]
			# print(method + " way " + str(closest_way.id))
		# print("\n")

	# once the while loop has exited (no close ways have been found for the trail selected in the beginning), 
	# append the trail_obj to a list of trails
	trail_list.append({
		'id': trail_id,
		'name': trail_name,
		'trail_obj': trail_obj,
		'tags': trail_tags})

	# finally, if way_df still contains items, call ways_to_trails again with the new way_df and trail_list
	return(ways_to_trails(way_df, trail_list, MAX_REPAIR_DIST_METERS))




def to_db(trail_df, region_code, tablename, schema=""):
	'''Args: trail_df
	Returns: Bool, if False, nothing happened or something went wrong.
	Does: stringifies trail_df, then checks database for trails with region code. 
	If they are found, delete all trails with this region code.
	If no trails for a given region, append to database. 
	'''
	# if schema: 
	# 	schema = schema + "."
	# 	use_schema = True
	region_code = str(region_code)
	trail_df = trail_df.applymap(lambda x: str(x))

	if schema:
		schema = schema + "."

	# Initialize the engine
	try: 
		username = config.username
	except Exception as e:
		print("populate config.py with the required database info")
	engine = create_engine('postgresql://'+ config.username +':'+config.password+'@'+ \
			config.host+':'+'5432'\
			+'/'+'totago',echo=False)
	conn = engine.connect()
	#print("engine initialized")

	# Does table exist?
	table_exists = engine.has_table(tablename)
	if table_exists:
		statement = "SELECT * FROM {}{}".format(schema, tablename)
		results = [result for result in conn.execute(statement)]
		if len(results) == 0:
		# if table exists but is empty, go ahead and remove it so that it can be properly initialized 
		# with to_sql
			statement = "DROP TABLE IF EXISTS {}{}".format(schema, tablename)
			table_exists = False
	#print("table exists = " + str(table_exists))

	if not table_exists:
		trail_df.to_sql(name=tablename, con=conn, if_exists='append', index=False)
		print("table {} created with trails for region: {}".format(tablename, str(region_code)))
		return 1


	# do we already have trails for the given region_code?
	
	statement = "SELECT * FROM {}{} WHERE region_code = '{}'".format(schema, tablename, region_code)
	results = [r for r in conn.execute(statement)]
	if len(results) == 0:
		existing_trails = False
	else:
		existing_trails = True

	print("trails exist = " + str(existing_trails))



	# if we already do, delete them, append the new ones
	if existing_trails:
		statement = "DELETE FROM {}{} WHERE region_code = '{}'".format(schema, tablename, region_code)
		conn.execute(statement)
		print("deleted existing trails for region: " + str(region_code))

	trail_df.to_sql(name=tablename, con=conn, if_exists='append', index=False)
	print("new trails added for region: " + str(region_code))

	# data = pd.read_sql('SELECT * FROM {}'.format(tablename), engine)
	# print(data)

	return 1

def add_osm_trails_within_polygon(polygon, region_code):

	print("\nquerying ways from OSM")

	# 1a. query OSM by region
	#region_code = util.get_region_code(REGION, COUNTRY)
	#osmQuery = getOSMQueryByRegion(TYPE, region_code, MIN_PATH_DIST_METERS)
	#osmElements = queryOSM(osmQuery)

	# 1b. query OSM by polygon
	osmQuery = getOSMQueryByPolygon(TYPE, polygon, MIN_PATH_DIST_METERS)
	osmElements = queryOSM(osmQuery)

	# Must have at least 2 ways
	if util.count_ways(osmElements) <= 1:
		return 0

	# 3. split OSM elements into ways and nodes
	print("\nsplitting elements")
	ways_and_nodes = splitElements(osmElements)
	ways = ways_and_nodes[0]
	nodes = ways_and_nodes[1]

	way_df = pd.DataFrame(ways)
	node_df = pd.DataFrame(nodes)

	# 4. get all nodes lat and lon for each way
	print("\ninjecting node coordinates into ways")
	way_df = way_df.progress_apply(injectNodes, node_df=node_df, axis=1)

	# 5. name each trail
	print("\nnaming trails")
	way_df = way_df.progress_apply(util.get_name, axis=1)

	# 6. Form new dataframe of trails, repair the ways within them
	print("\nconverting ways to trails, this may take a while...")
	trail_df_initial = []
	trail_df_list = ways_to_trails(way_df, trail_df_initial, MAX_REPAIR_DIST_METERS)[1]
	trail_df = pd.DataFrame(trail_df_list)

	# 7. Add column with region code, Add column with region name
	# trail_df = trail_df.apply(util.pop_region, args=(REGION, COUNTRY), axis=1)
	print("\nAdding columns for region code and region name")
	trail_df['region_code'] = region_code
	if COUNTRY != "":
		trail_df['region_name'] = str(REGION) + ", " + str(COUNTRY)
	else:
		trail_df['region_name'] = str(REGION)

	trail_df['region_name'] += "_" + TYPE

	# 8. Get geoJSON objects for each trail
	print("\nconverting to geoJSON LineString")
	trail_df = trail_df.apply(util.get_MultiLineString, axis=1)
	print("\nconverting to geoJSON MultiLineString")
	trail_df = trail_df.apply(util.get_LineString, axis=1)


	# 9. Encode polyline
	print("\nencoding polyline")
	trail_df = trail_df.progress_apply(util.get_polyline, axis=1)

	# 10. Repair tags
	#print("\nrepairing tags")
	#trail_df = trail_df.apply(util.repair_tags, axis=1)

	# 11. Get trail endpoints
	print("\ngetting trail endpoints")
	trail_df = trail_df.apply(util.pop_endpoints, axis=1)

	# 12. Calculate distance of trail (using LineString)
	print("\ncalculating trail distances")
	trail_df = trail_df.progress_apply(util.get_distance, axis=1)

	# 13. Determine trail shape
	print("\ndetermining trail shape")
	trail_df = trail_df.apply(util.is_loop, args=(LOOP_COMPLETION_THRESHOLD_METERS, ), axis=1)

	# 14. Find bus stops
	#print("\nfinding bus stops")
	#trail_df = trail_df.progress_apply(util.get_bus, args=(BUS_RADIUS_METERS, ), axis=1)

	# print(trail_df.columns)
	# print(trail_df)

	# 15. Insert trails into database
	print("\nUploading to DB")
	tablename = 'destinations_osm'
	schema = 'public'
	to_db(trail_df, region_code, tablename, schema)

	return len(trail_df)
	

def main():

	sys.setrecursionlimit(10000)

	""" Executes pipeline logic
	Process:
			1) queries OSM 
			2) splits OSM elements by type (way or node), then creates dataframes for each
			3) For each node in each way, replace the node ID with an dict object of: ID, lat, lon
			4) Names each trail from tags
	"""
	print("Requesting trails for {}".format(REGION))


	# tqdm means "progress" in Arabic, this guy wraps iterables and predicts the time it'll take to run. 
	# Because we're doing all our transformations with cython functions, we dont need to touch code in the functions
	# to change tqdm's behavior. 
	tqdm.pandas()
	
	#parks_geojson_raw = util.get_parks_geojson()

	total_features = 0
	num_features = 1
	offset = -1
	while num_features > 0:
		offset += 1

		query_url = "https://server3.tplgis.org/arcgis3/rest/services/ParkServe/ParkServe_Shareable/MapServer/0/query?where=" + where_query + "&text=&objectIds=&time=&geometry=" + geometry_query + "&geometryType=esriGeometryEnvelope&inSR=%7B%22wkid%22+%3A+4326%7D&spatialRel=esriSpatialRelEnvelopeIntersects&returnGeometry=true&returnTrueCurves=false&outSR=%7B%22wkid%22+%3A+4326%7D&f=geojson&resultRecordCount=1&resultOffset=" + str(offset)

		print(query_url)

		parks_geojson = geopandas.read_file(query_url)

		num_features = len(parks_geojson.index)
		if num_features == 0:
			break

		
		# OLD envelop approach
		#envelope_coords = parks_geojson.envelope.geometry.apply(util.coord_lister)[0]
		
		park_name = parks_geojson.Park_Name[0]

		if parks_geojson.geometry.type[0] == "Polygon":
			parks_geojson_simplified = parks_geojson.geometry.simplify(POLYGON_SIMPLIFICATION_THRESHOLD)
			parks_geojson_simplified_coords = parks_geojson_simplified.geometry.apply(util.coord_lister)[0]
			polygon = util.get_osm_polygon_string(parks_geojson_simplified_coords)
			total_features += add_osm_trails_within_polygon(polygon, park_name)

		elif parks_geojson.geometry.type[0] == "MultiPolygon":
			polygons = parks_geojson.geometry[0]

			# Iterate over each polygon
			park_polygon_index = 0
			for cur_polygon in polygons:
				region_code = park_name + "_" + str(park_polygon_index)
				park_polygon_index += 1

				parks_geojson_simplified = cur_polygon.simplify(POLYGON_SIMPLIFICATION_THRESHOLD)

				# For debugging: output GeoJSON string
				# util.get_polygon_geojson_from_multipolygon(parks_geojson_simplified)

				polygon = util.get_osm_polygon_string_from_multipolygon(parks_geojson_simplified)
				total_features += add_osm_trails_within_polygon(polygon, park_name)

		else:
			raise "Unknown geometry type: " + parks_geojson.geometry.type[0]
		
		print("found " + str(total_features) + " trails so far")
		

	print("found total of " + str(total_features) + " trails in " + REGION)






if __name__ == '__main__':

	main()

