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
WAYLIMIT = 100
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
# print(rel_df.head(5))
# print(nod_df.columns)
# print(rel_df.columns)
# print(way_df.columns)

''' get start and end of every way in relation '''

## To be applied to DF:
##  IN: dataframe row object 
## OUT: list of node tuples
def transform_members(c):
	nodes = []
	error = []
	for way in c['members']:
		try:
			w = list(way_df.loc[way_df['id'] == way['ref']]['nodes'])
			fnode = nod_df.loc[nod_df['id']==w[0][0]]
			lnode = nod_df.loc[nod_df['id']==w[0][-1]]
			nodes.append((way['ref'], way['role'], fnode['lat'], fnode['lon'], lnode['lat'], lnode['lon']))
		except Exception:
			error.append(way)
	return nodes

rel_df['members'] = rel_df.apply(transform_members, axis=1)


			


def main():
	geoJelements_df = queryToDf()
	print(geoJelements_df.head())

if __name__ == '__main__':
    main()






