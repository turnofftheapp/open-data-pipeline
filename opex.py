### Jack Stephenson ###
## Overpass Explorer ##
###### Version 1 ######

import requests
import json
# from itertools import ifilter



'''
Resources:
- Overpass API for Python documentation [https://python-overpy.readthedocs.io/en/latest/]
- Overpass Language Guide (must learn, based on C I believe) [https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide]
- Overpass Turbo Workbench []
'''

'''
TODO:
[] discuss best data structure to use (for recursively finding start and end nodes in relations, later injecting bus stop info to nodes)
'''


## Query for one relation: "North Country Trail"
q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
ql = {'data':q}
nct = requests.get('https://overpass-api.de/api/interpreter', params=ql)

geoJlist = json.loads(nct.text)['elements']
relations = [element for element in geoJlist if element['type'] == "relation"]
ways = [element for element in geoJlist if element['type'] == "way"]
nodes = [element for element in geoJlist if element['type'] == "node"]



def get_endpoints(geoJlist):
	for rel in relations: 
		relFirstWayID = rel['members'][0]['ref']
		relLastWayID = rel['members'][-1]['ref']
		print(relFirstWayID, relLastWayID)






