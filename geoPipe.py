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

'''split elements into 3 dfs'''

geoJelements_df = queryToDf()
dfs = [x for _, x in geoJelements_df.groupby('type')]
nod_df = dfs[0]
rel_df = dfs[1]
way_df = dfs[2]

print(nod_df.columns)
print(rel_df.columns)
print(way_df.columns)

''' get start and end of every way in relation '''

##  IN: dataframe to apply function to, c is an iterator object (I think?)
## OUT: creates list of trail objects
def get_coords(row):
	nodes = []
	nodinfo = []

	for way in row['members']:
		waynodes = list(way_df.loc[way_df['id'] == way['ref']]['nodes'])


		# nodes.append(way_df.iloc(way_df['id'] == way['ref'])['nodes'])

	# print(nodes)
	# print("----------")

	# firstnode_id = list(wa.loc[wa['id'] == firstway_id]['nodes'])[0][0]
	# firstnode_coords = nod.loc[nod['id'] == firstnode_id]
	# begin_lat = float(firstnode_coords['lat'])
	# begin_lon = float(firstnode_coords['lon'])
	
	# lastway_id = c['members'][-1]['ref']
	# print(lastway_id)

	# lastnode_id = list(wa.loc[wa['id'] == lastway_id]['nodes'])[0][-1]
	# lastnode_coords = nod.loc[nod['id']==lastnode_id]
	# end_lat = float(lastnode_coords['lat'])
	# end_lon = float(lastnode_coords['lon'])
	# return (begin_lat, begin_lon, end_lat, end_lon)		
	# return nodes					

# rel_df['nodes'] = rel_df.apply(get_coords, axis=1)

# rel_df.apply(get_coords, axis=1)



# print(rel_df.apply(get_coords, axis=))
# def main():
# 	geoJelements_df = queryToDf()
# 	print(geoJelements_df.head())

# if __name__ == '__main__':
#     main()






