# The skribble process will take in the skribble json specification and create a flattened image. The process MUST
# accept in the id of the skribble to process. The skribble process MUST complete the following validataion
# on the specification:

# All assets requested to be included MUST exist in the media server
# All assets requested MUST match the check field from the media service in the matching specification
# All assets that cannot overlap MUST NOT have points that intersect on the grid based on type of asset
# For Effect, Sound and Background, there MUST NOT be more than one instance of that type
# Status MUST BE "PROCESSING"

# The generated image MUST BE a png file that is web optimized. Once the image is generated, the image is then
# POSTed back to the api with the skribble id.

# Data Format

# When the __/a/:media_id endpoint is called, the data that is returned MUST be JSON encoded with the REQUIRED fields:

# media_id REQUIRED The id of the media
# check REQUIRED The MD5 Checksum of the asset that is used to verify the validaity of the asset
# mime_type REQUIRED The MIME type of the asset.
# type REQUIRED An enum of either:
# Item: MUST BE png or gif
# Background: MUST BE png or gif
# Message: MUST BE png or
# Sound: MUST BE mp3
# Effect: MUST BE javascript file (will contain all CSS and Images needed for the effect to go off)
# category OPTIONAL A custom category that this asset belongs too
# order OPTIONAL ordering of the asset when displayed to a user. MUST BE a positive integer
# can_overlap REQUIRED boolean dictating wwhetherthe asset can be overlapped on the skribble grid
# src REQUIRED the FQDN URL to access the asset

# Order of image manipulation
# position
# scale
# rotate

from __future__ import print_function
from PIL import Image, ImageChops, ImageOps  # Python Image Library
from rollbar.logger import RollbarHandler  # allows different config for rollbar
import logging  # info, error, debug messages
import requests  # open arbitrary resources from url
import cStringIO  # create string buffer (used to open virtual image from url)
import json  # pretty print json
import boto3  # aws client
import hashlib  # encode and decode in sha1/md5/etc
import rollbar  # rollbar integration
import config  # config file
import pprint  # pretty prints data
import sys
from requests.auth import HTTPBasicAuth  # allows basic HTTP Auth

# initiate rollbar
rollbar.init(
    config.rollbar_access_token,
    config.rollbar_env,
    timeout=30)

# report ERROR and above to Rollbar
rollbar_handler = RollbarHandler()
rollbar_handler.setLevel(logging.INFO)

real = logging.getLogger(__name__)
real.setLevel(logging.INFO)
real.addHandler(rollbar_handler)

print(config.media_base_url)

class SkribbleAdapter(logging.LoggerAdapter):
    """
    Custom adapter to put the skribble id into the logger
    """
    skribble_id = None

    def process(self, msg, kwargs):
        return 'Skribble [%s] %s' % (self.skribble_id, msg), kwargs


logger = SkribbleAdapter(real, {})


