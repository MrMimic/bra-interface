"""GPS coordinates have been extracted as CSV files from Google map handmade map.
Those CSV should be transformed into a JSON file to draw polygons on the BRA map.
https://www.google.com/maps/d/edit?mid=1S0qBZM0RRRZ5v6h1hjnlbOHXbDsgMBaO&usp=sharing
This map is exported layer by layer as CSV, that are placed into the folder along this script.
It creates a pickle file representing a dict {massif: Geoserie of the polygon}.
"""

import os
import pandas as pd
from geopandas import GeoSeries
from shapely import wkt
import pickle

data_path = os.path.join(os.path.dirname(__file__), "massif_coords_csv")
massif_coord_gps = {}

for file in os.listdir(data_path):
    massif = file.replace("BRA- ", "").replace(".csv", "")
    df = pd.read_csv(os.path.join(data_path, file))
    coords = GeoSeries([wkt.loads(p) for p in df["WKT"].to_list()]).tolist()
    massif_coord_gps[massif] = coords
pickle.dump(massif_coord_gps, open(os.path.join("bra_interface", "massif_coord_gps.pkl"), "wb"))
