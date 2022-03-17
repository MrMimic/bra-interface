"""http://andrewgaidus.com/leaflet_webmaps_python/
"""
import logging
import os
import pickle

import geopandas
from folium import GeoJson, GeoJsonTooltip, Map
from geopandas import GeoDataFrame
from shapely.geometry import MultiPolygon, Polygon

from bra_interface.connection import BraDatabase
from bra_interface.utils import DbCredentials, get_logger


class Mapper():

    def __init__(self, logger: logging.Logger = None) -> None:
        self.credentials = DbCredentials()
        self.logger = logger if logger is not None else get_logger()
        # This map a color for each risk of snow
        self.cmap = {
            1: "green",
            2: "yellow",
            3: "orange",
            4: "red",
            5: "black"
        }

    def get_style(self, input_data):
        score = self.get_last_risk(input_data["properties"]["name"].lower())
        return {"fillColor": self.cmap[score], "fillOpacity": "0.5", "weight": "1", "color": "white"}

    def get_last_risk(self, massif: str):
        query = f"""
            SELECT risk_score 
            FROM bra.france f
            WHERE f.id = (
                SELECT MAX(id) 
                FROM bra.france f1
                WHERE f1.`date` = (
                    SELECT max(`date`)
                    FROM bra.france f2 
                    WHERE f2.massif = '{massif}'
                ) AND
            massif = '{massif}')
        """
        with BraDatabase(credentials=self.credentials, logger=self.logger) as database:
            score = database.exec_query(query)[0]["risk_score"]
        return score

    def get_risk_map(self, html: bool = False):

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
        style_france = {'fillColor': "#00000000", "weight": "1", "color": "black"}
        # Create a Folium map with desired level of zoom of the France
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

        # Load the massif coordinate coming from Gmaps data    
        massifs_coords = pickle.load(open(os.path.join(os.path.dirname(__file__), "massif_coord_gps.pkl"), "rb"))
        geometries = []
        names = []
        risks = []
        for massif in massifs_coords:
            geometries.append(Polygon(massifs_coords[massif]))
            names.append(massif)
            risks.append(self.get_last_risk(massif))
        
        massifs = GeoDataFrame({'geometry': geometries, "name": names, "risks": risks})
        massifs.crs = france.crs  

        # Apply the massifs on the map
        GeoJson(massifs,
            style_function=lambda x: self.get_style(x),
            tooltip=GeoJsonTooltip(fields=['name', "risks"],
                                                                    aliases = ['Name', "Risque"],
                                                                    labels=True,
                                                                    sticky=False
                                                                                )).add_to(zoomed_map)

        if html:
            return zoomed_map._repr_html_()
        else:
            return zoomed_map

    @staticmethod
    def save_map(map_object, outfp: str = "base_map.html"):
        map_object.save(outfp)