class Skribble:
    # init instance by extracting background, items, and messages
    def __init__(self, event):
        logger.info('Received skribble:\n{}'.format(pprint.pformat(event)))

        self.skribble_id = event['skribble_id']
        logger.skribble_id = self.skribble_id

        self.url = event['skribble_url']
        self.post_back = event['post_back']
        self.show_preview = event['preview']
        self.media_url_base = event['media_url'] + '/{}'

        logger.debug('Downloading skribble data from: {}'.format(self.url))

        skribble_response = self.url_response(self.url)
        logger.debug('Received skribble data:\n{}'.format(pprint.pformat(skribble_response)))

        self.skribble_json = skribble_response.json()

        self.background_asset = self.skribble_json['rules']['background']
        self.item_assets = self.skribble_json['rules']['items']
        self.message_assets = self.skribble_json['rules']['messages']
        self.background = None
        self.layers = []
        self.render()

    #########################
    # HELPER METHODS
    #########################
    # validates downloaded asset matches expected content type from media server
    def valid_type(self, raw_asset, response):
        logger.debug('Validating mime_type of asset: {}'.format(raw_asset['media_id']))
        mime_type = raw_asset['mime_type']

        logger.debug('Expected MIME: {}'.format(mime_type))
        logger.debug('Content type from media service: {}'.format(response.headers['Content-Type']))

        if response.headers['Content-Type'] == mime_type:
            logger.debug('Valid Content-Type')
            return True

        raise Exception(
            'Invalid type for asset: {}, expected {}, instead saw {}'.format(raw_asset['media_id'], mime_type,
                                                                             response.info()['Content-type']))

    # Validates the assets checksum by comparing it to the media server
    def validate_checksum(self, raw_asset, response):
        if config.verify_hash is False:
            logger.debug('Not validating hash')
            return True

        logger.debug('Validating checksum of asset: {}'.format(raw_asset['media_id']))

        # verify check type
        type_of_check = raw_asset['check']['type']
        expected_hash = raw_asset['check']['value']

        if type_of_check == 'sha1':
            logger.debug('Using SHA1')
            hash_value = hashlib.sha1(response.content).hexdigest()
        elif type_of_check == 'md5':
            logger.info('Using MD5')
            hash_value = hashlib.md5(response.content).hexdigest()
        else:
            raise Exception('Unsupported checksum type: {}'.format(type_of_check))

        logger.debug('Expected value: {}'.format(expected_hash))
        logger.debug('Calculated value: {}'.format(hash_value))

        if hash_value == expected_hash:
            logger.debug('Valid checksum')
            return True
        else:
            raise Exception(
                'Asset {} failed checksum validation! expected {} and calculated {}'.format(raw_asset['media_id'],
                                                                                            expected_hash, hash_value))

    # Fetches data from a url
    def url_response(self, url, redirect_count=0):

        if redirect_count > 3:
            raise Exception('Exceeded redirect counts for {}'.format(url))

        logger.debug('Downloading data from {}'.format(url))

        response = requests.get(url, stream=True, timeout=60, auth=HTTPBasicAuth(config.api_user, config.api_pass),
                                verify=config.verify_ssl)
        logger.debug('Status Code: {}'.format(response.status_code))

        if response.status_code == 200:
            return response

        if response.status_code == 301 | response.status_code == 302:
            logger.debug('Redirect to: {}'.format(response.headers['Location']))
            redirect_count += 1

            return self.url_response(response.headers['Location'], redirect_count)

        raise Exception('Invalid response code {} from: {}'.format(response.status_code, url))

    # Reports an error to the api
    def report_error_to_api(self):
        try:
            self.report_to_api('error')
        except:
            logger.error('Unable to report error to API')

    # Reports a status back to the API
    def report_to_api(self, status):
        logger.info('Reporting {} to api'.format(status))
        # Build the request
        headers = {'Content-Type': 'application/json'}

        data = json.dumps({'status': status})

        logger.debug('Submitting to {}\n with data: {}\n using headers: {}'.format(self.post_back, pprint.pformat(data),
                                                                                   pprint.pformat(headers)))

        response = requests.post(self.post_back, data=data, headers=headers,
                                 auth=HTTPBasicAuth(config.api_user, config.api_pass), verify=config.verify_ssl)
        # server response

        if response.status_code != 201:
            logger.debug(response.content)
            raise Exception(
                'Unexpected response code from API, expected 201, saw {}, body: {}'.format(response.status_code,
                                                                                           response.content))

        logger.debug('Successfully submitted status {}'.format(self.skribble_json['skribble_id']))

    # create string buffer for reading and writing data
    def string_buffer(self, response):
        return cStringIO.StringIO(response.content)

    def upload_skribble_to_s3(self, rendered_asset):
        logger.info('Uploading to S3')
        # create a key (file name) based on skribble id
        file_name = '{}.png'.format(self.skribble_id)
        # connect to s3
        s3 = boto3.resource('s3')

        # upload in memory buffer to bucket
        # s3.Bucket(config.aws_s3_bucket).put_object(Key=key, Body=rendered_asset.getvalue())
        s3.Object(config.aws_s3_bucket, file_name).put(Body=rendered_asset.getvalue(), ContentType='image/png')

    # open image (currently used for debugging)
    def preview(self, rendered_asset):
        logger.info('Loading Preview')
        rendered_asset.show()

    #########################
    # IMAGE METHODS
    #########################

    # load image from a file in this case from the string buffer

    def image(self, asset_file):
        logger.debug('Opening image')
        return Image.open(asset_file).convert('RGBA')

    # get an assets top left coordinate
    def get_anchor_coordinates(self, raw_asset):
        x = float(raw_asset['state']['left'])
        y = float(raw_asset['state']['top'])
        logger.debug('Found Anchor points: {}, {}'.format(x, y))
        return x, y

    # get an assets scale if any
    def get_scale_value(self, raw_asset):
        scale_value = float(raw_asset['state']['scale'])
        logger.debug('Scale value: {}'.format(scale_value))
        return scale_value

    # get an assets rotation if any
    def get_rotation_value(self, raw_asset):
        rotation_value_radians = float(raw_asset['state']['rotation'])
        logger.debug('Rotation value in radians: {}'.format(rotation_value_radians))
        rotation_value_degrees = rotation_value_radians * 57.2958
        logger.info('Calculating rotation value in degrees...')
        logger.debug('Rotation value in degrees: {}'.format(rotation_value_degrees))
        return rotation_value_degrees

    # calculate all corners after asset is scaled
    def calculate_corners(self, processed_asset):
        corners = {}

        # dimensions
        w, h = processed_asset['resized_asset'].size
        corners['top_left'] = processed_asset['n_coordinates']
        corners['top_right'] = ((processed_asset['n_coordinates'][0] + w), processed_asset['n_coordinates'][1])
        corners['bottom_right'] = (
            (processed_asset['n_coordinates'][0] + w), (processed_asset['n_coordinates'][1] + h))
        corners['bottom_left'] = (processed_asset['n_coordinates'][0], (processed_asset['n_coordinates'][1] + h))
        logger.debug('Calculated corners: $s'.format(pprint.pformat(corners)))
        return corners

    # verify that non-overlap assets don't collide
    # TODO Match up with front end collision detection
    def collision_detected(self, base_asset, processed_assets):
        base_corners = base_asset['corners']
        logger.debug('Compare Asset Corners:\n{}'.format(pprint.pformat(base_corners)))

        for asset in processed_assets:
            asset_corners = asset['corners']
            logger.debug('Asset Corners:\n{}'.format(pprint.pformat(asset_corners)))

            # raise Exception('Collision detected between assets {}, {}', base_asset['raw']['media_id'],
            #                 asset['raw']['media_id'])

            logger.debug('No collision detected between assets {}, {}'.format(base_asset['raw']['media_id'],
                                                                              asset['raw']['media_id']))

    # validate an assets url and type
    def validate_and_get_asset(self, raw_asset):
        logger.info('Downloading media data for asset: {}'.format(raw_asset['media_id']))
        logger.debug('Raw Asset data:\n {}'.format(pprint.pformat(raw_asset)))
        media_data_url = self.media_url_base.format(raw_asset['media_id'])

        logger.debug('Media Url: {}'.format(media_data_url))

        media_data = self.url_response(media_data_url).json()
        logger.debug('Received Media data:\n {}'.format(pprint.pformat(media_data)))

        if raw_asset['media_id'] != media_data['media_id']:
            raise Exception('Media IDs did not match')

        response = self.url_response(media_data['src'])
        logger.info('Validating {}'.format(media_data['media_id']))

        self.valid_type(media_data, response)
        self.validate_checksum(media_data, response)

        logger.debug('Validated url, type, and checksum of {}'.format(media_data['media_id']))

        asset_file = self.string_buffer(response)
        logger.info('Fetching image for {}'.format(media_data['media_id']))
        return self.image(asset_file)

    # recalculate new coordinates after asset is scaled

    def recalculate_coordinates(self, processed_asset):
        logger.debug('Recalculating coordinates for asset: {} '.format(pprint.pformat(processed_asset)))

        # original dimensions
        o_width, o_height = processed_asset['asset'].size
        # realized dimensions

        r_width, r_height = processed_asset['resized_asset'].size

        nx = processed_asset['raw']['state']['left']
        ny = processed_asset['raw']['state']['top']

        # if asset has shrunk
        if (o_width > r_width) & (o_height > r_height):
            logger.info('Scaling image down')
            # dimension differences to calculate new coordinates
            width_difference = o_width - r_width
            height_difference = o_height - r_height
            # set new coordinates for x & y
            nx = (processed_asset['coordinates'][0] + (width_difference / 2))
            ny = (processed_asset['coordinates'][1] + (height_difference / 2))

        logger.debug('New Coordinates: {}'.format(pprint.pformat([nx, ny])))
        return nx, ny

    # find the pivot point for the asset now that it has moved
    def get_rotation_pivot(self, processed_asset):
        logger.debug('Calculating rotation pivot point: '.format(pprint.pformat(processed_asset)))

        # calculate x coordinate of center
        center_x = processed_asset['n_coordinates'][0] + (processed_asset['resized_asset'].size[0] / 2)

        # calculate y coordinate of center
        center_y = processed_asset['n_coordinates'][1] + (processed_asset['resized_asset'].size[1] / 2)
        logger.debug('Pivot Point: {} '.format(pprint.pformat([center_x, center_y])))
        return center_x, center_y

    #########################
    # TRANSFORM METHODS
    #########################

    # layer assets onto a base at given coordinates
    def paste(self, base, layer, coordinates=None):
        # add layer to base
        base.paste(layer, (int(coordinates[0]), int(coordinates[1])), layer)
        return base

    # resize an asset
    def resize(self, processed_asset):
        # original width & height of asset
        o_width = round((processed_asset['asset'].size[0]), 14)
        o_height = round((processed_asset['asset'].size[1]), 14)
        scale_value = float(processed_asset['scale_value'])

        # resized width & height
        r_width = int(o_width * scale_value)
        r_height = int(o_height * scale_value)

        # resized asset
        logger.debug('Resized asset {}'.format(processed_asset['raw']['media_id']))
        return processed_asset['asset'].resize((r_width, r_height), Image.ANTIALIAS)

    # center asset for rotation
    def center(self, base, processed_asset):
        # dimensions for base
        base_width, base_height = base.size
        # center of base
        center_x = base_width / 2
        center_y = base_height / 2
        # dimensions for asset
        asset_width, asset_height = processed_asset['resized_asset'].size
        x = center_x - (asset_width / 2)
        y = center_y - (asset_height / 2)
        logger.debug('Centered asset {}'.format(processed_asset['raw']['media_id']))
        return self.paste(base, processed_asset['resized_asset'], (x, y))

    # crop asset from its center
    def crop_from_center(self, processed_asset, proposed_size):

        # img size
        width, height = processed_asset['asset'].size

        # proposed dimensions
        proposed_width, proposed_height = proposed_size

        # coordinates for 4-tuple (That's Too-ule not Tup-ule)
        left = (width - proposed_width) / 2
        top = (height - proposed_height) / 2
        right = proposed_width + left
        bottom = proposed_height + top

        # crop asset from center
        logger.debug('Cropped asset {}'.format(processed_asset['raw']['media_id']))
        return processed_asset['asset'].crop((left, top, right, bottom))

    # resize asset to fit within proposed size
    def resize_from_center(self, processed_asset, proposed_size):
        # asset dimensions
        width, height = processed_asset['asset'].size

        # proposed dimensions
        proposed_width, proposed_height = proposed_size

        # calculate whether to scale to proposed width or proposed height
        width_difference = proposed_width - width
        height_difference = proposed_height - height

        # if width requires scaling priority scale by proposed width
        logger.debug('Resized asset {} from center'.format(processed_asset['raw']['media_id']))

        if width_difference > height_difference:
            r_width = proposed_width
            r_height = int((height * proposed_width) / width)
            return processed_asset['asset'].resize((r_width, r_height), Image.ANTIALIAS)

        r_height = proposed_height
        r_width = int((width * proposed_height) / height)
        return processed_asset['asset'].resize((r_width, r_height), Image.ANTIALIAS)

    # format background
    def transform_background(self, base, processed_asset):
        logger.info('Transforming background')

        # if sizes are equal do nothing
        if base.size == processed_asset['asset'].size:
            return processed_asset['asset']

        base_width, base_height = base.size
        asset_width, asset_height = processed_asset['asset'].size
        # if either the width or height of the layer are smaller then the width or height of the
        # base resize the layer to cover the base area

        if asset_width < base_width | asset_height < base_height:
            # resize the layer
            logger.debug('Resizing background')
            return self.resize_from_center(processed_asset, base.size)

        # crop the larger layer from center to fit exactly within the base area
        logger.debug('Cropping background')
        return self.crop_from_center(processed_asset, base.size)

    def position_scale_rotate(self, processed_asset):
        logger.info('Positioning Asset')

        base = self.render_canvas()

        # # dimensions for base
        base_width, base_height = base.size
        logger.debug('base height and width: {}, {}'.format(base_width, base_height))

        # # dimensions for asset
        asset_width, asset_height = processed_asset['resized_asset'].size
        logger.debug('asset height and width: {}, {}'.format(asset_height, asset_width))

        # # point of pivot (asset centerpoint)
        pivot_x, pivot_y = processed_asset['pivot']
        logger.debug('pivot point: {} {}'.format(pivot_x, pivot_y))

        # # center of base
        center_x = base_width / 2
        center_y = base_height / 2
        logger.debug('center point: {}, {}'.format(center_x, center_y))

        # dimensions for asset
        x = center_x - (asset_width / 2)
        y = center_y - (asset_height / 2)
        logger.debug('top left point: {}, {}'.format(x, y))

        # determine offset to reposition centered image after rotation
        x_shift = processed_asset['n_coordinates'][0] - x
        y_shift = processed_asset['n_coordinates'][1] - y
        logger.debug('shifted point: {} {}'.format(x_shift, y_shift))

        # calculate padding for canvas
        x_padding = abs(x_shift)
        y_padding = abs(y_shift)
        logger.debug('Canvas padding: {} {}'.format(x_padding, y_padding))

        # center image
        centered = self.center(base, processed_asset)
        # pad image
        padded = ImageOps.expand(centered, border=(int(x_padding), int(y_padding)))
        # rotate image
        logger.info('Rotating Asset')
        rotated = padded.rotate(-processed_asset['rotation_value'])
        # reposition image using offset and reset asset in dictionary
        logger.info('Re-Positioning asset')
        processed_asset['asset'] = ImageChops.offset(rotated, int(x_shift), int(y_shift))

        # crop bleed from offset
        logger.info('Scaling asset')
        cropped_asset = self.crop_from_center(processed_asset, base.size)
        return cropped_asset

    #########################
    # PREFLIGHT METHODS
    #########################

    # check background to see if cropping or resizing is required
    def preflight_background(self, base, raw_asset):
        logger.info('Performing background preflight')
        logger.debug('Background data:\n {}'.format(pprint.pformat(raw_asset)))
        # validate url, type, and generate asset
        if raw_asset is None:
            logger.warning('No background present, rendering white background')
            self.background = self.render_canvas(color=(255, 255, 255))
            return

        processed_asset = dict()
        processed_asset['raw'] = raw_asset
        processed_asset['asset'] = self.validate_and_get_asset(processed_asset['raw'])

        self.background = self.transform_background(base, processed_asset)
        logger.info('PASSED!')

    def preflight(self, asset_list):
        logger.info('Performing preflight')
        if asset_list is None:
            logger.warning('No assets present')
            return

        # store validated assets
        processed_assets = []

        # iterate through assets list
        for asset in asset_list:
            logger.info('Preflighting asset {}'.format(asset['media_id']))
            logger.debug('Pre-processing asset {}'.format(asset['media_id']))

            # create a new dictionary to store values
            processed_asset = dict()
            # store reference to original asset

            processed_asset['raw'] = asset
            # validate url, type, and generate asset

            processed_asset['asset'] = self.validate_and_get_asset(processed_asset['raw'])

            # get scale value
            processed_asset['scale_value'] = self.get_scale_value(processed_asset['raw'])

            # get rotation value
            processed_asset['rotation_value'] = self.get_rotation_value(processed_asset['raw'])

            # resize asset
            processed_asset['resized_asset'] = self.resize(processed_asset)

            # get coordinates
            processed_asset['coordinates'] = self.get_anchor_coordinates(processed_asset['raw'])

            # new coordinates after resize
            processed_asset['n_coordinates'] = self.recalculate_coordinates(processed_asset)

            # calculate corners
            processed_asset['corners'] = self.calculate_corners(processed_asset)

            # calculate pivot for rotation
            processed_asset['pivot'] = self.get_rotation_pivot(processed_asset)

            processed_assets.append(processed_asset)

            logger.debug('Asset passed Preflight:\n {}'.format(pprint.pformat(processed_asset)))

        logger.info('Checking collision')
        for asset in processed_assets:
            # run collision test
            self.collision_detected(asset, processed_assets)

            # position scale and rotate asset
            transformed = self.position_scale_rotate(asset)
            # insert 0, transformed layer to layers list
            self.layers.append(transformed)

    # check items and perform necessary manipulations
    def preflight_items(self, items):
        logger.info('PREFLIGHT - ITEMS')
        self.preflight(items)
        logger.info('Passed!')

    # check messages and perform necessary manipulations
    def preflight_messages(self, messages):
        logger.info('PREFLIGHT - MESSAGES')
        self.preflight(messages)
        logger.info('Passed!')

    #########################
    # RENDER METHODS
    #########################

    # base canvas
    def render_canvas(self, size=(1280, 720), color=None):
        # create new image instance width default canvas size and no fill
        logger.info('Generating canvas')
        canvas = Image.new('RGBA', size, color)
        return canvas

    # render skribble
    def render(self):
        try:
            canvas = self.render_canvas()
            self.preflight_background(canvas, self.background_asset)
            self.preflight_items(self.item_assets)
            self.preflight_messages(self.message_assets)
        except Exception as error:
            # catch-all
            logger.exception(error)
            # self.report_to_api('error')
            return

        try:
            logger.info('RENDERING SKRIBBLE')
            canvas = Image.alpha_composite(canvas, self.background)

            logger.debug('Merging layers')
            for layer in self.layers:
                canvas = Image.alpha_composite(canvas, layer)
            logger.info('Writing to file')
            string_buffer = cStringIO.StringIO()
            canvas.save(string_buffer, 'PNG')
            # upload skribble to s3
            self.upload_skribble_to_s3(string_buffer)
            self.report_to_api('success')
        except Exception as error:
            # catch-all
            logger.exception(error)
            self.report_to_api('error')
            return

        if self.show_preview:
            logger.info('Opening preview')
            self.preview(canvas)


def handler(event, context):
    for record in event['Records']:
        try:
            logger.info('Recieved SNS Message: \n {}'.format(pprint.pformat(record)))
            message = json.loads(record['Sns']['Message'])
            message['preview'] = 0
            message['media_url'] = config.media_base_url
            Skribble(message)
        except:
            logger.exception('Fatal error during skramble: %s' % sys.exc_info()[0])


def handle_cli(message):
    try:
        Skribble(message)
    except Exception as error:
        logger.exception(error)
