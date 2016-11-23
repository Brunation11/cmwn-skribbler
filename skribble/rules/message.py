"""
Background rule
"""

from skribble.rules.base import BaseRule


class Message(BaseRule):
    """
    A Background rule
    """

    def __init__(self,
                 asset_src=None,
                 asset_name=None,
                 asset_id=None,
                 asset_type=None,
                 asset_mime_type=None,
                 asset_can_overlap=None,
                 asset_hash=None,
                 asset_hash_type=None):
        BaseRule.__init__(
            self,
            asset_src=asset_src,
            asset_name=asset_name,
            asset_id=asset_id,
            asset_type=asset_type,
            asset_mime_type=asset_mime_type,
            asset_can_overlap=asset_can_overlap,
            asset_hash=asset_hash,
            asset_hash_type=asset_hash_type
        )

        if self.asset_type != self.MESSAGE:
            raise Exception('Invalid message asset type passed')
