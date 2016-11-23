"""
Skribble Client
"""

import json

from skribble import config
from skribble import logger

import requests
from base_client import BaseClient
from requests.auth import HTTPBasicAuth  # allows basic HTTP Auth


class ApiClient(BaseClient):
    """
    Used to handle calls to the api
    """

    # Settings for Requests
    verify_ssl = config.getboolean('cmwn', 'verify_ssl')
    max_redirects = config.getint('cmwn', 'max_redirects')

    auth = HTTPBasicAuth(username=config.get('cmwn', 'api_user'),
                         password=config.get('cmwn', 'api_pass'))
    post_headers = {'Content-Type': 'application/json'}

    def __init__(self, skribble_to_process):
        object.__init__(self)
        self.skribble = skribble_to_process

    def report_status(self, status):
        """
        Used to report a status back for the skribble
        :param status:
        :return:
        """
        if status not in self.skribble.allowed_status:
            raise Exception('Invalid status: %s' % status)

        logger.info('Reporting status: %s to: %s' % (status, self.skribble.post_back))
        data = json.dumps({'status': status})

        response = requests.post(self.skribble.post_back,
                                 data=data,
                                 headers=self.post_headers,
                                 auth=self.auth,
                                 verify=self.verify_ssl)

        logger.debug('Status Response code: %s' % response.status_code)

        if response.status_code in [201, 200]:
            logger.debug('Successfully reported status to api')
            return True

        logger.error('Failed to report status: %s to: %s' % (status, self.skribble.post_back))
        logger.error(response.content)
        return False

    def get_skribble_data(self):
        """
        Gets the skribble data from the API
        :return:
        """

        logger.info('Fetching skribble data from: %s' % self.skribble.skribble_url)
        response = self.get(self.skribble.skribble_url)
        logger.debug('Skribble response code: %s' % response.status_code)

        if response.status_code == 200:
            logger.debug('Skribble data: %s' % response.content)
            return response.content

        raise Exception('Invalid response code: %s from: %s' % (response.status_code, self.skribble.skribble_url))

    def report_error(self):
        """
        Helper to report error easily
        :return:
        """

        return self.report_status(self.skribble.ERROR)

    def report_processing(self):
        """
        Helper to report processing
        :return:
        """
        return self.report_status(self.skribble.PROCESSING)

    def report_complete(self):
        """
        Helper to report complete
        :return:
        """
        return self.report_status(self.skribble.COMPLETE)

    def _hydrate_skribble_rules(self, content):
        """
        Takes the json response from skribble api and creates the correct rules
        :param content:
        :return:
        """

        return

__all__ = ['ApiClient', 'BaseClient']
