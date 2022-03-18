"""Insert structured data into a GCP MySQL database.
"""
import logging
from typing import Any, List, get_type_hints

import pymysql
from pymysql.err import IntegrityError

from bra_interface.utils import DbCredentials, get_logger


class BraDatabase():
    """Insert structured data into an SQL database.
    """

    def __init__(self, credentials: DbCredentials, logger: logging.Logger = None) -> None:
        self.credentials = credentials
        # Logger
        self.logger = logger or get_logger()

    def __enter__(self) -> Any:
        """Get a connection.
        """
        self.connection = pymysql.connect(host=self.credentials.host,
                                          user=self.credentials.user,
                                          password=self.credentials.password,
                                          port=self.credentials.port,
                                          db=self.credentials.database)
        return self

    def __exit__(self, *exec_info) -> None:
        """Clear the connection
        """
        self.connection.commit()
        self.connection.close()

    def get_cursor(self) -> pymysql.cursors.DictCursor:
        """Get a cursor.
        """
        return self.connection.cursor(pymysql.cursors.DictCursor)

    def exec_query(self, query: str, data: Any = None, output: bool = True) -> Any:
        """Execute a query.
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            try:
                if data:
                    cursor.execute(query, data)
                else:
                    cursor.execute(query)
            except IntegrityError as error:
                self.logger.error(str(error))
                return None
            self.connection.commit()
            if output:
                return cursor.fetchall()
            return None
