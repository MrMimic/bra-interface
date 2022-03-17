"""http://andrewgaidus.com/leaflet_webmaps_python/
"""
import geopandas
import matplotlib.pyplot as plt
import pandas as pd
from folium import GeoJson, GeoJsonTooltip, Map
from geopandas import GeoDataFrame
from shapely.geometry import MultiPolygon, Point, Polygon


def get_style() -> dict:
    return {'fillColor': '#00FFFFFF'}


def get_risk_map(html: bool = False):
    # Get a map of the world and slice only France
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    france = world.query('name == "France"')
    # Remove Gayana and DOM-TOM (no mountains)
    france = GeoDataFrame(
        france["geometry"]
        .apply(
            lambda mp: MultiPolygon(
                [p for p in mp.geoms if p.bounds[1] > 20]
            )
        )
    )
    france["name"] = ["France"]
    # No color filling for the whole country
    style_france = {'fillColor': "#00000000"}

    # Create a Folium map with desired level of zoom
    middle_france = [46.854422675450635, 3.6521234005924885]
    zoomed_map = Map(location=middle_france, zoom_start=6, control_scale=True)

    # Add the France polygon to the map
    GeoJson(france,
        style_function=lambda x: style_france,
        tooltip=GeoJsonTooltip(fields=['name'],
                                                                aliases = ['Name'],
                                                                labels=True,
                                                                sticky=False
                                                                            )).add_to(zoomed_map)


    # Here all massifs should be defined
    vercors = Polygon([
        Point(5.017319341040425, 44.7493579157845), 
        Point(5.1642614797123, 44.9646799514329), 
        Point(5.3839880422123, 45.15323581600035), 
        Point(5.585861821509175, 45.311057714316235), 
        Point(5.69435181174355, 45.171028542320705), 
        Point(5.68336548361855, 44.91504301397672)
    ])
    massifs = GeoDataFrame({'geometry': [vercors], "name": ["Vercors"], "color": ["red"] })
    massifs.crs = france.crs  

    # Apply the massifs on the map
    GeoJson(massifs,
        style_function=lambda x: get_style(),
        tooltip=GeoJsonTooltip(fields=['name'],
                                                                aliases = ['Name'],
                                                                labels=True,
                                                                sticky=False
                                                                            )).add_to(zoomed_map)

    if html:
        return zoomed_map._repr_html_()
    else:
        return zoomed_map

def save_map(map_object, outfp: str = "base_map.html"):
    map_object.save(outfp)

map = get_risk_map()
save_map(map)
