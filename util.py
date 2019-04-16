#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os
import polyline
import math
from geopy.distance import distance, geodesic
from shapely.geometry import LineString
from collections import deque
from itertools import chain


MAX_DIST_BETWEEN_WAYS = 100
# meters

## IN: country, region
## OUT: Overpass region code
def get_state_area_id(state_full_name):
	states = {}
	state = state_full_name.lower()
	with open("us-state-relations.csv") as f:
		for line in f.readlines()[1:]:
			states[line.split(',')[1].lower()] = int(line.split(',')[2])
	return states[state]

## To be applied to df
## IN: row iterator object (c)
## OUT: new column containing presence and location of bus stop, we will use this to designate a trailhead
# def getBus(c):

# 	### ISSUE: We don't want to pay for google api, can we use transitland? 
# 	apikey = 'nice try, thief'
# 	lat = 42.7313033
# 	lon = -84.547612
# 	rad = 1000 # Meters

# 	bus_q = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?' + 'key=' + apikey + '&location=' + str(lat) + ',' + str(lon) + '&radius=' + str(rad) + '&types=bus_station'
# 	print(bus_q)

# 	bus_resp = requests.get(bus_q)
# 	bus_json = json.loads(bus_resp.text)
# 	print(bus_json)
# 	if len(bus_json['results'])>0:
# 	    print('TRANSIT-ACCESSIBLE')
# 	else:
# 	    print('NOT ACCESSIBLE')
# 	return c
	## for Sam; just implement what you did in jupyter here, then apply it in geoPipe's main method

	

## To be applied to df
## IN: row iterator object (c)
## OUT: fixes bad data
def validate_trails(c):
	c['issues'] = []
	## make sure trails that don't have tags get an empty list
	if type(c['tags']) not in [list, dict, str]:
		c['tags'] = []
		c['issues'].append("no tags")
	## make sure nodes and ways arent empty (caused by trails outside of specified geoarea)
	if c.ways == [] or c.nodes == []:
		c['issues'].append("out of bounds")
	return c


def get_name(c):
	"""creates new column name for each row of dataframe, fills with name string from tags object

	Args:
		c: cython iterator object representing each row in the trails dataframe

	Returns:
		new column with trail name
	"""
	try:
		name = c['tags']['name']
	except Exception as e: 
		print('ERROR, '+ e + "on trail: " + c)
	c['name'] = str(name)
	return c

## To be applied to df
## IN: row iterator object (c)
## OUT: new col "shape" with either "loop" or "out and back" as values
def get_shape(c):
	shape_errors = []
	c['shape'] = None
	try:
		if "out of bounds" not in c['issues']:
			fnode = c['nodes'][0]['id']
			lnode = c['nodes'][-1]['id']
			if fnode == lnode:
				c['shape'] = "loop"
			else:
				c['shape'] = "straight"
	except Exception as e:
		print("get_shape error ", e, " on trail id: ", c.id)
	return c

## To be applied to df
## IN: row iterator object (c)
## OUT: values in end_lat and end_lon for loop trails, N/A for those without.
def get_trail_end(c):
	c['end_lat'] = None
	c['end_lon'] = None
	if c['shape'] == "straight":
		c['end_lat'] = float(c['nodes'][-1]['lat'])
		c['end_lon'] = float(c['nodes'][-1]['lon'])
	return c

## FIX: take from geoJSON ***
def get_polyline(c, precision=5):
	# list(chain.from_iterable(
	nodes = []
	for node in list(chain.from_iterable(c['ways_ordered'])):
		nodes.append((float(node['lat']), float(node['lon'])))
	c['polyline'] = polyline.encode(nodes, precision)
	return c

def get_LineString(c):
	'''
	Args: c iterable
	'''
	ls_geoJSON = {"type":"LineString", "coordinates": []}
	# make LineString
	for node in list(chain.from_iterable(c['ways_ordered'])):
		ls_geoJSON['coordinates'].append([node['lon'], node['lat']])
	c['LineString'] = ls_geoJSON
	return c

def get_MultiLineString(c):
	'''
	Args: c iterable
	'''
	mls_geoJSON = {"type":"MultiLineString", "coordinates": []}
	# make MultiLineString
	for way in list(c['ways']):
		way_coords = []
		for node in way: 
			way_coords.append([node['lon'], node['lat']])
		mls_geoJSON["coordinates"].append(way_coords)

	c['MultiLineString'] = mls_geoJSON
	return c

def repair_tags(c):
	'''
	Args: c iterable
	Returns: c with 'tags' column with duplicates removed
	'''
	tag_obj = {}
	for tag in c['tags']:
		for k, v in tag.items():
			if k not in tag_obj:
				tag_obj[k] = [v]
			elif v not in tag_obj[k]:
				tag_obj[k].append(v)

	c['tags'] = tag_obj
	return c


## currently, when we generate our polyline the ways are out of order. Fix this and the distances will be ok
def get_distance(c):
	try:
	
		length = 0
		line = c['LineString']['coordinates']
		for pair in pairs(line):
			length = length + distance(pair[0], pair[1]).meters


		c['trail_distance_meters'] = length
		# print("worked")
	except Exception as e: 
		# print("distance calculation encountered error: " + str(e) + "on trail: " + str(c))
		pass
	return c




	# for node in c['nodes']:
	# 	## for geopy we need to reverse the order of the coords
	# 	multiLine.append((float(node['lat']), float(node['lon'])))
	# for line in multiLine:
	# 	length += line_length(line)
	
	# c['trail_distance_meters'] = length
	# length = 0



