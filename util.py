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

import config
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




# def get_region_code(state_full_name, country_full_name="", base_code = 3600000000):
# 	if country_full_name != "":
# 		params = {"state": state_full_name,
# 				  "country": country_full_name,
# 				  "format": "json"
# 				 }
# 	else:
# 		params = {"state": state_full_name,
# 				  # "country": country_full_name,
# 				  "format": "json"
# 				 }
# 	url = "https://nominatim.openstreetmap.org/search?"
# 	try:
# 		r = requests.get(url, params = params)
# 		text = json.loads(r.text)[0]
# 		code = base_code+text["osm_id"]
# 		return code
# 	except Exception as e:
# 		print(e)
# 		print("\n\n\n\nNominatim API limit reached, wait 15 minutes and try again\n\n\n\n")
# 	return None

# This one uses MapQuests API

def get_region_code(state_full_name, country_full_name="", base_code = 3600000000):

	if country_full_name != "":
		params = {"state": state_full_name,
				  "country": country_full_name,
				  "format": "json"
				 }
	else:
		params = {"state": state_full_name,
				  # "country": country_full_name,
				  "format": "json"
				 }

	params['key'] = config.mapQuestKey
	url = "http://open.mapquestapi.com/nominatim/v1/search.php"
	# try:
	r = requests.get(url, params = params)
	text = json.loads(r.text)[0]
	code = base_code+int(text["osm_id"])
	return code
	# except Exception as e:
	# 	print(e)
	# 	print("\n\n\n\nNominatim API limit reached, wait 15 minutes and try again\n\n\n\n")


# def pop_region(c, region, country=""):
# 	'''
# 	Args: 
# 		- c iterable representing a row
# 		- region
# 		- country (optional)
# 	Returns:
# 		- new column "Region" with the region code for each trail
# 	'''
# 	code = get_region_code(region, country)
# 	c['region_code'] = code
# 	return c

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
	for node in list(chain.from_iterable(c['trail_obj'])):
		nodes.append((float(node['lat']), float(node['lon'])))
	c['polyline'] = polyline.encode(nodes, precision)
	return c

def get_LineString(c):
	'''
	Args: c iterable
	'''
	ls_geoJSON = {"type":"LineString", "coordinates": []}
	# make LineString
	for node in list(chain.from_iterable(c["trail_obj"])):
		ls_geoJSON["coordinates"].append([node["lon"], node["lat"]])
	c["LineString"] = ls_geoJSON
	return c

def get_MultiLineString(c):
	'''
	Args: c iterable
	'''
	mls_geoJSON = {"type":"MultiLineString", "coordinates": []}
	# make MultiLineString
	for way in list(c['trail_obj']):
		way_coords = []
		for node in way: 
			way_coords.append([node["lon"], node["lat"]])
		mls_geoJSON["coordinates"].append(way_coords)

	c["MultiLineString"] = mls_geoJSON
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
			begin_lat = pair[0][1]
			begin_lon = pair[0][0]
			end_lat = pair[1][1]
			end_lon = pair[1][0]

			length = length + distance((begin_lat, begin_lon), (end_lat, end_lon)).meters


		c['trail_distance_meters'] = length
		# print("worked")
	except Exception as e: 
		print("distance calculation encountered error: " + str(e) + "on trail: " + str(c))
		pass
	return c

def get_elevation(c):
	'''
	Args: - c iterator object
	Returns: column with the elevation change of each trail
	'''
	dist = c['trail_distance_meters']
	polyline = c['polyline']
	thru_hike = c['thru_hike']
	pass
	return c





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
	return distance((node1['lat'], node1['lon']), (node2['lat'], node2['lon'])).meters


def pop_endpoints(c):
	'''for each trail, create columns trail_start and trail_end
	args: c iterator object
	returns: row with 2 new columns
	'''
	trail_start = c['trail_obj'][0][0]
	trail_end = c['trail_obj'][-1][-1]

	c['trail_start'] = {'lat':trail_start['lat'], 'lon':trail_start['lon']}
	c['trail_end'] = {'lat':trail_end['lat'], 'lon':trail_end['lon']}
	return c

def is_loop(c, stretch_distance):
	if c['trail_start']['lat'] == c['trail_end']['lat'] and c['trail_start']['lon'] == c['trail_end']['lon']:
		c['thru_hike'] = True
	else:
		if distance((c['trail_start']['lat'], c['trail_start']['lon']), (c['trail_end']['lat'], c['trail_end']['lon'])).meters < stretch_distance:
			c['thru_hike'] = True
			#print('Incomplete Loop') # Debugging
		else:
			c['thru_hike'] = False
			#print('Out-and-Back') # Debugging
	return c

# Make sure each list of bus stops is sorted by proximity to trail endpoint.
def get_bus(c, bus_radius):
	c['bus_stops'] = []

	head_query = 'http://transit.land/api/v1/stops?lon={}&lat={}&r={}'.format(str(c['trail_start']['lon']),str(c['trail_start']['lat']), str(bus_radius))
	head_json = json.loads(requests.get(head_query).text)
	if len(head_json['stops']) > 0:
		c['bus_stops'] = [(t['geometry']['coordinates'][0],t['geometry']['coordinates'][1]) for t in head_json['stops'][:2]]
	tail_query = 'http://transit.land/api/v1/stops?lon={}&lat={}&r={}'.format(str(c['trail_end']['lon']),str(c['trail_end']['lat']), str(bus_radius))
	tail_json = json.loads(requests.get(tail_query).text)
	if len(tail_json['stops']) > 0:
		# print("found bus end")
		if len(tail_json['stops']) > len(head_json['stops']):
			c['bus_stops'] = [(t['geometry']['coordinates'][0],t['geometry']['coordinates'][1]) for t in tail_json['stops'][:2]]

	return c



	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit



