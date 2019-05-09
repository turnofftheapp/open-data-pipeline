# Quick Start

(Python 3)
How To Run: (from /open-data-pipeline/)
1. install dependencies:
	<pip install -r requirements.txt>
2. Populate config.py with db info and mapquest key.
3. Edit REGION in main()
4. run <python geoPipe.py>
5. optionally, print(trail_df) to read dataframe output
	hint: look for column headers and notice
	how output is split to fit the terminal

# Issue tracker

https://github.com/turnofftheapp/open-data-pipeline/projects/1

# Documentation

### OSM Query:
´´´
[out:json][timeout:1000][maxsize:2073741824]; \
area({0})->.searchArea; \
(way["highway"~"path|footway|cycleway|bridleway"]\
["name"~"trail|Trail|Hiking|hiking"] \
(area.searchArea););(._;>;);out;'.format(region_code)
´´´

**Breakdown of what each part of this query does:**

* [out:json]
   * Specifies the output is in JSON
* [timeout:1000][maxsize:2073741824];
   * Setting time and size limits, allowing us to get as many trails as possible. The default maxsize value is 512MB (too small), but OSM automatically aborts any queries that go over 2GB.
* area({0})->.searchArea;
   * The {0} is pulling from the .format(region_code) part at the end. This is passing a coded value for the desired area into the area() function, and assigning it to a variable called .searchArea. This allows us to make our query only search in a given area, which we are calling .searchArea.
* (way
   * We are searching for ways with the following tags (not relations).
* ["highway"~"path|footway|cycleway|bridleway"]
   * Uses regex to determine if the “highway” tag for each way contains one of these four things. Bridleway means it’s designed for horses, but allows foot traffic according to OSM documentation.
*  ["name"~"trail|Trail|Hiking|hiking"]
   * Uses regex to determine if the name of the way contains “trail” or “hiking.” Misses some false negatives, but avoids a lot of false positives too.
* (area.searchArea););
   * This is where the searchArea variable is used; it is put at the end of the rest of the tags to signify that only ways in this area should be considered
* (._;>;);
   * Recurses down, to include all of the nodes involved in these ways.
   * More technically, this is doing the following:
      * The parentheses are doing a union of the sets inside of it.
      * The first set is just the “default set,” meaning the output of our query. It is represented as “._”.
      * The second set is the result of recursing down “>”. 
      * In effect, this is combining the ways we found with our query with the set of nodes found by recursing down, and returning all this info together.
* out;
   * OSM syntax, returns the JSON of what we just found
* .format(region_code)
   * As mentioned above, this replaces {0} with the python variable region_code in order to set up searchArea.
* NOTE: The slashes are just syntax for allowing line breaks, they don’t actually do anything to the query. The single quotation marks (‘) are because the query string is having .format(region_code) applied to it; to run this in Overpass, you would need to remove the .format(region_code) part, the quotation marks, and the slashes.


### Global Parameters

* MAX_REPAIR_DIST_METERS = 150: distance in meters within which a way may be joined to a trail_obj
* BUS_RADIUS_METERS = 800: radius within which to search for bus stops
* LOOP_COMPLETION_THRESHOLD_METERS = 20: distance deemed close-enough for a trail to be considered a loop
* REGION = "California" : region to query for
* COUNTRY = "" : country to query for, use if multiple regions exist in different countries, can/should be left as an empty string if otherwise

### Functions

**geoPipe.py:** Functions/runtime

* main(): pipeline logic exists here, following steps below:
   * Setup: 
	* sys.setrecursionlimit(5000): sets max recursion depth to 5000, needed for ways_to_trails()
	* MAX_REPAIR_DIST_METERS: max distance between two ways for them to be repaired into the same trail
	* BUS_RADIUS_METERS: radius within which a bus stop may be located
	* REGION = “”: specify region here, i.e. “Michigan” or “Ontario”
	* COUNTRY = “”: specify country here, if multiple regions exist by same name
	* tqdm.pandas(): initializes tqdm package, allows progress_apply to display a progress bar when applying a function to a dataframe

	1. Get overpass region_code using util.get_region_code
	2. Query overpass for trail ways in given region
	3. Split elements returned by query into dataframe of ways and dataframe of nodes
	4. For each way: inject its nodes into column ‘nodes’ (replacing old ‘nodes’ column)
	5. For each way: evaluate name and create new column
	6. Call ways_to_trails() to combine all closeby way objects into trail relations, also combining their tags. Result is new dataframe trail_df
	7. Add column with region code to trail_df, Add column with region name to trail_df
	8. Get geoJSON LineString and MultiLineString objects for each trail in trail_df
	9. Determines encoded polyline for each trail in trail_df, adds to column ‘polylines’
	10. Flattens nested tag objects, combining values with the same key for each trail
	11. Creates new columns: trail_start and trail_end containing start and end coordinates for each trail
	12. Calculate distance along each trail LineString object, adds to column ‘distances’
	13. Determine trail shape (if trail_start == trail_end; thru_hike = True)
	14. Query transit land for each trail, finding bus stops within a defined radius
	15. Insert trails into database using to_db()

