#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os
import polyline

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
def getBus(c):
	## for Sam; just implement what you did in jupyter here, then apply it in geoPipe's main method
	pass

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

## To be applied to df
## IN: row iterator object (c)
## OUT: new col w name (from relation tags)
def get_name(c):
	tags = c['tags']
	c['name'] = ""
	try:
		if "name" in tags:
			c['name'] = tags['name']
		elif "ref" in tags:
			c['name'] = tags['ref']
		else:
			c['issues'].append("no name")
	except Exception as e:
		print("get_name error, ", e, "on trail: ", c.id)
	# print("errors: ", errors)
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

def get_polyline(c, precision=5):
	nodes = []
	for node in c['nodes']:
		nodes.append((float(node['lat']), float(node['lon'])))
	c['polyline'] = polyline.encode(nodes, precision)
	return c


	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit



