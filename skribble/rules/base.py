"""
Base asset rule
"""

import hashlib

from skribble import config
from skribble import logger


class BaseRule:
    """
    Base Asset rule
    """

    MESSAGE = 'message'
    ITEM = 'item'
    BACKGROUND = 'background'
    _HASH_MD5 = 'md5'
    _HASH_SHA1 = 'sha1'
    _ALLOWED_HASHES = [_HASH_MD5, _HASH_SHA1]
    _CHECK_HASH = config.getboolean('media', 'verify_file_hash')

    def __init__(self,
                 asset_src=None,
                 asset_name=None,
                 asset_id=None,
                 asset_type=None,
                 asset_mime_type=None,
                 asset_can_overlap=None,
                 asset_hash=None,
                 asset_hash_type=None):

        if asset_can_overlap is None:
            asset_can_overlap = False

        if isinstance(asset_can_overlap, bool) is False:
            raise TypeError('asset_can_overlap must be a boolean')

        self._asset_src = asset_src
        self._asset_name = asset_name
        self._asset_id = asset_id
        self._asset_type = asset_type
        self._asset_mime_type = asset_mime_type
        self._asset_hash = asset_hash
        self._asset_hash_type = asset_hash_type
        self._asset_can_overlap = asset_can_overlap

        if self._asset_hash_type is None:
            return

        if asset_hash_type not in self._ALLOWED_HASHES:
            raise Exception('Invalid hash type: %s' % asset_hash_type)

    def validate_asset_checksum(self, raw_asset):
        """
        Validates the check sum of the asset
        :param raw_asset:
        :return:
        """

        if self._CHECK_HASH is False:
            logger.info('Not checking file hash')
            return True

        if self._asset_hash_type == self._HASH_MD5:
            return self._validate_md5(raw_asset)

        if self._asset_hash_type == self._HASH_SHA1:
            return self._validate_sha1(raw_asset)

    def _validate_md5(self, raw_asset):
        """
        Checks the MD5 hash of a file
        :param raw_asset:
        :return:
        """
        logger.debug('Checking MD5 of file: %s' % self._asset_src)
        logger.debug('Expected MD5: %s' % self._asset_hash)
        hash_value = hashlib.md5(raw_asset).hexdigest()
        logger.debug('Calculated hash: %s' % hash_value)
        return hash_value == self._asset_hash

    def _validate_sha1(self, raw_asset):
        """
        Checks the SHA1 of a file
        :param raw_asset:
        :return:
        """
        logger.debug('Checking SHA1 of file: %s' % self._asset_src)
        logger.debug('Expected SHA1: %s' % self._asset_hash)
        hash_value = hashlib.md5(raw_asset).hexdigest()
        logger.debug('Calculated hash: %s' % hash_value)
        return hash_value == self._asset_hash

    def download_asset(self):
        """
        Downloads the asset from the media server
        :return:
        """
        # TOD
        return

    @property
    def asset_src(self):
        return self._asset_src

    @property
    def asset_name(self):
        return self._asset_name

    @property
    def asset_id(self):
        return self._asset_id

    @property
    def asset_type(self):
        return self._asset_type

    @property
    def asset_mime_type(self):
        return self._asset_mime_type

    @property
    def asset_hash(self):
        return self._asset_hash

    @property
    def asset_hash_type(self):
        return self._asset_hash_type

    @property
    def asset_can_overlap(self):
        return self._asset_can_overlap

__all__ = ['BaseRule']