## borrowed from stackexchange
def line_length(line):
	"""Length of a line in meters, given in geographic coordinates

	Args:
		line: a shapely LineString object with WGS-84 coordinates

	Returns:
		Length of line in meters
	"""
	# b, a because the distance calculation requires latitude, longitude or y, x in cartesian terms
	return sum(distance(a, b).meters for (a, b) in pairs(line))


def pairs(lineString):
	"""Iterate over a list in overlapping pairs without wrap-around.

	Args:
		lst: an iterable/list

	Returns:
		Yields a pair of consecutive elements (lst[k], lst[k+1]) of lst. Last 
		call yields the last two elements.

	Example:
		lst = [4, 7, 11, 2]
		pairs(lst) yields (4, 7), (7, 11), (11, 2)

	Source:
		https://stackoverflow.com/questions/1257413/1257446#1257446
	"""
	i = iter(lineString)
	prev = next(i)
	for item in i:
		yield prev, item
		# print("TESTING")
		# print(prev, item)
		prev = item


def get_node_distance(node1, node2): 
	[x1, y1] = node1['lat'], node1['lon']
	[x2, y2] = node2['lat'], node2['lon']
	dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)  
	return dist 

def get_node_distance_meters(node1, node2):
	return distance((node1['lon'], node1['lat']), (node2['lon'], node2['lat'])).meters

def order_ways(trail_obj, way_list, flags=[]):
	''' Bring order to our lists of ways

	Args: 
		- trail_obj: list containing our first way, wrapped in a list(first way doesnt matter) 
			i.e. [[way object dict]]
		- way_list: list of lists of other ways, not in any order

	Returns: 
		- trail_obj: each time with 1 new trail appended or prepended, until entire trail_obj has been formed
		- way_list: 1 item smaller, until empty, when function exits
	'''
	# break recurse if there are no remaining unbound ways
	if len(way_list) == 0:
		flags_copy = flags
		flags = []
		return(list(trail_obj), list(way_list), flags_copy)
	
	# use deque from collections lib instead of list for more efficient appending (and prepending)
	trail_obj = deque(trail_obj)
	trail_start = trail_obj[0][0]
	trail_end = trail_obj[-1][-1]
	repair_distance = 999999 

	for way in way_list:
		flags = []

		way_start = way[0]
		way_end = way[-1]

		front_dist = get_node_distance_meters(trail_start, way_end)
		end_dist = get_node_distance_meters(trail_end, way_start)
		# if a way must be inverted
		front_dist_invert = get_node_distance_meters(trail_start, way_start)
		end_dist_invert = get_node_distance_meters(trail_end, way_end)

		if front_dist < repair_distance:
			repair_distance = front_dist
			method = 'prepend'
			winner_way = way
		if end_dist < repair_distance:
			repair_distance = end_dist
			method = 'append'
			winner_way = way
		if front_dist_invert < repair_distance:
			repair_distance = front_dist_invert
			method = 'prepend inverted'
			winner_way = way
		if end_dist_invert < repair_distance:
			repair_distance = end_dist_invert
			method = 'append inverted'
			winner_way = way
		
		if repair_distance > MAX_DIST_BETWEEN_WAYS:
			flags.append('repair gap size: '+ str(repair_distance) + " meters")

	if method == 'prepend':
		trail_obj.appendleft(winner_way)
		print(method + " way " + str(len(winner_way)))
	elif method == 'append':
		trail_obj.append(winner_way)
		print(method + " way " + str(len(winner_way)))
	elif method == 'prepend inverted':
		winner_way.reverse()
		trail_obj.appendleft(winner_way)
		print(method + " way " + str(len(winner_way)))
	elif method == 'append inverted':
		winner_way.reverse()
		trail_obj.append(winner_way)
		print(method + " way " + str(len(winner_way)))
	# else:
	# 	print("huh?")

	way_list.remove(winner_way)

	# for debug
	print("\n")
	print("running order_ways...")
	print("trail obj is size: " + str(len(trail_obj)))
	print("way obj is size: " + str(len(way_list)))
	print("trail start: " + str(trail_start) + "\ntrail end: " + str(trail_end))
	print("repair size: " + str(repair_distance) + " meters")

	return(order_ways(trail_obj, way_list, flags))



		# print(str(way) + "\n" + str(i) + "\n" + str(repair_distance))

def pop_endpoints(c):
	'''for each trail, create columns trail_start and trail_end
	args: c iterator object
	returns: row with 2 new columns
	'''
	trail_start = c['ways_ordered'][0][0]
	trail_end = c['ways_ordered'][-1][-1]

	c['trail_start'] = {'lat':trail_start['lat'], 'lon':trail_start['lon']}
	c['trail_end'] = {'lat':trail_end['lat'], 'lon':trail_end['lon']}
	return c



# with open('trail.json') as f:  
# 	way_list = json.load(f)

# trail_obj = [way_list[0]]
# way_list = way_list[1:]


# o = order_ways(trail_obj, way_list)
# print("\n")
# print(list(o[0]))
# print(list(o[1]))

# ls_geoJSON = {"type":"LineString", "coordinates": []}
# for node in list(chain.from_iterable(o[0])):
# 		ls_geoJSON['coordinates'].append([node['lon'], node['lat']])
# print(ls_geoJSON)





	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit


'''
BUGS: 
- need to fix order of lat, lon for polyline, distance, and geoJSON
- perhaps make a 2 functions that 1. accepts geoJSON and gets polyline and 2. accepts geoJSON and gets distance
- distances are ALL fucked up, need to redo this

'''

