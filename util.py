#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os

## IN: country, region
## OUT: Overpass region code
def getStateAreaId(state_full_name):
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
## OUT: new col w int elevation_gain
''' ISSUE: we still need to clarify how we determine "trail start" and "trail end"'''
def getElevation(c):
	base_url = "https://maps.googleapis.com/maps/api/elevation/json?locations="
	gKey = "AIzaSyChXIQQQrzdfeuPPFgY_RQKSQZgvXdwTV8"
	coords = []
	e_change = []
	error = []
	for way in c['members']:
		try:
			w = list(way_df.loc[way_df['id'] == way['ref']]['nodes'])
			fnode = nod_df.loc[nod_df['id']==w[0][0]]
			lnode = nod_df.loc[nod_df['id']==w[0][-1]]
			coords.append((str(fnode['lat'])+","+str(fnode['lon']), str(lnode['lat'])+","+str(lnode['lon'])))
		except Exception:
			error.append(way)
	for coord in coords:
		e1 = base_url + coord[1] + "&key=" + gKey
		e2 = base_url + coord[2] + "&key=" + gKey
		e = e1-e2
		e_change.append(e)
	return e_change

def getRoundTripDist(c):
	'''use info from shape column,
	   could use google libraries
	   once we geocode'''
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
				c['shape'] = "out and back"
	except Exception as e:
		print("get_shape error ", e, " on trail id: ", c.id)
	return c

## To be applied to df
## IN: row iterator object (c)
## OUT: values in end_lat and end_lon for loop trails, N/A for those without.
def get_trail_end(c):
	c['end_lat'] = None
	c['end_lon'] = None
	if c['shape'] == "loop":
		c['end_lat'] = float(c['nodes'][-1]['lat'])
		c['end_lon'] = float(c['nodes'][-1]['lon'])
	return c

## IN: dataframe, id of row to remove
## OUT: dataframe without removed row
def remove_trail(df, idlist):

	pass



	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit



