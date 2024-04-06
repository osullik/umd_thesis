import geopandas as gpd
import os
# import reverse_geocoder as rg2
import reverse_geocode as rg
from tqdm import tqdm
import json

# Read in the data
fp = os.path.join("TRAN_Maryland_State_Shape","Shape","Trans_RoadSegment.shp")
outfile = "vertices.json"
print("Reading in", fp)
data = gpd.read_file(fp)
print("Read Complete")
print(data.head)
vertices = {}
lim = 0
#Extract coords and geocode to get vertex properties
print("Iterating through segments")

for index, row in tqdm(data.iterrows(), total=data.shape[0]):
# for index, row in data.iterrows():  
    try:
        lat,lon = (row['geometry'].coords.xy)
    except NotImplementedError:
       continue
    id = (row['source_fea'])
    # print(id)

    for x in zip(lon,lat):
        loc = rg.search([x])
        try:
          vertices[id]
          # print("DOUBLE UP")
          continue

        except KeyError:
          vertices[id] = {}
          vertices[id]['country'] = loc[0]['country']
          vertices[id]['state'] = "Maryland"
          # vertices[id]['county'] = loc[0]['admin2']
          vertices[id]['city'] = loc[0]['city']
    # if lim > 2:
    #     break 
    # lim +=1
print(vertices)

with open(outfile,'w') as f:
  json.dump(vertices,f,indent=2) 