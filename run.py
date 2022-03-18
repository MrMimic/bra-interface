"""
"""
from datetime import datetime
import os
from typing import Dict
from urllib import request
from bra_interface.connection import BraDatabase
from bra_interface.utils import DbCredentials, get_logger
from bra_interface.maps import Mapper

from dotenv import load_dotenv
from flask import Flask, render_template, request

app = Flask(__name__)

date_format = "%d/%m/%Y"

# Load credentials if found locally
load_dotenv()

# Download the BRA files of the day
try:
    today = os.environ["BRA_DATE"]
except KeyError:
    today = datetime.today().strftime("%Y%m%d")

# Get a distinct logger each day
try:
    base_path = os.environ["BRA_LOG_FOLDER"]
except KeyError:
    base_path = os.path.join(os.sep, "logs")
logger = get_logger(base_path=base_path, file_name=f"{today}_bra_database.log")

# Get the massif names
credentials = DbCredentials()
with BraDatabase(credentials=credentials, logger=logger) as database:
    query = f"""
        SELECT DISTINCT(massif) from bra.france"""
    available_massifs = [m["massif"] for m in database.exec_query(query)]

# Create the object allowing to design the map
mapper = Mapper(logger=logger)

def get_specific_bra(massif: str) -> Dict[str, str]:
    """
    """
    with BraDatabase(credentials=credentials, logger=logger) as database:
        query = f"""
            SELECT * 
            FROM bra.france f
            WHERE f.id = (
                SELECT MAX(id) 
                FROM bra.france f1
                WHERE f1.`date` = (
                    SELECT max(`date`)
                    FROM bra.france f2 
                    WHERE f2.massif = '{massif}'
                ) AND
            massif = '{massif}');
        """
        data = database.exec_query(query)[0]
        return data

@app.route("/", methods=["GET", "POST"])
def index():

    # The selected massif for BRA print
    try:
        selected_massif = request.form["selected_massif"]
    except KeyError:
        selected_massif = "aravis"

    # Get the BRA of the selected massif
    selected_bra = get_specific_bra(selected_massif)

    # Create the response context and post as a Jinja template
    context = {
        "contact_email": "emeric.dynomant@gmail.com",
        "home": "https://data-baguette.com",
        "carte_risque_massifs": mapper.get_risk_map(html=True),
        "massifs": available_massifs,
        "BRA_selected_massif": selected_massif,
        "BRA_data": {
            "Massif": selected_bra["massif"],
            "BRA original": f"<a href='{selected_bra['original_link']}'target='_blank'>{selected_bra['original_link']}</a>",
            "Date" : selected_bra["date"].strftime(date_format),
            "Jusqu'au" : selected_bra["until"].strftime(date_format),
            "Départs spontanés" : selected_bra["departs"],
            "Déclenchements provoqués" : selected_bra["declanchements"],
            "Risque d'avalanche /5": selected_bra["risk_score"],
            "Risque d'avalanche": selected_bra["risk_str"],
            "Situation avalancheuse typique": selected_bra["situation_avalancheuse_typique"],
            "Départ spontanés": selected_bra["departs_spontanes"],
            "Départs provoqués": selected_bra["declanchements_provoques"],
            "Qualité de la neige": selected_bra["qualite_neige"],
        }
    }
    html_template = render_template("index.html", **context)
    return html_template


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
