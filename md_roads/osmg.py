#Author: Kent O'Sullivan // osullik@umd.edu
#Derived from the OsmGraph Package (PyPi: https://pypi.org/project/osm-graph/) by tsutomu (https://pypi.org/user/tsutomu/)

#Core Imports:
import os, pickle, overpy, networkx as nx, matplotlib.pyplot as plt
from math import cos, pi, sqrt
from functools import lru_cache
from statistics import median
import argparse
import time
import sys

#Libraries
from tqdm import tqdm
import reverse_geocode as rg

#User Imports

class OSM_To_Graph():  
    earth_rad = 6371  # radius of earth(km)
    len1deg = earth_rad / 180 * pi * 1000  # m/
    
    def __init__(self, cache=True, cache_dir=os.path.join(".","cache"), cache_name="test"):

        self.coe = 0

        cdir = cache_dir

        if not os.path.isdir(cdir):
            os.mkdir(cdir)
        self.fname = os.path.join(cdir, f'osm_graph_{cache_name}.pkl')
        
        if cache and os.path.isfile(self.fname):
            print(f"LOADING {self.fname} from cache")
            with open(self.fname, 'rb') as fp:
                self.graph, self.pos = pickle.load(fp)
                self.from_cache = True
            return
        else:
            print(f"No matching cache '{self.fname}' found")
            self.from_cache = False


    def query_API(self, area_name:str, admin_level:str):
        print(f"Querying OSM for {area_name}")
        api = overpy.Overpass(read_chunk_size=524288000) #size in bytes, this is 500mb
        result=api.query(f'''
                area["name"="{area_name}"]["admin_level"="{admin_level}"]->.query_result;
                way(area.query_result)[highway];
                node(w);
                way(area.query_result)[highway];
                (._;>;);
                out body;
                ''')
        print(f"GOT RESPONSE {result} of size {sys.getsizeof(result)} bytes")
        self.get_centre_of_elipse(result)
        return(result)
    
    def get_centre_of_elipse(self, results):
        print("CALCULATING COE")
        max_nh_lat = 0
        min_nh_lat = 90
        max_sh_lat = -90
        min_sh_lat = 0
        median_lat = 0
        north_hem = False
        south_hem = False
        for way in results.ways:
            for node in way.nodes:
                if 0 < node.lat < 90:
                    north_hem = True
                    if node.lat > max_nh_lat:
                        max_nh_lat = node.lat
                    elif node.lat < min_nh_lat:
                        min_nh_lat = node.lat
                elif -90 < node.lat < 0:
                    south_hem = True
                    if node.lat > max_sh_lat:
                        max_sh_lat = node.lat
                    elif node.lat < min_sh_lat:
                        min_sh_lat = node.lat

        if north_hem and south_hem:
            median_lat = (max_nh_lat + max_sh_lat)/2
        elif north_hem:
            median_lat = (max_nh_lat+min_nh_lat)/2
        elif south_hem:
            median_lat = (min_sh_lat+max_sh_lat)/2

        print(f'''
                MAX NTH {max_nh_lat}
                MIN NTH {min_nh_lat}
                MAX STH {max_sh_lat}
                MIN STH {min_sh_lat}

                MED     {median_lat}
              ''')
        
        self.coe = cos(float(median_lat) / 180 * pi)
        print("CALCULATED COE:",self.coe)

    def get_centre_of_elipse_from_ways_list(self, ways_list):
        print("CALCULATING COE")
        max_nh_lat = 0
        min_nh_lat = 90
        max_sh_lat = -90
        min_sh_lat = 0
        median_lat = 0
        north_hem = False
        south_hem = False
        for way in ways_list:
            for node in way.nodes:
                if 0 < node.lat < 90:
                    north_hem = True
                    if node.lat > max_nh_lat:
                        max_nh_lat = node.lat
                    elif node.lat < min_nh_lat:
                        min_nh_lat = node.lat
                elif -90 < node.lat < 0:
                    south_hem = True
                    if node.lat > max_sh_lat:
                        max_sh_lat = node.lat
                    elif node.lat < min_sh_lat:
                        min_sh_lat = node.lat

        if north_hem and south_hem:
            median_lat = (max_nh_lat + max_sh_lat)/2
        elif north_hem:
            median_lat = (max_nh_lat+min_nh_lat)/2
        elif south_hem:
            median_lat = (min_sh_lat+max_sh_lat)/2

        print(f'''
                MAX NTH {max_nh_lat}
                MIN NTH {min_nh_lat}
                MAX STH {max_sh_lat}
                MIN STH {min_sh_lat}

                MED     {median_lat}
              ''')
        
        self.coe = cos(float(median_lat) / 180 * pi)
        print("CALCULATED COE:",self.coe)


        

    def refine_results(self,query_results, white_list:list):
        print("REFINING RESULTS")
        blst= set(white_list)

        self.graph = nx.Graph()
        inbox, self.pos = set(), {}
        for way in tqdm(query_results.ways):
            
            if way.tags.get('highway') not in blst:
                continue
            
            #Get street names and county for attributes
            street = [val for key, val in way.tags.items() if "name" == key]
            # print("KEYs:",[key for key, val in way.tags.items() if "name" in key])
            if street == []:
                street = "<UNK>"
            else:
                street= street[0]
            county = [val for key, val in way.tags.items() if "county" in key]
            if county == []:
                county = "<UNK>"
            else:
                county = county[0]
            # print("STREET",street, "COUNTY", county)

            for nd in way.nodes:
                inbox.add(nd.id)
                if nd.id not in self.pos:
                    self.pos[nd.id] = float(nd.lon), float(nd.lat)
                    longitude = nd.lon
                    latitude = nd.lat
                    self.graph.add_node(nd.id, 
                                        lat=float(latitude),
                                        lon=float(longitude), 
                                    )
                    
                    country,city=reverse_geocode(latitude,longitude)
                    
                    nx.set_node_attributes(self.graph, {nd.id:city}, 'city')
                    nx.set_node_attributes(self.graph, {nd.id:country}, 'country')
                    # nx.set_node_attributes(self.graph, {nd.id:' '.join(street)}, 'street_name') #Use when getting list of street names
                    nx.set_node_attributes(self.graph, {nd.id:street}, 'street_name')
                    nx.set_node_attributes(self.graph, {nd.id:county}, 'county')
                            
            for nd1, nd2 in zip(way.nodes[:-1], way.nodes[1:]):
                if nd1.id in inbox or nd2.id in inbox:
                    dis = self.distance(nd1.id, nd2.id)
                    self.graph.add_edge(nd1.id, nd2.id, weight=dis, **way.tags)
        with open(self.fname, 'wb') as fp:
            pickle.dump((self.graph, self.pos), fp)

        return

    def refine_results_from_ways_list(self,ways_list, white_list:list):
        print("REFINING RESULTS FROM WAYS LIST")

        self.get_centre_of_elipse_from_ways_list(ways_list)

        blst= set(white_list)

        self.graph = nx.Graph()
        inbox, self.pos = set(), {}
        for way in ways_list:
            if way.tags.get('highway') not in blst:
                continue
            
            for nd in way.nodes:
                inbox.add(nd.id)
                if nd.id not in self.pos:
                    self.pos[nd.id] = float(nd.lon), float(nd.lat)
                    self.graph.add_node(nd.id, lat=float(nd.lat),
                        lon=float(nd.lon), **nd.tags)
            
            for nd1, nd2 in zip(way.nodes[:-1], way.nodes[1:]):
                if nd1.id in inbox or nd2.id in inbox:
                    dis = self.distance(nd1.id, nd2.id)
                    self.graph.add_edge(nd1.id, nd2.id, weight=dis, **way.tags)
        with open(self.fname, 'wb') as fp:
            pickle.dump((self.graph, self.pos), fp)

        return 
    
    def combine_results(self, results_dict):
        print("COMBINING RESULTS")
        ways = []
        for county in results_dict.keys():
            for way in results_dict[county].ways:
                ways.append(way)

        return ways

    @lru_cache(maxsize=4096)
    def distance(self, nd1, nd2):
        x1, y1 = self.pos[nd1]
        x2, y2 = self.pos[nd2]
        return sqrt(((x1 - x2) * self.coe)**2 + (y1 - y2)**2) * OSM_To_Graph.len1deg
    
    def get_county_names(self,state):
        print("GETTING COUNTY NAMES")
        api = overpy.Overpass()
        query = f"""
        [out:json];
        area["name"="{state}"]->.searchArea;
        (
        relation["admin_level"="6"](area.searchArea);
        );
        out body;
        """.format(state=state)

        result = api.query(query)

        county_names = []
        for item in result.relations:
            if 'name' in item.tags and 'type' in item.tags:
                if item.tags['type'] == 'boundary' and item.tags['boundary'] == 'administrative':
                    county_names.append(item.tags['name'])

        return county_names
    
    def extract_largest_subgraph(self, graph):
        print("EXTRACTING LARGEST CC")
        largest_subgraph = None
        max_nodes = 0

        for subgraph in nx.connected_components(graph):
            if len(subgraph) > max_nodes:
                largest_subgraph = graph.subgraph(subgraph)
                max_nodes = len(subgraph)
                
        l1 = [n for n in graph]
        l2 = [self.process_node(n,largest_subgraph) for n in tqdm(l1)]
        graph.remove_nodes_from(l2)
        
        return(graph)
    
    def process_node(self,node, largest_subgraph):
            if node not in largest_subgraph:
                return node
    
    def generate_summary_statistics(self,graph):
        print("Number of nodes:", nx.number_of_nodes(G))
        print("Number of edges:", nx.number_of_edges(G))
        print("Density:", nx.density(G))
        print("Average degree:", sum(dict(G.degree()).values()) / len(G))
        print("Maximal degree:", max(dict(G.degree()).values()))
        print(nx.degree_histogram(G))
        print(set(dict(G.degree()).values()))
        print("Average clustering coefficient:", nx.average_clustering(G))
        print("Number of connected components:", nx.number_connected_components(G))
        print("Largest Connected Component Size:", max([len(cc) for cc in list(nx.connected_components(G))]),
              "(", 
              ((max([len(cc) for cc in list(nx.connected_components(G))]))/nx.number_of_nodes(G))*100,"% of graph size)")
        print("Median Connected Component Size:", median([len(cc) for cc in list(nx.connected_components(G))]))
        
        #Diameter and Average Shortest path require fully connected graphs, and take a looooong time on large graphs. 
        try:
            print("Diameter:", nx.diameter(G))
        except nx.NetworkXError as e:
            print(f"SKIPPING DIAMETER -- {e}")
        # try:
        #     print("Average shortest path length:", nx.average_shortest_path_length(G))
        # except nx.NetworkXError as e:
        #     print(f"SKIPPING Shortest Path -- {e}")

    def calculate_communities(self,G:nx.graph, community_list:list=['city']):
        print("CALCULATING COMMUNITIES")
        # Initialize an empty dictionary to store city-node mappings
        communitities = {}

        for community in community_list:
            # print("COMMUNITY:", community)
            communitities[community] = {}

            # Iterate over nodes in the graph
            for node in tqdm(G.nodes()):
                member_of = G.nodes[node][community]
                # print(member_of)
                # print("TYPE", type(member_of))
                
                if member_of not in communitities[community]:
                    communitities[community][member_of] = set()
                
                # Append the node ID to the list corresponding to the city
                communitities[community][member_of].add(node)

            print("THERE ARE", (len(communitities[community])), "COMMUNITIES")

        return communitities

    def dump_graph(self, graph:nx.graph, filename:str, comment:str=None,):
        print(f"DUMPING WEIGHTED GRAPH TO {filename}")
        with open(filename, 'w') as f:
            # Write comment at the start of the file if provided
            if comment is not None:
                f.write(f"# {comment}\n")
            # Iterate over each node in the graph
            for node in tqdm(graph.nodes()):
                neighbors = graph[node]
                # Write the node followed by its neighbors and edge weights
                if neighbors:
                    neighbor_strings = [
                        f"{neighbor} {graph[node][neighbor]['weight']:.6f}" 
                        for neighbor in neighbors
                    ]
                    f.write(f"{node} {' '.join(neighbor_strings)}\n")
                else:
                    f.write(f"{node}\n")
        print(f"DUMPED WEIGHTED GRAPH TO {filename}")

    def dump_communities(self, communities:dict, filename:str, comment:str=None):
        for community_type in communities:
            print(f"DUMPING GROUND TRUTH {community_type} COMMUNITIES TO {filename}")
            with open(f"{filename}_{community_type}.txt", 'w') as f:
                # Write comment at the start of the file if provided
                if comment is not None:
                    f.write(f"# {community_type}{comment}\n")
                # Iterate over each community
                    for comm in communities[community_type]:
                        f.write(f"{comm} {list(communities[community_type][comm])}\n")

        print(f"DUMPED GROUND TRUTH {community_type} COMMUNITIES")

    def dump_attributes(self, graph:nx.graph, attributes:list, filename:str, comment:str=None):
        print(f"DUMPING ATTRIBUTES: {attributes} TO FILE {filename}")
        with open(filename,'w') as f:
            if comment is not None:
                f.write(f"# {comment}\n")
            for node in tqdm(graph.nodes):
                # print(graph.nodes[node])
                to_write = []
                for attribute in attributes:
                    thisattr = graph.nodes[node][attribute]
                    to_write.append(str(thisattr))
                    # print("ATTRIBUTE:", attribute, thisattr)
                f.write(f"{node} {' '.join(to_write)}\n")
                # print("WRITING:", to_write)
        print("DUMPED ATTRIBUTES TO FILE")

                # print("WRITING:", to_write)
                






