#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 1 ######
import pandas as pd
import requests
import requests_cache
import json
import os
import util

requests_cache.install_cache('demo_cache')


pd.set_option('display.max_colwidth', -1)

# dataset for 1 trail
# q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
# ql = {'data':q}
# mich = requests.get('https://overpass-api.de/api/interpreter', params=ql)

# Gets whole dataset for state of Michigan
def getturbojson(area="MI"):
	
	# TODO: implement in util
	# areacode = util.getArea(area)
	areacode = '3600165789'
	query = '[out:json][timeout:25];area({})->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'.format(areacode)
	pckg = {'data':query}
	outs = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	geoJelements = json.loads(outs.text)['elements']

	# Filter objects by type
	for element in geoJelements:
		returnDict = {}
		# print(element)
		nodes, ways, relations, other = [], [], [], []
		if element['type'] == "node":
			nodes.append(element)
		elif element['type'] == "way":
			nodes.append(element)
		elif element['type'] == "relation":
			nodes.append(element)
		else:
			other.append(element)

	# Enter into dataframes
	rel_df = pd.DataFrame(relations)
	way_df = pd.DataFrame(ways)
	nod_df = pd.DataFrame(nodes)

	returnDict['rel_df'] = rel_df
	returnDict['way_df'] = way_df	
	returnDict['nod_df'] = nod_df

	return returnDict
	# return rel_df

elementDict = getturbojson()
print(elementDict['nod_df'].head())

	
# rel['start_way'] = rel.apply(get_coords, axis=1)
# # rel['end_way'] = rel.apply(get_end_node, axis = 1)

'''
1. for each relation, get first and last way ID's
2. for first way ID, get first node , for last way ID get last node
3. profit
'''

# class Trail(self, 
# 			id=id_int, 
# 			lat=lat_int, 
# 			lon=lon_int 
# 			tags=tags, 
# 			type=type):




