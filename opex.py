### Jack Stephenson ###
## Overpass Explorer ##
###### Version 1 ######

import requests


'''
Resources:
- Overpass API for Python documentation [https://python-overpy.readthedocs.io/en/latest/]
- Overpass Language Guide (must learn, based on C I believe) [https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide]
- Overpass Turbo Workbench []
'''

import requests

q = '[out:json][timeout:25];relation["route"="hiking"](46.561516046166,-87.437782287598,46.582255876979,-87.39284992218);(._;>;);out;'
ql = {'data':q}
michigan = requests.get('https://overpass-api.de/api/interpreter', params=ql)

print(michigan.text)



