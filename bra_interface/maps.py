"""http://andrewgaidus.com/leaflet_webmaps_python/
"""
import logging
import os
import pickle
from typing import List

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
        # Load the precomputed polygons representing massifs
        self.massifs_coords = pickle.load(open(os.path.join(os.path.dirname(__file__), "massif_coord_gps.pkl"), "rb"))
        # And the latest data from the DB
        self.massif_data= {}
        for massif in self.massifs_coords:
            self.logger.info(f"Getting data for massif {massif}")
            self.massif_data[massif] = self.get_lastest_data(massif, columns=["risk_score", "date"])

    def get_style(self, input_data):
        score = self.massif_data[input_data["properties"]["name"].upper()]["risk_score"]
        return {"fillColor": self.cmap[score], "fillOpacity": "0.5", "weight": "1", "color": "white"}

    def get_lastest_data(self, massif: str, columns: List[str] = ["*"]):
        query = f"""
            SELECT {', '.join(columns)} 
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
            data = database.exec_query(query)[0]
        return data

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
        # Create a Folium map , centered on Avignon, with the desired level of zoom of the France
        middle_france = [43.949317, 4.805528]
        zoomed_map = Map(location=middle_france, zoom_start=7, control_scale=True)
        # Add the France polygon to the map
        GeoJson(france,
            style_function=lambda x: style_france,
            tooltip=GeoJsonTooltip(fields=['name'],
                                                                    aliases = ['Name'],
                                                                    labels=True,
                                                                    sticky=False
                                                                                )).add_to(zoomed_map)

        # Aggregate the massif data
        massifs_data = {
            "geometry": [],
            "name": [],
            "risks": [],
            "date": []
        }
        for massif in self.massifs_coords:
            massifs_data["geometry"].append(Polygon(self.massifs_coords[massif]))
            massifs_data["name"].append(massif)
            massif_data = self.massif_data[massif]
            massifs_data["risks"].append(massif_data["risk_score"])
            massifs_data["date"].append(massif_data["date"].strftime("%d/%m/%Y"))
        
        massifs = GeoDataFrame(massifs_data)
        massifs.crs = france.crs  

        # Apply the massifs on the map
        GeoJson(massifs,
            style_function=lambda x: self.get_style(x),
            tooltip=GeoJsonTooltip(fields=['name', "risks"],
                                                                    aliases = ['Name', "Risque"],
                                                                    labels=True,
                                                                    sticky=False
                                                                                )).add_to(zoomed_map)

        # Returns HTML or the map object directly
        if html:
            return zoomed_map._repr_html_()
        else:
            return zoomed_map

    @staticmethod
    def save_map(map_object, outfp: str = "base_map.html"):
        map_object.save(outfp)
