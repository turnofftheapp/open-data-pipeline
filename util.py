#### UMSIvsTOTAGO  ####
## Utility Functions ##
###### Version 1 ######
import pandas as pd
import requests
import json
import os



## IN: country, region
## OUT: Overpass region code
def getArea(country='US', region='MI'):
	'''
	Make request to overpass or wherever to retreive geo encodings.
	In the future we'll use this function to make it easier to 
	switch states and areas when querying.
	'''
	pass
