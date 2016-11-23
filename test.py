
from skribble.client import ApiClient
from skribble import Skribble
from skribble import logger
from skribble.rules.background import Background
from skribble.rules.hydrator.json import JsonHydrator

logger.info('No skribble yet')
try:
    # from skribble import Skribble
    skribble = Skribble(skribble_id="8771dcc2-68ad-11e6-aecc-9bfc4b094892",
                        skribble_url="https://api-qa.changemyworldnow.com/user/a0175b78-655e-11e6-9d67-60324a37494e/skribble/8771dcc2-68ad-11e6-aecc-9bfc4b094892",
                        post_back="https://api-qa.changemyworldnow.com/user/a0175b78-655e-11e6-9d67-60324a37494e/skribble/8771dcc2-68ad-11e6-aecc-9bfc4b094892/notice",
                        show_preview=False)

    client = ApiClient(skribble_to_process=skribble)

    data = client.get_skribble_data()

    client.report_complete()
    JsonHydrator.hydrate_background('{}');
except Exception:
    logger.exception('Exception')
    print 'here'

