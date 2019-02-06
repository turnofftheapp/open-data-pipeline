#### UMSIvsTOTAGO  ####
## Overpass Explorer ##
###### Version 1 ######
import pandas as pd
import requests
import json

pd.set_option('display.max_colwidth', -1)

# Whole dataset for Mich
q = '[out:json][timeout:25];area(3600165789)->.searchArea;relation["route"="hiking"](area.searchArea);(._;>;);out;'
ql = {'data':q}
mich = requests.get('https://overpass-api.de/api/interpreter', params=ql)

# dataset for 1 trail
# q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
# ql = {'data':q}
# mich = requests.get('https://overpass-api.de/api/interpreter', params=ql)

geoJlist = json.loads(mich.text)['elements']

nodes = [element for element in geoJlist if element['type'] == "node"]
ways = [element for element in geoJlist if element['type'] == "way"]
relations = [element for element in geoJlist if element['type'] == "relation"]

rel = pd.DataFrame(relations)
wa = pd.DataFrame(ways)
nod = pd.DataFrame(nodes)

def get_coords(c):
    firstway_id = c['members'][0]['ref']
    firstnode_id = list(wa.loc[wa['id'] == firstway_id]['nodes'])[0][0]
    firstnode_coords = nod.loc[nod['id'] == firstnode_id]
    begin_lat = float(firstnode_coords['lat'])
    begin_lon = float(firstnode_coords['lon'])
    
    lastway_id = c['members'][-1]['ref']
    lastnode_id = list(wa.loc[wa['id'] == lastway_id]['nodes'])[0][-1]
    lastnode_coords = nod.loc[nod['id']==lastnode_id]
    end_lat = float(lastnode_coords['lat'])
    end_lon = float(lastnode_coords['lon'])
    return (begin_lat, begin_lon, end_lat, end_lon)
    
rel['start_way'] = rel.apply(get_coords, axis=1)
# # rel['end_way'] = rel.apply(get_end_node, axis = 1)

'''
1. for each relation, get first and last way ID's
2. for first way ID, get first node , for last way ID get last node
3. profit
'''




