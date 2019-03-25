#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 1 ######
import pandas as pd
import requests
import requests_cache
import json
import os
import math
from tqdm import tqdm


## HELPFUL UTILITY FUNCTIONS ##
import util
from pprint import pprint

DEBUG_MODE = False
STATE = "Michigan"
# WAYLIMIT = 100
requests_cache.install_cache('demo_cache')

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 100)

# dataset for 1 trail
# q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
# ql = {'data':q}
# mich = requests.get('https://overpass-api.de/api/interpreter', params=ql)

## IN: nothing, yet, will add parameters
## Out: nodeID, begin_lat, begin_lon, end_lat, end_lon
def queryToDf(state):

	area = util.getStateAreaId(state)
	query = '[out:json][timeout:25]; area({0})->.searchArea; (way["highway"~"path|footway|cycleway|bridleway"]\
	["name"~"trail|Trail|Hiking|hiking"](area.searchArea);<;);(._;>;);out;'.format(area)
	# query = '[out:json][timeout:25];area(3600165789)->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'
	# query = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
	pckg = {'data':query}
	r = requests.get('https://overpass-api.de/api/interpreter', params=pckg, stream=True)
	# Total size in bytes.
	total_size = int(r.headers.get('content-length', 0)); 
	block_size = 1024
	wrote = 0 

	with open('Output/queryoutput.bin', 'wb') as f:
		for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size//block_size) , unit='KB', unit_scale=True):
			wrote = wrote  + len(data)
			f.write(data)
	# if total_size != 0 and wrote != total_size:
	# 	print("ERROR, something went wrong")  

	geoJ = json.loads(r.text)
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
	# To find the type of each member, we first need to know what key is used (sometimes 'role' is used instead of 'type')
	for way in c['members']:
		if way['type'] != '':
			way_obj = way['type']
		elif way['role'] != '':
			way_obj = way['role']

	# Now, catch bad data where nodes are included in members instead of ways
	if way_obj == "node":
		errors.append((c['id'], way))

	# If the object is a way, 
	elif way_obj == "way":
		try:
			w = way_df.loc[way_df['id'] == way['ref']]
			way_id = int(w['id'])
			way_tags = list(dict(w['tags']).values())
			obj_type = str(w['type'])
			try: 
				tags = list(dict(w['tags']).values())[0]
			except Exception:
				#this only happens if there aren't tags to begin with
				tags = []
			way = {'id':way_id, 'tags':tags, 'role':obj_type}
			ways.append(way)

			for node in list(w['nodes'])[0]:
				n = nod_df.loc[nod_df['id'] == node]
				node = {'id':int(n['id']), 'lat':float(n['lat']), 'lon':float(n['lon'])}
				nodes.append(node)
		except Exception as e:
			errors.append((e, c))
			# print("way error: ", e, " on: \n")
			# print(c)
			# print("*************************")


	c['ways'] = ways
	c['nodes'] = nodes
	return c





def main():

	print("Requesting trails for {}".format(STATE))

	# tqdm means "progress" in Arabic, this guy wraps iterables and predicts the time it'll take to run. 
	# Because we're doing all our transformations with cython functions, we dont need to touch code in the functions
	# to change tqdm's behavior. 
	tqdm.pandas()

	# 1. query OSM and send results to df
	geoJelements_df = queryToDf(STATE)

	# 2. split into 3 dfs by type 
	dfs = [x for _, x in geoJelements_df.groupby('type')]
	nod_df = dfs[0]
	rel_df = dfs[1]
	way_df = dfs[2]
	print("found ",len(rel_df), " trails!")

	# 3. new df from rel_df, including column containing ways, nodes + their respective data
	print("transforming relations to trails")
	trail_df = rel_df.progress_apply(transform_members, args=(way_df, nod_df), axis=1)

	trail_df = trail_df.dropna(axis=1, how='all')
	# trail_df.to_csv(r'Output/trails.csv')

	# 4. validate trail dataframe
	print("validating trails")
	trail_df = trail_df.progress_apply(util.validate_trails, axis=1)

	# 5. name trails
	print("naming trails")
	trail_df = trail_df.progress_apply(util.get_name, axis=1)
	# print(trail_df)

	# 6. Determind shape: oop or out-and-back, get end lat and lon if loop
	trail_df = trail_df.apply(util.get_shape, axis=1)
	trail_df = trail_df.apply(util.get_trail_end, axis=1)

	# 7. Remove bad trails
	'''
	criteria: no name, ways or nodes out of bounds, no tags
	'''
	print("removing false positives")
	trail_df = trail_df[trail_df['issues'].map(len) == 0]
	print(trail_df)


if __name__ == '__main__':
	main()



'''
DISCUSSION
1. Is what OSM returns geoJSON? 
2. How do we define trailstart and trailend (maybe w bustop proximity, tho we're using the default rel start and end vals)
3. How to me plot this, given the current data structure (rel_df)? 
'''



