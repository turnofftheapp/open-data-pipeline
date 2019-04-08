#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os
import polyline
import math
from geopy.distance import distance, geodesic
from shapely.geometry import LineString
from collections import deque

MAX_DIST_BETWEEN_WAYS = 99999

## IN: country, region
## OUT: Overpass region code
def get_state_area_id(state_full_name):
	states = {}
	state = state_full_name.lower()
	with open("us-state-relations.csv") as f:
		for line in f.readlines()[1:]:
			states[line.split(',')[1].lower()] = int(line.split(',')[2])
	return states[state]

## To be applied to df
## IN: row iterator object (c)
## OUT: new column containing presence and location of bus stop, we will use this to designate a trailhead
# def getBus(c):

# 	### ISSUE: We don't want to pay for google api, can we use transitland? 
# 	apikey = 'nice try, thief'
# 	lat = 42.7313033
# 	lon = -84.547612
# 	rad = 1000 # Meters

# 	bus_q = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?' + 'key=' + apikey + '&location=' + str(lat) + ',' + str(lon) + '&radius=' + str(rad) + '&types=bus_station'
# 	print(bus_q)

# 	bus_resp = requests.get(bus_q)
# 	bus_json = json.loads(bus_resp.text)
# 	print(bus_json)
# 	if len(bus_json['results'])>0:
# 	    print('TRANSIT-ACCESSIBLE')
# 	else:
# 	    print('NOT ACCESSIBLE')
# 	return c
	## for Sam; just implement what you did in jupyter here, then apply it in geoPipe's main method

	

## To be applied to df
## IN: row iterator object (c)
## OUT: fixes bad data
def validate_trails(c):
	c['issues'] = []
	## make sure trails that don't have tags get an empty list
	if type(c['tags']) not in [list, dict, str]:
		c['tags'] = []
		c['issues'].append("no tags")
	## make sure nodes and ways arent empty (caused by trails outside of specified geoarea)
	if c.ways == [] or c.nodes == []:
		c['issues'].append("out of bounds")
	return c


def get_name(c):
	"""creates new column name for each row of dataframe, fills with name string from tags object

	Args:
		c: cython iterator object representing each row in the trails dataframe

	Returns:
		new column with trail name
	"""
	try:
		name = c['tags']['name']
	except Exception as e: 
		print('ERROR, '+ e + "on trail: " + c)
	c['name'] = str(name)
	return c

## To be applied to df
## IN: row iterator object (c)
## OUT: new col "shape" with either "loop" or "out and back" as values
def get_shape(c):
	shape_errors = []
	c['shape'] = None
	try:
		if "out of bounds" not in c['issues']:
			fnode = c['nodes'][0]['id']
			lnode = c['nodes'][-1]['id']
			if fnode == lnode:
				c['shape'] = "loop"
			else:
				c['shape'] = "straight"
	except Exception as e:
		print("get_shape error ", e, " on trail id: ", c.id)
	return c

## To be applied to df
## IN: row iterator object (c)
## OUT: values in end_lat and end_lon for loop trails, N/A for those without.
def get_trail_end(c):
	c['end_lat'] = None
	c['end_lon'] = None
	if c['shape'] == "straight":
		c['end_lat'] = float(c['nodes'][-1]['lat'])
		c['end_lon'] = float(c['nodes'][-1]['lon'])
	return c

## FIX: take from geoJSON ***
def get_polyline(c, precision=5):
	nodes = []
	for node in c['nodes']:
		nodes.append((float(node['lat']), float(node['lon'])))
	c['polyline'] = polyline.encode(nodes, precision)
	return c

## currently, when we generate our polyline the ways are out of order. Fix this and the distances will be ok
def get_distance(c):
	# multiLine= []
	# length = 0
	# for lineString in c['geoJSON']['coordinates']:
	# 	length += line_length(lineString)
	# c['trail_distance_meters'] = length
	# length = 0
	pass
	# return c


	# for node in c['nodes']:
	# 	## for geopy we need to reverse the order of the coords
	# 	multiLine.append((float(node['lat']), float(node['lon'])))
	# for line in multiLine:
	# 	length += line_length(line)
	
	# c['trail_distance_meters'] = length
	# length = 0
	# return c



## borrowed from stackexchange
def line_length(line):
	"""Length of a line in meters, given in geographic coordinates

	Args:
		line: a shapely LineString object with WGS-84 coordinates

	Returns:
		Length of line in meters
	"""

	return sum(distance(a, b).miles for (a, b) in pairs(line))


