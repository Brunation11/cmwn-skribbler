"""
Base client for making http calls
"""

from skribble import logger

import requests


class BaseClient:
    """
    Wrapper to make calls and follow redirects
    """

    def __init__(self, verify_ssl, max_redirects, auth=None, timeout=60):
        self.verify_ssl = verify_ssl
        self.max_redirects = max_redirects
        self.auth = auth
        self.timeout = timeout

    def get(self, url, redirect_count=0):
        """
        Gets the skribble data from the API
        :param url:
        :param redirect_count:
        :return:
        """

        if redirect_count > self.max_redirects:
            raise Exception('Exceeded redirect count for: %s' % url)

        logger.info('Fetching skribble data from: %s' % url)
        response = requests.get(url,
                                auth=self.auth,
                                verify=self.verify_ssl,
                                allow_redirects=False) # We do not want to keep redirecting

        logger.debug('Skribble response code: %s' % response.status_code)
        if response.status_code in [301, 302]:
            logger.info('Skribble has been redirected to: %s' % response.headers['Location'])
            redirect_count += 1
            return self.get(url=response.headers['Location'],
                            redirect_count=redirect_count)

        if response.status_code == 200:
            logger.debug('Skribble data: %s' % response)
            return response

        raise Exception('Invalid response code: %s from: %s' % (response.status_code, url))

__all__ = ['BaseClient']
