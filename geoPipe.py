#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 1 ######
import pandas as pd
import requests
import requests_cache
import json
import os

## HELPFUL UTILITY FUNCTIONS ##
import util
from pprint import pprint

'''TODO: Add bug testing and possibly logging features'''
DEBUG_MODE = False

requests_cache.install_cache('demo_cache')


pd.set_option('display.max_colwidth', -1)

'''
FOR ADRIAN/HENRY, BIG QUESTION: In order to do all our data processing, with a focus
								on efficiency and readability should we:

								1. Use 1 pandas dataframe, query against itself with 
								apply function? Util functions will also be applied.
												---OR---
								2. Create 3 pandas dataframes, Relations, Ways, Nodes? 
												---OR---
								3. create objects for the three types of Elements: 
								Relations, Ways, and Nodes, then inject into 
								database?
												---OR---
								4. Keep in original list of dictionary format? (eh)
'''	

# dataset for 1 trail
# q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
# ql = {'data':q}
# mich = requests.get('https://overpass-api.de/api/interpreter', params=ql)

## IN: nothing, yet, will add parameters
## Out: nodeID, begin_lat, begin_lon, end_lat, end_lon
def queryToDf():
	
	'''TODO: implement in util.py'''
	# areaid = util.getArea(area)		
	# areaid = '3600165789'

	query = '[out:json][timeout:25];area(3600165789)->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'
	pckg = {'data':query}
	outs = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	geoJ = json.loads(outs.text)
	geoJelements = geoJ['elements']

	geoJelements_df = pd.DataFrame(geoJelements)
	return geoJelements_df

##  IN: dataframe to apply function to, c is an iterator object (I think?)
## OUT: creates list of trail objects
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


## TODO: Function to split dataframes into objects of relations, ways, and nodes

class Relation:
	def __init__(self, id, tags, ways):
		pass
class Way: 
	def __init__(self, id, nodes, tags):
		pass
class Node:
	def __init__(self, id, lat, lon):
		pass

class Trail:
	def __init__(self, id, begin_lat, begin_lon, end_lat, end_lon, tags, type):


		## TODO: This will go at the end, everything in between will be operations 
		##       on the staging database. All completed utility functions will be 
		##       built in util.py
		pass

def main():
	geoJelements_df = queryToDf()
	print(geoJelements_df.head())

if __name__ == '__main__':
    main()






