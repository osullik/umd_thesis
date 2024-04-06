import geopandas as gpd
import os
# import reverse_geocoder as rg2
from tqdm import tqdm
import json
import pickle
from shapely import Point, LineString
from shapely.ops import linemerge
from shapely.geometry import MultiLineString
import reverse_geocode as rg


def load_data(pickle_file:os.path):
    # Read in the data
    print("Reading in", pickle_file)
    with open(pickle_file,'rb') as f:
        data = pickle.load(f)
    print("Read Complete")
    return data

def reverse_geocode(data):
    print("Reverse geocoding...")
    for index, row in tqdm(data.iterrows(), total=data.shape[0]):
    # for index, row in data.iterrows():  
        try:
            lat,lon = (row['geometry'].coords.xy)
        except NotImplementedError:
            continue
        id = (row['source_fea'])
        name = (row['name'])
        data.loc[index,'lat'] = lat[0]
        data.loc[index,'lon'] = lon[0]

        

        
        for x in zip(lon,lat):
            loc = rg.search([x])
            country = loc[0]['country']
            state = "MD"
            city = loc[0]['city']
    
            data.loc[index,'country']  = str(country)
            data.loc[index,'state']  = str(state)
            # vertices[id]['county'] = loc[0]['admin2']
            data.loc[index,'city']  = str(city)

            data.loc[index,'full_name']=f"{name,city,state}" 
    
    return data


def generate_segment_lists(data):
    ids = []
    names = []
    segments = []
    for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
        ids.append(row['ObjectID'])
        names.append(row['full_name'])
        segments.append(row['geometry'])  

    return (ids, names, segments)

def group_by_street(data):
    names = list(data.full_name.unique())
    segments = {}
    for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
        try:
            segments[row['full_name']].append(row.geometry)
        except KeyError: 
            segments[row['full_name']] = []
            segments[row['full_name']].append(row.geometry)

    return segments

# def merge_segments(segments):
#     merged_coords = []
#     if isinstance(segments, MultiLineString):
#         for line_string in segments:
#             merged_coords.extend(line_string.coords)
#     else:
#         merged_coords.extend(segments.coords)
    
#     merged_line = LineString(merged_coords)
#     return merged_line

def generate_big_segments(geom_lists_by_name:dict):
    results = []
    names = []

    ls = 0
    ml = 0
    o = 0
    outputs = {}
    for name in tqdm(geom_lists_by_name):
        flat_line_str = []
        for geom in geom_lists_by_name[name]:
            if type(geom) is LineString:
                # new_name = reverse_geocode(name,geom.coords.xy)
                flat_line_str.append(geom)
            elif type(geom) is MultiLineString:
                for sub_geom in geom.geoms:
                    flat_line_str.append(sub_geom)
                    # new_name = reverse_geocode(name,geom.coords.xy)
                # ml +=1
            else:
                print("OTHER", type(geom))
        outputs[name] = flat_line_str
    
    for name in outputs:
        result = linemerge(outputs[name])
        results.append(result)
        names.append(name)

    
    return(results,names)

def extract_intersections(segments:list, names:list):
    intersections = []
    roads=[]
    for i, seg1 in enumerate(tqdm(segments)):
        for j, seg2 in enumerate(segments):
            if j == i:
                pass 
            else:
                intersection = seg1.intersection(seg2)
                if intersection.is_empty:
                    continue
                if isinstance(intersection, Point):
                    intersections.append(intersection)
                    print("INTERSECTION", intersections[-1], names[i],names[j])
                elif isinstance(intersection, LineString):
                    print("INTERSECTION",intersections[-1],names[i],names[j])
                    intersections.extend(list(intersection.coords))
    
        if i>5:
            break

    return(intersections,roads)

def pickle_results(data,filename="TRAN_Maryland_State_Shape_Geocoded.pkl"):
    print(f"Pickling {filename}")
    data.to_pickle(os.path.join(".",filename))

if __name__ == "__main__":

    # fp = os.path.join("TRAN_Maryland_State_Shape.pkl")

    # data = load_data(fp)
    
    # gc_data = reverse_geocode(data)
    # pickle_results(gc_data)

    gc_data = load_data(os.path.join(".","TRAN_Maryland_State_Shape_Geocoded.pkl"))

    print(gc_data.head())

    bs = group_by_street(gc_data)

    segs,names = generate_big_segments(bs)

    # print(segs)

    intersections = extract_intersections(segs,names)

    # print(intersections)
    
    with open("intersections.pkl","wb") as f:
        pickle.dump(intersections,f)

    



    # for k in bs.keys():
    #     print(k, bs[k])
    # print(list(create_big_segments(data)))

    

    # ids,names,segments = generate_segment_lists(data)

    # merged = merge_segments(segments)
    
    # ids,names,segments = generate_segment_lists(data)
    # intersections= extract_intersections(segments)

    # print(intersections)




