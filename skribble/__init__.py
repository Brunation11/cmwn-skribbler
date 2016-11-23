"""
Skribble Skrambler
"""

import logging
from rollbar.logger import RollbarHandler
import rollbar
import ConfigParser
import os
from decimal import *
from urlparse import urlparse
from exceptions import *
from skribble.rules.rules import SkribbleRules

skribble_context = Context(prec=14, rounding=ROUND_UP)

dir_path = os.path.dirname(os.path.realpath(__file__ + "../../"))

config = ConfigParser.RawConfigParser()
config.read(dir_path + "/skramble.cfg")

rollbar_handler = RollbarHandler()
rollbar_handler.setLevel(config.getint('rollbar', 'level'))

rollbar.init(config.get('rollbar', 'access_token'),
             config.get('rollbar', 'env'),
             version=config.get('rollbar', 'version'),
             timeout=30)

real = logging.getLogger(__name__)
real.setLevel(logging.DEBUG)
real.addHandler(rollbar_handler)


class SkribbleAdapter(logging.LoggerAdapter):
    """
    Custom adapter to put the skribble id into the logger
    """
    skribble_id = None

    def process(self, msg, kwargs):
        return 'Skribble [%s] %s' % (self.skribble_id, msg), kwargs


logger = SkribbleAdapter(real, {})


class ProcessSkribble(object):
    """
    Object that holds
    """

    __slots__ = ('_skribble_id', '_skribble_url', '_post_back', '_show_preview')

    def __new__(cls, skribble_id, skribble_url, post_back, show_preview=False):
        """
        Sets the skribble
        :param skribble_id:
        :param skribble_url:
        :param post_back:
        :param show_preview:
        """
        self = object.__new__(cls)

        self._skribble_id = skribble_id
        self._skribble_url = skribble_url
        self._post_back = post_back
        self._show_preview = bool(show_preview)
        logger.skribble_id = skribble_id
        return self

    @property
    def skribble_id(self):
        return self._skribble_id

    @property
    def skribble_url(self):
        return self._skribble_url

    @property
    def post_back(self):
        return self._post_back

    def show_preview(self):
        return self.show_preview()


class Skribble(object):
    """
    Immutable Object that holds all the skribble data
    """
    PROCESSING = 'processing'
    COMPLETE = 'success'
    ERROR = 'error'

    __slots__ = (
        '_created_by',
        '_created',
        '_updated',
        '_deleted',
        '_friend_to',
        '_read',
        '_rules',
        '_skribble_id',
        '_status',
        '_url',
        '_version'
    )

    def __new__(
            cls,
            created_by,
            created,
            updated,
            deleted,
            friend_to,
            read,
            rules,
            skribble_id,
            status,
            url,
            version
    ):
        self = object.__new__(cls)

        if self.uri_validator(url) is False:
            raise TypeError('The URL: % is not a valid skribble url' % url)

        if self.valid_status(status) is False:
            raise TypeError('Invalid skribble status: %s' % status)

        if isinstance(rules, SkribbleRules) is False:
            raise TypeError('Invalid rules passed to skribble')

        self._created_by = created_by
        self._created = created
        self._updated = updated
        self._deleted = deleted
        self._friend_to = friend_to
        self._read = bool(read)
        self._rules = rules
        self._skribble_id = skribble_id
        self._status = status
        self._url = url
        self._version = version
        return self

    @staticmethod
    def valid_status(status):
        return status in [Skribble.PROCESSING, Skribble.COMPLETE, Skribble.ERROR]

    @staticmethod
    def uri_validator(uri):
        try:
            result = urlparse(uri)
            return True if [result.scheme, result.netloc, result.path] else False
        except:
            return False

    @property
    def created_by(self):
        return self._created_by

    @property
    def created(self):
        return self._created

    @property
    def updated(self):
        return self._updated

    @property
    def deleted(self):
        return self._deleted

    @property
    def friend_to(self):
        return self._friend_to

    @property
    def is_read(self):
        return self._read

    @property
    def rules(self):
        return self._rules

    @property
    def skribble_id(self):
        return self._skribble_id

    @property
    def status(self):
        return self._status

    @property
    def url(self):
        return self._url

    @property
    def version(self):
        return self._version

    @staticmethod
    def set_precision(value):
        """
        Returns a new decimal with the agreed skribble precision
        :param value:
        :return:
        """

        return Decimal(str(value), context=skribble_context)


__all__ = ['set_precision', 'Skribble', 'SkribbleAdapter', 'logger']
