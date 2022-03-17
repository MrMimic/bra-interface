"""
"""
from datetime import datetime
import os
from bra_interface.connection import BraDatabase
from bra_interface.utils import DbCredentials, get_logger
from bra_interface.maps import get_risk_map

from dotenv import load_dotenv
from flask import Flask, render_template

app = Flask(__name__)

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

# Prepare the PDF parser and the DB credentials
credentials = DbCredentials()
with BraDatabase(credentials=credentials, logger=logger) as database:
    query = f"""
        SELECT COUNT(id) from bra.france"""
    out = database.exec_query(query)
    print(out)

@app.route("/", methods=["GET", "POST"])
def index():
    context = {
        "contact_email": "emeric.dynomant@gmail.com",
        "home": "https://data-baguette.com",
        "carte_risque_massifs": get_risk_map(html=True)
    }
    html_template = render_template("index.html", **context)
    return html_template

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
