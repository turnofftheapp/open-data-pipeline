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
	'''For each relation: need to eval if trail is a loop or not, then figure out how to calc dist'''
	pass






	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit



