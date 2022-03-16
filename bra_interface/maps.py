"""http://andrewgaidus.com/leaflet_webmaps_python/
"""
import matplotlib.pyplot as plt
import libpysal as ps
import geopandas
import pandas as pd

from geopandas import GeoSeries, GeoDataFrame
from shapely.geometry import Point
from shapely.geometry import Polygon

world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
country_shapes = world[['geometry', 'iso_a3']]
country_names = world[['name', 'iso_a3']]
countries = world[['geometry', 'name']]
countries = countries.rename(columns={'name':'country'})

# What is that notation? CLose to Guyana
vercors = Polygon([Point(-51.0, 4.0), Point(-51.0, 8.0), Point(-45.0, 8.0), Point(-45.0, 5.0)])
massifs = GeoDataFrame({'geometry': [vercors], "country": ['vercors']})
massifs.crs = countries.crs

joined = pd.concat([countries, massifs], ignore_index=True)
joined.to_csv("out.csv")

m = joined.explore(legend=False)
outfp = r"base_map.html"
m.save(outfp)