def pairs(lineString):
	"""Iterate over a list in overlapping pairs without wrap-around.

	Args:
		lst: an iterable/list

	Returns:
		Yields a pair of consecutive elements (lst[k], lst[k+1]) of lst. Last 
		call yields the last two elements.

	Example:
		lst = [4, 7, 11, 2]
		pairs(lst) yields (4, 7), (7, 11), (11, 2)

	Source:
		https://stackoverflow.com/questions/1257413/1257446#1257446
	"""
	i = iter(lineString)
	prev = next(i)
	for item in i:
		yield prev, item
		# print("TESTING")
		# print(prev, item)
		prev = item

# def get_node_distance(node1, node2):
# 	if node1["id"] == node2["id"]:
# 		return 0
# 	else:
# 		node1 = (node1['lat'], node1['lon'])
# 		node2 = (node2['lat'], node2['lon'])
# 		print(int(str(distance(node1, node2))))
# 		return 0

def get_node_distance(node1, node2): 
	[x1, y1] = node1['lat'], node1['lon']
	[x2, y2] = node2['lat'], node2['lon']
	dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)  
	return dist 

def order_ways(trail_obj, way_list):
	# print(list(trail_obj))
	# print(len(trail_obj))

	# use deque from collections lib instead of list for more efficient appending (and prepending)
	trail_obj = deque(trail_obj)
	trail_start = trail_obj[0][0]
	trail_end = trail_obj[-1][-1]

	# print("trail start: " + str(trail_start) + "\ntrail end: " + str(trail_end))

	way_min_dist = MAX_DIST_BETWEEN_WAYS 

	for i, way in enumerate(way_list):


		way_start = way[0]
		way_end = way[-1]
		# print("way start: " + str(way_start) + "\nway end: " + str(way_end))

		front_dist = get_node_distance(trail_start, way_end)
		end_dist = get_node_distance(trail_end, way_start)
		# if a way must be inverted
		front_dist_invert = get_node_distance(trail_start, way_start)
		end_dist_invert = get_node_distance(trail_end, way_end)

		if front_dist < way_min_dist:
			way_min_dist = front_dist
			method = 'prepend'
			winner_way = way
		elif end_dist < way_min_dist:
			way_min_dist = end_dist
			method = 'append'
			winner_way = way
		elif front_dist_invert < way_min_dist:
			way_min_dist = front_dist_invert
			method = 'prepend inverted'
			winner_way = way
		elif end_dist_invert < way_min_dist:
			way_min_dist = end_dist_invert
			method = 'append inverted'
			winner_way = way

	if method == 'prepend':
		trail_obj.appendleft(winner_way)
	elif method == 'append':
		trail_obj.append(winner_way)
	elif method == 'prepend inverted':
		winner_way.reverse()
		trail_obj.appendleft(winner_way)
	elif method == 'append inverted':
		winner_way.reverse()
		trail_obj.append(winner_way)
	way_list.remove(winner_way)

	if len(way_list) > 0:
		print('running again')
		order_ways(trail_obj, way_list)

	return(list(trail_obj), way_list)




		# print(str(way) + "\n" + str(i) + "\n" + str(way_min_dist))






with open('trail.json') as f:  
	way_list = json.load(f)

trail_obj = [way_list[0]]
way_list = way_list[1:]

o = order_ways(trail_obj, way_list)
print("trail_obj: " + str(o[0]))
print("numways  = " + str(len(o[0])))
print("\n way_list: " + str(o[1]))


# print("before\n")
# print("trail obj: " + str(trail_obj) + "\nway_list: " + str(way_list))
# print("\nafter\n")
# print("trail obj: " + str((order_ways(trail_obj, way_list))[0]) + "\nway_list: " + str((order_ways(trail_obj, way_list))[1]))


