"""
"""
from datetime import datetime
import os
from bra_interface.connection import BraDatabase
from bra_interface.utils import DbCredentials, get_logger

from dotenv import load_dotenv

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
