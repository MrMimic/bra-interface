"""Get and format BRAs.
"""
import logging
from bra_interface.connection import BraDatabase
from bra_interface.utils import DbCredentials, get_logger


class BulletinsRisquesAvalanches():
    def __init__(self, logger: logging.Logger = None) -> None:
        self.credentials = DbCredentials()
        self.logger = logger if logger is not None else get_logger()
