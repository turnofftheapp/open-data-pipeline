#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os
import polyline

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

## To be applied to df
## IN: row iterator object (c)
## OUT: new col w name (from relation tags)
def get_name(c):
	tags = c['tags']
	c['name'] = ""
	try:
		if "name" in tags:
			c['name'] = tags['name']
		elif "ref" in tags:
			c['name'] = tags['ref']
		else:
			c['issues'].append("no name")
	except Exception as e:
		print("get_name error, ", e, "on trail: ", c.id)
	# print("errors: ", errors)
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

def get_polyline(c, precision=5):
	nodes = []
	for node in c['nodes']:
		nodes.append((float(node['lon']), float(node['lat'])))
	c['polyline'] = polyline.encode(nodes, precision)
	return c



# def get_totago_URL(distance):
# 	url = 'https://www.totago.co/api/v1/path_stats.json?'
# 	pckg = {'path':'enc:' + 'wkcaGrnnfOEFGNEJAF?N@TAVAV?TELCLK`@M`@CJOd@IVKf@CFEHEHMLSHMDOBM?I?KAOGKIGEGIGQSi@M_@GOIKKEOCOC[EQCMMUQUSSMUAU?OBO?MAGAK?]@QBU@MBa@@c@BQFKJGNELCHAPAJ?NANARKTSTMFMDOFMJMHMPGRAL@LDZDPFf@FVBVBR@Z?V?NDd@BNDRHTFNDLBJBH?LAJ?REZCJELMNIFWDOFIDKHGHMTGNCV?RAREVCTALC^AR?LCRGVGRGLS\ENELAJ@ZBd@DZ@b@ATCTAT?RBZHTPTJPHRLPHHLJJBNBL?NCJCNBP@J@F?LBJBD@HFDFH^F`@Fh@?VAVENELS\YXIHMNGPCPERCRCNBTBVBTDZBV?Z?ZGXIRQj@MTQTMPIREJGRIRMd@EHIN[^ONSFMHQHKJGFKHGHGLCFERCPCNAJ@N?LBNDR@T?PARA\?NCFCDEDKFGFKL??cCvE??OX_@r@W^e@t@e@z@a@f@a@ROJ_@V_@RWLQDU?k@?qAC[AyABwCB}BBcC@aBCU@K?K@KBq@?e@EWCg@G]Ce@A]@U?]BOCMMKMQIOAY?ODSFOFWJUBOAMEIKGOES?YC]Es@@e@?[BSFa@Da@@WCMEKKEQ?UBM@OEQIW@q@Be@@W?ICIIMMwA}B@_HBmGU?W??dA?Po@?kA@w@?e@@e@BS@OAOGCECECKAK?m@EcACi@Ew@E{@Cm@Ao@Ac@C}@@e@Ay@Ca@Kg@KMSE}@B[?_@?U?WDMBM?OIGQCECAQGMAc@Y]Ei@K]EU?e@KSA[BMDIDS@OCE@e@?S?KBI@KHSBOFe@Ew@_@I?MEWW_@e@SMYUWKW]O]EYC_@AMKg@BG?UEc@GUAOI[G]M[YSSEG@SIYEQGK@YGSCa@GOCUFI?IB?JWHOGWU[QQGG@KCUC[O??MEWAM?WGQ@]CMB[F??KBa@CM@IBm@@MBMNM\GJODQ?o@Uc@S[Kc@UG???_@CSBO@SECK@MCY???KKk@KQ]]OWEe@Ia@M[MKQGKBMJMPIX@^@R@NAZGPCTANAL@PAVFh@Fb@D^Bb@DXB\?Z?RETG^IPCND~@Mf@ITET?`@??CbACZCv@??Ep@C`@AR?HCXEPC^?Z?V@NBJh@lAPPf@ZZ\JXJ\DZFJJBPBRBNRNXBHBb@CTAZ@ZB^Lb@L`@BVF^Tl@Vt@Pj@BNDT?NARBPHPEPGp@Ef@GXATBRJd@@VEZIXG\I^G\E^Ir@I|@AT?ZAZBLAHEPCTAV@|@@`@A^?BALE?a@?e@?c@?Y?i@BM?OCKEQKOEUCg@Aa@@Q@MAGGOQMQMKMEOCM@WBUDYJSDSDQ?MEQIOQMMQIG?k@?e@?g@@o@@u@Bc@?_@BS@SBWBU?U?[@UA[?c@?Q@MBQFKPOTQ^KTITERAZ?`@@|@?VBXA`@Af@@l@@^A`@?n@Ab@@f@?dA?d@@d@@TAd@?j@Bx@?XCj@?v@@b@?ZAXEXGZEb@Kb@E\Gd@If@Kb@IVOVU\OTULWFOHIJGLENGb@Mz@EJEHGDQJKFGLCTCPITMLc@b@w@p@q@^EY',
# 	'is_through_hike':True}
# 	r = requests.get(url, params=pckg)

# 	print(r)
# 	print(r.url)

# 	pass


	# DB Schema: https://docs.google.com/document/d/1D_bjp7f0lv7hRCPbL2rCDwIlX152Pmr9M81Dwwt-iQk/edit



