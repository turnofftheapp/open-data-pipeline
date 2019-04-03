#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os
import math
from tqdm import tqdm


## Add ability to collect user input


## HELPFUL UTILITY FUNCTIONS ##
import util

DEBUG_MODE = False
STATE = "Michigan"
# WAYLIMIT = 100
# requests_cache.install_cache('demo_cache')

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100000)
pd.set_option('display.width', 1000)

def importDNRdata(fname):
	with open('DNRdata/' + str(fname)) as f:
		data = json.load(f)
	





def main():

	importDNRdata('DNR_Michigan.geojson')

'''
	print("Requesting trails for {}".format(STATE))

	# tqdm means "progress" in Arabic, this guy wraps iterables and predicts the time it'll take to run. 
	# Because we're doing all our transformations with cython functions, we dont need to touch code in the functions
	# to change tqdm's behavior. 
	tqdm.pandas()

	# 1. query OSM and send results to df
	geoJ = queryToDf(STATE)
	geoJelements = geoJ['elements']

	geoJelements_df = pd.DataFrame(geoJelements)

	# with open('raw.txt', "w") as f:
	# 	f.write(str(geoJelements_df))
	#2. split into 3 dfs by type 
	
	print("processing response...")
	dfs = [x for _, x in geoJelements_df.groupby('type')]

	nod_df = dfs[0]
	rel_df = dfs[1]
	way_df = dfs[2]

	print(rel_df)
	print("BREAK")
	print(way_df)


	# print("found ",len(rel_df), " trails!")

	# 3. new df from rel_df, including column containing ways, nodes + their respective data, also gets geoJSON
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

	# 6. Determind shape: loop or out-and-back, get end lat and lon if loop
	trail_df = trail_df.apply(util.get_shape, axis=1)
	trail_df = trail_df.apply(util.get_trail_end, axis=1)

	# 7. Remove bad trails
	
	##criteria: no name, ways or nodes out of bounds, no tags
	
	print("removing false positives")
	trail_df = trail_df[trail_df['issues'].map(len) == 0]

	print("encoding polyline")
	trail_df = trail_df.progress_apply(util.get_polyline, axis=1)


	print("calculating distances")
	# trail_df = trail_df.progress_apply(util.get_distance, axis=1)
	print(trail_df.columns)

	print(trail_df)

	# print(trail_df.loc[31047]['geoJSON'])
'''

if __name__ == '__main__':
	main()




'''
DISCUSSION
1. Is what OSM returns geoJSON? 
2. How do we define trailstart and trailend (maybe w bustop proximity, tho we're using the default rel start and end vals)
3. How to me plot this, given the current data structure (rel_df)? 
'''



