#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 1 ######
import pandas as pd
import requests
import requests_cache
import json
import os
import util

from pprint import pprint


DEBUG_MODE = False
# requests_cache.install_cache('demo_cache')


pd.set_option('display.max_colwidth', -1)

# dataset for 1 trail
# q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
# ql = {'data':q}
# mich = requests.get('https://overpass-api.de/api/interpreter', params=ql)

# Gets whole dataset for state of Michigan
## Out: nodeID, begin_lat, begin_lon, end_lat, end_lon
def getturbojson():
	
	# TODO: implement in util
	# areacode = util.getArea(area)
	# if DEBUG_MODE == True:
		
	areacode = '3600165789'

	# query = '[out:json][timeout:25];area({})->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'.format(areacode)
	# query = '[out:json][timeout:25];area(3600165789)->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'.format(areacode)
	# pckg = {'data':query}
	# outs = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	# geoJ = json.loads(outs.text)
	with open('geoJ.json') as f:
		geoJ = json.load(f)
		print(geoJ)

	 


	# Filter objects by type
	# geoJelements = geoJ['elements']
	# sorted_geoJ = sorted(geoJelements, key = lambda i: (i['type']))
	# pprint(geoJelements)
	# print ("\r") 

	# print(sorted_geoJ)

getturbojson()
	  
	# print(type(geoJelements))
	# print("---------------------------------------------------")
	# print(geoJelements)

















# break 
# 	for element in geoJelements:
# 		print(type(element))
# 		returnDict = {}
# 		# print(element)
# 		# nodes, ways, relations, other = [], [], [], []
# 		nodes = []
# 		ways = []
# 		relations = []
# 		other = []

# 		if element['type'] == "node":
# 			nodes.append(element)
# 		elif element['type'] == "way":
# 			ways.append(element)
# 		elif element['type'] == "relation":
# 			relations.append(element)
# 		else:
# 			other.append(element)

# 	print('nodes: ', len(nodes))
# 	print('ways: ',len(ways))
# 	print('relations: ',len(relations))


# 	# Enter into dataframes
# 	rel_df = pd.DataFrame(relations)
# 	way_df = pd.DataFrame(ways)
# 	nod_df = pd.DataFrame(nodes)

# 	return (rel_df, way_df, nod_df)
# 	# return rel_df

# stuff = getturbojson()
# rel_df = stuff[0]
# way_df = stuff[1]
# nod_df = stuff[2]

	
# # rel['start_way'] = rel.apply(get_coords, axis=1)
# # # rel['end_way'] = rel.apply(get_end_node, axis = 1)

# '''
# 1. for each relation, get first and last way ID's
# 2. for first way ID, get first node , for last way ID get last node
# 3. profit
# '''

# # class Trail(self, 
# # 			id=id_int, 
# # 			lat=lat_int, 
# # 			lon=lon_int 
# # 			tags=tags, 
# # 			type=type):




