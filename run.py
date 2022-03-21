"""
"""
import os
from datetime import datetime
from typing import Dict
from urllib import request

from dotenv import load_dotenv
from flask import Flask, render_template, request

from bra_interface.connection import BraDatabase
from bra_interface.maps import Mapper
from bra_interface.utils import DbCredentials, get_logger

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
    """Select the latest BRA of a specific massif"""
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


def get_specific_history(massif: str) -> Dict[str, str]:
    """Select the BRA history of a specific massif"""
    with BraDatabase(credentials=credentials, logger=logger) as database:
        query = f"""
            SELECT date, original_link
            FROM bra.france
            WHERE massif = '{massif}'
            ORDER BY date DESC;
        """
        history = [(d["date"].strftime(date_format), d["original_link"]) for d in database.exec_query(query)]
    return history


def get_tab_panel_activity(active: bool = True) -> str:
    """The first active/inactive refers to the selected tab on top-page.
    The other one (tab-pane fade) refers to the panel that is indeed printed below.
    """
    if active:
        return "active", "tab-pane fade in active"
    else:
        return "inactive", "tab-pane fade"


@app.route("/", methods=["GET", "POST"])
def index():

    # The selected massif for BRA table. Other variables are used to select the panel/tab once
    # the page is refreshed.
    try:
        bra_selected_massif = request.form["bra_selected_massif"]
        activity_bra_tab, activity_bra_div = get_tab_panel_activity(active=True)
    except KeyError:
        bra_selected_massif = "aravis"
        activity_bra_tab, activity_bra_div = get_tab_panel_activity(active=False)

    # The selected massif for the historical data
    try:
        historical_selected_massif = request.form["history_selected_massif"]
        activity_history_tab, activity_history_div = get_tab_panel_activity(active=True)
    except KeyError:
        historical_selected_massif = "aravis"
        activity_history_tab, activity_history_div = get_tab_panel_activity(active=False)

    # Get the BRA of the selected massif
    selected_bra = get_specific_bra(bra_selected_massif)
    # Get the history of the selected massif
    selected_history = get_specific_history(historical_selected_massif)

    # Create the response context and post as a Jinja template
    original_link_formated = ".".join(selected_bra['original_link'].split(".")[3:5])

    print(f"BRA: {activity_bra_tab}")
    print(f"HIS: {activity_history_tab}")

    context = {
        "activity_history_tab": activity_history_tab,
        "activity_bra_tab": activity_bra_tab,
        "activity_history_div": activity_history_div,
        "activity_bra_div": activity_bra_div,
        "contact_email": "emeric.dynomant@gmail.com",
        "home": "https://data-baguette.com",
        "carte_risque_massifs": mapper.get_risk_map(html=True),
        "massifs": available_massifs,
        "BRA_selected_massif": bra_selected_massif,
        "HISTORY_selected_massif": historical_selected_massif,
        "BRA_data": {
            "Massif": selected_bra["massif"].title(),
            "BRA original": f"<a href='{selected_bra['original_link']}'target='_blank'>{original_link_formated}</a>",
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
        },
        "BRA_history": selected_history
    }
    html_template = render_template("index.html", **context)
    return html_template


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