def reverse_geocode(longitude, latitude):
    loc = rg.search([(longitude,latitude)])
    country = loc[0]['country']
    city = loc[0]['city']
    
    return (country,city)


if __name__=="__main__":

    white_list = ["motorway",
                  "trunk",
                  "primary",
                  "secondary",
                  "tertiary",
                  "unclassified",
                  "residential",
                  "motorway_link",
                  "trunk_link",
                  "primary_link",
                  "secondary_link",
                  "tertiary_link",
                  "living_street",
                  "service"
                  ]

    ap = argparse.ArgumentParser()

    ap.add_argument("--search_area",
                    type=str,
                    required=True,
                    help="The OSM name of the City, County, State, Country you wish to generate a road graph of")
    ap.add_argument("--area_type",
                    type=str,
                    required=True,
                    help="The type of entity you are searching for: COUNTRY, STATE, COUNTY, CITY")
    
    flags = ap.parse_args()

    area_type_map = {"COUNTRY":2,
                      "STATE":4,
                      "COUNTY":6,
                      "CITY":8}

    TARGET = flags.search_area
    ADMIN_LEVEL = area_type_map[flags.area_type]
    GRAPH_DIRECTORY = os.path.join(".","graphs")
    
    OQ = OSM_To_Graph(cache_name=TARGET)

    #Check for cached data
    if OQ.from_cache:
        pass
    else:

        # #CUSTOM SEARCH (FOR TESTING)
        
        # results = OQ.query_API(area_name=TARGET_CITY, admin_level=TARGET_ADMIN_LEVEL)
        # refined = OQ.refine_results(results,white_list=white_list)


        #SEARCH BY STATE
        results = OQ.query_API(area_name=TARGET, admin_level=ADMIN_LEVEL)
        
        with open (TARGET+"_raw.pkl", "wb") as f:
            pickle.dump(results,f)

        time.sleep(2) #Give it time to finish writing the raw before refining. 

        refined = OQ.refine_results(results,white_list=white_list)
        

        #SEARCH BY COUNTY (I.e. get puzzle pieces and combine)  - performs poorly, lots of orphan nodes:
        # # Get the list of county names
        # county_names = OQ.get_county_names(state=TARGET_STATE)
        # countyDict = {}
        # for county in county_names:
        #     if(os.path.isfile(county+".pkl")):
        #         with open(county+".pkl", "rb") as f:
        #             print(f"loading cached data for {county}")
        #             results=pickle.load(f)
        #     else:
        #         results = OQ.query_API(area_name=county, admin_level="6")
        #         with open (county+".pkl", "wb") as f:
        #             pickle.dump(results,f)
        #     countyDict[county] = results

        # combined = OQ.combine_results(results_dict=countyDict)
        # refined = OQ.refine_results_from_ways_list(ways_list=combined, white_list=white_list)


    G = OQ.graph
    OQ.generate_summary_statistics(G)

    G_sub = OQ.extract_largest_subgraph(G)

    communities = OQ.calculate_communities(G,['city','county'])

    
    if not os.path.isdir(GRAPH_DIRECTORY):
            os.mkdir(GRAPH_DIRECTORY)

    comment="Line Format: Source Dest1 Weight1 ... DestN WeightN. Weight is distance in KM"
    OQ.dump_graph(graph=G,comment=comment,filename=os.path.join(GRAPH_DIRECTORY,TARGET+"_adj_list.txt"))
    
    comm_comment = "-level ground-truth communties. Shared nodes denoted with Community1;CommunityN. Line Format: Community [Member nodes]."
    OQ.dump_communities(communities=communities,comment=comm_comment,filename=os.path.join(GRAPH_DIRECTORY,TARGET+"_gt_communities"))

    attr_comment = "Line Format: Vertex lat lon street_name"
    OQ.dump_attributes(graph=G,attributes=['lat','lon','street_name'],filename=os.path.join(GRAPH_DIRECTORY,TARGET+"_attributes.txt"),comment=attr_comment)

    OQ.generate_summary_statistics(G_sub)

