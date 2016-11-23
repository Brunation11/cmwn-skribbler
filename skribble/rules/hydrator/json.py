from skribble import logger

from skribble.rules.background import Background


class JsonHydrator:
    """
    Takes JSON Data and hydrates it to skribble rules
    """

    def __init__(self, json):
        logger.debug('Hydrating json to rules')
        self.background = self.hydrate_background(json['rules'])

    def hydrate_background(self, json):
        """
        Creates a background rule from json
        :param json:
        :return:
        """

        if json['background'] is None:
            raise

        bg_json = json['background']
        background = Background(
            asset_src=bg_json['src'],
            asset_name=bg_json['name'],
            asset_id=bg_json['media_id'],
            asset_mime_type=bg_json['mime_type'],
            asset_can_overlap=bg_json['can_overlap'],
            asset_hash=bg_json['check']['value'],
            asset_hash_type=bg_json['check']['type'],
            asset_type=bg_json['asset_type']
        )
        return background

    def get_background(self):
        return self.background

__all__ = ['JsonHydrator']