# p = []
# for linestring in smalltrail:
# 	p.append(pairs(linestring))
# print(p)
# p = []
# for pair in pairs([[[-83.3248197, 42.6179619], [-83.326194, 42.616364], [-83.329406, 42.613143], [-83.331711, 42.610831], [-83.3324881, 42.6101564], [-83.3324563, 42.6100763], [-83.3324207, 42.6099865], [-83.3323492, 42.6098826], [-83.3326765, 42.6097874], [-83.3330192, 42.6096741], [-83.335751, 42.607295], [-83.336501, 42.606639], [-83.337241, 42.605991], [-83.3375172, 42.6057254], [-83.338312, 42.604961], [-83.3390532, 42.6042904]], [[-83.3390532, 42.6042904], [-83.3394562, 42.6039251], [-83.339836, 42.6036025], [-83.3403916, 42.6031362], [-83.3410182, 42.6026624]]]):
# 	p.append(pair)
# print(p)
# def get_totago_URL(distance):
# 	url = 'https://www.totago.co/api/v1/path_stats.json?'
# 	pckg = {'path':'enc:' + 'wkcaGrnnfOEFGNEJAF?N@TAVAV?TELCLK`@M`@CJOd@IVKf@CFEHEHMLSHMDOBM?I?KAOGKIGEGIGQSi@M_@GOIKKEOCOC[EQCMMUQUSSMUAU?OBO?MAGAK?]@QBU@MBa@@c@BQFKJGNELCHAPAJ?NANARKTSTMFMDOFMJMHMPGRAL@LDZDPFf@FVBVBR@Z?V?NDd@BNDRHTFNDLBJBH?LAJ?REZCJELMNIFWDOFIDKHGHMTGNCV?RAREVCTALC^AR?LCRGVGRGLS\ENELAJ@ZBd@DZ@b@ATCTAT?RBZHTPTJPHRLPHHLJJBNBL?NCJCNBP@J@F?LBJBD@HFDFH^F`@Fh@?VAVENELS\YXIHMNGPCPERCRCNBTBVBTDZBV?Z?ZGXIRQj@MTQTMPIREJGRIRMd@EHIN[^ONSFMHQHKJGFKHGHGLCFERCPCNAJ@N?LBNDR@T?PARA\?NCFCDEDKFGFKL??cCvE??OX_@r@W^e@t@e@z@a@f@a@ROJ_@V_@RWLQDU?k@?qAC[AyABwCB}BBcC@aBCU@K?K@KBq@?e@EWCg@G]Ce@A]@U?]BOCMMKMQIOAY?ODSFOFWJUBOAMEIKGOES?YC]Es@@e@?[BSFa@Da@@WCMEKKEQ?UBM@OEQIW@q@Be@@W?ICIIMMwA}B@_HBmGU?W??dA?Po@?kA@w@?e@@e@BS@OAOGCECECKAK?m@EcACi@Ew@E{@Cm@Ao@Ac@C}@@e@Ay@Ca@Kg@KMSE}@B[?_@?U?WDMBM?OIGQCECAQGMAc@Y]Ei@K]EU?e@KSA[BMDIDS@OCE@e@?S?KBI@KHSBOFe@Ew@_@I?MEWW_@e@SMYUWKW]O]EYC_@AMKg@BG?UEc@GUAOI[G]M[YSSEG@SIYEQGK@YGSCa@GOCUFI?IB?JWHOGWU[QQGG@KCUC[O??MEWAM?WGQ@]CMB[F??KBa@CM@IBm@@MBMNM\GJODQ?o@Uc@S[Kc@UG???_@CSBO@SECK@MCY???KKk@KQ]]OWEe@Ia@M[MKQGKBMJMPIX@^@R@NAZGPCTANAL@PAVFh@Fb@D^Bb@DXB\?Z?RETG^IPCND~@Mf@ITET?`@??CbACZCv@??Ep@C`@AR?HCXEPC^?Z?V@NBJh@lAPPf@ZZ\JXJ\DZFJJBPBRBNRNXBHBb@CTAZ@ZB^Lb@L`@BVF^Tl@Vt@Pj@BNDT?NARBPHPEPGp@Ef@GXATBRJd@@VEZIXG\I^G\E^Ir@I|@AT?ZAZBLAHEPCTAV@|@@`@A^?BALE?a@?e@?c@?Y?i@BM?OCKEQKOEUCg@Aa@@Q@MAGGOQMQMKMEOCM@WBUDYJSDSDQ?MEQIOQMMQIG?k@?e@?g@@o@@u@Bc@?_@BS@SBWBU?U?[@UA[?c@?Q@MBQFKPOTQ^KTITERAZ?`@@|@?VBXA`@Af@@l@@^A`@?n@Ab@@f@?dA?d@@d@@TAd@?j@Bx@?XCj@?v@@b@?ZAXEXGZEb@Kb@E\Gd@If@Kb@IVOVU\OTULWFOHIJGLENGb@Mz@EJEHGDQJKFGLCTCPITMLc@b@w@p@q@^EY',
# 	'is_through_hike':True}
# 	r = requests.get(url, params=pckg)

# 	print(r)
# 	print(r.url)

# 	pass


	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit


'''
BUGS: 
- need to fix order of lat, lon for polyline, distance, and geoJSON
- perhaps make a 2 functions that 1. accepts geoJSON and gets polyline and 2. accepts geoJSON and gets distance
- distances are ALL fucked up, need to redo this

'''