* queryOSM(region_code): queries OSM for trail ways within a given region. If the OSM server times out/ display error message and exit program. 
* splitElements(osmElements): splits osm elements by type. Returns tuple of lists (ways, nodes)
* injectNodes(c, node_df): Apply to dataframe: for each row (represented by c (Cython iterator object)), replace ‘nodes’ column data with list of nodes w/coordinates for each way
* ways_to_trails(way_df, trail_list, MAX_REPAIR_DIST_METERS): 
   * groups ways with same name, selects starter way as trail_obj. 
   * for each way in a name group, if distance between endpoints < MAX_REPAIR_DIST_METERS, append way to trail_obj. Do this until no more repairs can be made, then create trail dict and append to trail_list. 
   * Continues to call itself until no ways are left in the original way_df
* to_sql(trail_df, region_code, tablename, schema=""): adds trails to database
   * Convert all types in trail_df to string
   * If a schema is specified, append a ‘.’ so that sql execute statements will work w/ schema and tablename
   * Initialize engine using info from config.py file
   * Evaluates existence of table. If exists and empty, drop. If exists, continue. If doesn't exist: create with trail_df
   * Evaluates existence of trails in db for given region. If they exist, delete them, if not, continue
   * Finally, appends new trails

**util.py:** Functions

* get_region_code(state_full_name, country_full_name="", base_code = 3600000000):
        Queries MapQuest’s Nominatum API to obtain an OSM area code for a given region. If
no region found, print warning and return error message
* validate_trails(c): not used anymore, but useful in the future to make minor adjustments and data quality assessments before running large operations on the dataset
* get_name(c): extracts name of each way from tags and pops into column
* get_polyline(c, precision=5): uses polyline library to encode trail_obj (List of list of nodes) into polyline format
* get_LineString(c): flattens trail object and injects into empty geoJSON LineString object
* get_MultiLineString(c): creates un-flattened version of LineString
* get_distance(c): calculates + sums distance between each node in a trail LineString, creates distance column with distances in meters
* pairs(lineString): generator returning set of pairs of each node in a LineString, used in get_distance
* get_node_distance_meters(node1, node2): uses geopy's distance library to calculate the distance in meters between any two coordinate pairs
* pop_endpoints(c): for each trail, create columns trail_start and trail_end
* is_loop(c, stretch_distance): Compares trail end and trail start, if within stretch_distance, trail is considered a loop/ thru_hike


### config.py: configuration

Our database info and MapQuest API key are stored in a config.py file that must be populated for each user. 


### Data:

Before pushing to the database, our trails are represented by a Pandas dataframe with columns:

* 'id’: id of each trail, unique. Derived from ID of first way used to create a given trail’s trail_obj (ways_to_trails)
* ‘name’: trail name
* ‘tags’: dictionary with tags as keys and values as lists of all tag values for a given key for a given trail
* ‘trail_obj’: deque list of each way in a trail, sorted using ways_to_trails
* ‘region_code’: OSM code representing an ‘area’ polygon. Used to specify searchArea in OSM query
* ‘region_name’: name of region queried. If a country is specified, region name will follow the “Region, Country” format
* ‘MultiLineString’: geoJSON MultiLineString object
* ‘LineString’: geoJSON LineString object
* ‘polyline’: encoded polyline derived from trail_obj, used in UI
* ‘trail_start’: first node in trail_obj
* ‘trail_end’: last node in trail_obj
* ‘trail_distance_meters’: distance of trail, in meters
* ‘thru_hike’: currently only thru_hike if trail is determined to be a loop. Used in elevation calculation
* ‘bus_stops’: list of bus stops within specified radius of trail start or end


### Caveats:

* Sometimes, the OSM servers are overloaded and a large query (i.e. California) will fail
* For the ways_to_trails algorithm, the default python recursion depth must be increased to 10000 for large queries (California). Do this at your own risk, it may cause issues depending on the system
* There is no progress bar for ways_to_trails which does take a while to run. Patience is key
