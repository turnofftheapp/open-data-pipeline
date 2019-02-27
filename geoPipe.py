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

DEBUG_MODE = False
# WAYLIMIT = 100
requests_cache.install_cache('demo_cache')

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 10)

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
	query = '[out:json][timeout:25]; area(3600165789)->.searchArea; (way["highway"~"path|footway|cycleway|bridleway"]\
	["name"~"trail|Trail|Hiking|hiking"](area.searchArea);<;);(._;>;);out;'
	# query = '[out:json][timeout:25];area(3600165789)->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'
	# query = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
	pckg = {'data':query}
	outs = requests.get('https://overpass-api.de/api/interpreter', params=pckg)
	geoJ = json.loads(outs.text)
	geoJelements = geoJ['elements']


	geoJelements_df = pd.DataFrame(geoJelements)
	return geoJelements_df

## To be applied to DF:
##  IN: dataframe row object 
## OUT: list of nodes in relation
def transform_members(c, way_df, nod_df):
	ways = []
	nodes = []
	errors = []
	badways = []
	for way in c['members']:
		if way['type'] == "node":
			badways.append((c['id'], way))
			break
		elif way['type'] == "way":
			try:
				w = way_df.loc[way_df['id'] == way['ref']]
				way_id = 0

				way_tags = list(dict(w['tags']).values())
				role = way['role']
				try: 
					tags = list(dict(w['tags']).values())[0]
				except Exception:
					"this only happens if there aren't tags to begin with"
					tags = []
				way = {'id':way_id, 'tags':tags, 'role':role}
			# way = {'id':int(w['id']), 'tags':list(dict(w['tags']).values())[0]}
				ways.append(way)

				for node in list(w['nodes'])[0]:
					n = nod_df.loc[nod_df['id'] == node]
					node = {'id':n['id'], 'lat':n['lat'], 'lon':n['lon']}
					nodes.append(node)

			except Exception as e:
				errors.append((e, c))
				print("way error: ", e, " on: \n")
				print(c)
				print("*************************")
	c['ways'] = ways
	c['nodes'] = nodes
	return c



def main():

	# 1. query OSM and send results to df
	geoJelements_df = queryToDf()

	# 2. split into 3 dfs by type 
	dfs = [x for _, x in geoJelements_df.groupby('type')]
	nod_df = dfs[0]
	rel_df = dfs[1]
	way_df = dfs[2]
	print("found ",len(rel_df), " trails!")
	# 3. new df from rel_df, including column containing ways, nodes + their respective data
	trail_df = rel_df.apply(transform_members, args=(way_df, nod_df), axis=1)
	trail_df = trail_df.dropna(axis=1, how='all')
	print(trail_df.head())


if __name__ == '__main__':
	main()



'''
DISCUSSION
1. Is what OSM returns geoJSON? 
2. How do we define trailstart and trailend (maybe w bustop proximity, tho we're using the default rel start and end vals)
3. How to me plot this, given the current data structure (rel_df)? 

'''



