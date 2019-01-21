### Jack Stephenson ###
## Overpass Explorer ##
###### Version 1 ######

import requests
import overpy


'''
Resources:
- Overpass API for Python documentation [https://python-overpy.readthedocs.io/en/latest/]
- Overpass Language Guide (must learn, based on C I believe) [https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide]
- Overpass Turbo Workbench []

Instructions:
1. Build queries with the workbench
2. Insert queries into overpy api reqeust call
3. load data into dataframe
4. Inspect for quality manually if possible
'''



## Example 
api = overpy.Overpass()
result = api.query("""
	node["foot"="designated"]({{bbox}});
  	way["foot"="designated"]({{bbox}});
  	relation["foot"="designated"]({{bbox}});
  	""")
numnodes = len(result.nodes) 
numways = len(result.ways)
numrelations = len(result.relations)