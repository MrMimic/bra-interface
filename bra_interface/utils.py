"""Utilitary package.
"""
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pymysql
from dotenv import load_dotenv


class DbCredentials:
    """Class handling credentials.
    """

    def __init__(self,
                 username: str = None,
                 password: str = None,
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 logger: logging.Logger = None) -> None:
        self.logger = logger or get_logger()
        # Load .env file
        load_dotenv()
        self.user = username or self._try_to_get_key("MYSQL_USER")
        self.password = password or self._try_to_get_key("MYSQL_PWD")
        self.host = host or self._try_to_get_key("MYSQL_HOST")
        self.port = port or int(self._try_to_get_key("MYSQL_PORT"))
        self.database = database or self._try_to_get_key("MYSQL_DB")
        self.table = database or self._try_to_get_key("MYSQL_TABLE")
        # Say hello
        self._handshake()

    def _handshake(self) -> None:
        """Get the number of already treated files in the DB.
        """
        query = f"""
            SELECT COUNT(original_link) AS nb_files
            FROM {self.database}.{self.table}
        """
        connection = pymysql.connect(host=self.host,
                                     user=self.user,
                                     password=self.password,
                                     port=self.port,
                                     db=self.database)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)
            self.inserted_files = cursor.fetchone()["nb_files"]
            self.logger.info(f"Found {self.inserted_files} files in the database.")

    @staticmethod
    def _try_to_get_key(key: str) -> Optional[str]:
        """Try to get the key from the environment.
        """
        try:
            return os.environ[key]
        except KeyError:
            return None

    def get_connection_string(self) -> str:
        """Return a connection string.
        """
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}"

    def __repr__(self) -> str:
        """Return a string representation of the credentials.
        """
        output = f"""
        Found database parameters:
            \t- User: {self.user}
            \t- Password: {'*' * (len(list(self.password)) + 1)}
            \t- Host: {self.host}
            \t- Port: {self.port}
        """
        return output


@dataclass
class FrenchMonthsNumber:
    """French months numbers.
    """
    janvier: int = 1
    février: int = 2
    mars: int = 3
    avril: int = 4
    mai: int = 5
    juin: int = 6
    juillet: int = 7
    août: int = 8
    septembre: int = 9
    octobre: int = 10
    novembre: int = 11
    décembre: int = 12

    def get_month_number(self, month: str) -> int:
        """Return the month number.
        """
        return getattr(self, month.lower())

    def get_month_name(self, month_number: int) -> str:
        """Return the month name.
        """
        return [month for month in dir(self) if getattr(self, month) == month_number][0]


class StabiliteManteauKeys():
    """
    Under the "Stabilité du manteau neigeux" text bloc, the keys of the text are not consistents.
    To structure them, for now, this class only store words that should be retireved.
    """

    def __init__(self):
        self.situation_avalancheuse_typique: List[str] = ["typique", "avalancheuse"]
        self.departs_spontanes: List[str] = ["spontané", "naturels"]
        self.declanchements_provoques: List[str] = [
            "skieurs", "déclanchement", "déclenchements", "provoqués", "declenchements", "accidentels"
        ]

    def retrieve_best_match(self, text: str) -> Optional[str]:
        """Retrieve the best match of a text in the list of keys.
        """
        for key, words in self.__dict__.items():
            for word in words:
                if word in text:
                    return key
        return None


def get_logger(base_path: str = "logs", file_name: str = None) -> logging.Logger:
    """Define and returns a logger.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # Format
    formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
    # Stream handler
    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    # File handler
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    if not file_name:
        execution_date = datetime.today().strftime("%Y%m%d")
        file_name = f"{execution_date}_bra_database.log"
    log_path = os.path.join(base_path, file_name)
    if os.path.exists(log_path):
        os.remove(log_path)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
