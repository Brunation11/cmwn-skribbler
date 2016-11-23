"""
Skribble Skrambler
"""

from skribble.client import ApiClient
from skribble import logger


class Skramble:
    """
    Skribble Skrambler
    """

    def __init__(self, skribble):
        if isinstance(skribble, 'Skribble') is False:
            raise Exception('Invalid skribble passed into skramble')

        self.logger = logger
        self.api_client = ApiClient(skribble_to_process=skribble)

