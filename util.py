#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os


## IN: relation
## OUT: begin_lat int, begin_lon int, end_lat int, end_lon int
def get_coords(c):

	firstway_id = c['members'][0]['ref']
	print(firstway_id)

	# firstnode_id = list(wa.loc[wa['id'] == firstway_id]['nodes'])[0][0]
	# firstnode_coords = nod.loc[nod['id'] == firstnode_id]
	# begin_lat = float(firstnode_coords['lat'])
	# begin_lon = float(firstnode_coords['lon'])
	
	lastway_id = c['members'][-1]['ref']
	print(lastway_id)

	# lastnode_id = list(wa.loc[wa['id'] == lastway_id]['nodes'])[0][-1]
	# lastnode_coords = nod.loc[nod['id']==lastnode_id]
	# end_lat = float(lastnode_coords['lat'])
	# end_lon = float(lastnode_coords['lon'])
	return (begin_lat, begin_lon, end_lat, end_lon)


## IN: country, region
## OUT: Overpass region code
def getArea(country='US', region='MI'):
	'''
	Make request to overpass or wherever to retreive geo encodings.
	In the future we'll use this function to make it easier to 
	switch states and areas when querying.
	'''
	pass
