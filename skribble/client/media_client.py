"""
Client for talking to the media server
"""

from skribble import config


class MediaClient:
    """
    Handles downloading assets from the media server
    """
    verify_ssl = config.getboolean('media', 'verify_ssl')
    max_redirects = config.getint('media', 'max_redirects')

    def __init__(self, asset):
        if isinstance(asset, 'BaseRule') is False:
            raise Exception('Invalid Asset passed to Media Client')

        self.asset = asset
