# Ths skribble process will take in the skribble json specification and create a flattened image. The process MUST accept in the id of the skribble to process. The skribble process MUST complete the following validataion on the specification:

      # All assets requested to be included MUST exist in the media server
      # All assets requested MUST match the check field from the media service in the matching specification
      # All assets that cannot overlap MUST NOT have points that intersect on the grid based on type of asset
      # For Effect, Sound and Background, there MUST NOT be more than one instance of that type
      # Status MUST BE "PROCESSING"

# The generated image MUST BE a png file that is web optimized. Once the image is generated, the image is then POSTed back to the api with the skribble id.

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
# can_overlap REQUIRED boolean diticating wether the asset can be overlapped on the skribble grid
# src REQUIRED the FQDN URL to access the asset

# Order of image manipulation
      # postion
      # scale
      # rotate

from __future__ import print_function
from PIL import Image, ImageChops, ImageOps
import logging, requests, cStringIO, json, boto3, os, sys, uuid, hashlib, base64 #rollbar
# PIL           Python Image Library
# requests       open arbitrary resources from url
# cstringIO     create string buffer (used to open virtual image from url)
# json          pretty print json
# boto3         aws client
# os            Miscellaneous operating system interfaces
# sys           System-specific parameters and functions
# uuid          UUID objects according to RFC 4122
# logging       info, error, debug messages
# base64        encoding for posting images
# hashlib       encode and decode in sha1/md5/etc
# rollbar       info, error, debug logging

# initiate logger
logger = logging.getLogger()
# set base level for logger
logger.setLevel(logging.DEBUG)
# create handler for logging at console lvl
ch = logging.StreamHandler(sys.stdout)
# attatch handler to logger
logger.addHandler(ch)

# initiate rollbar
# rollbar.init('POST_SERVER_ITEM_ACCESS_TOKEN', 'production')  # access_token, environment



class Skribble:
  # init instance by extracting background, items, and messages
  def __init__(self, event):
    url = event['skribble_url']
    self.media_url_base = 'https://media.changemyworldnow.com/a/{}'
    logger.info('Starting to process Skribble at {}...'.format(url))
    self.bucket = 'cmwn-skribble'
    self.post_back = event['post_back']
    self.skribble_json = requests.get(url).json()
    logger.debug(self.skribble_json)
    self.background_asset = self.skribble_json['rules']['background']
    logger.debug(self.background_asset)
    self.item_assets = self.skribble_json['rules']['items']
    logger.debug(self.item_assets)
    self.message_assets = self.skribble_json['rules']['messages']
    logger.debug(self.message_assets)
    self.background = None
    self.layers = []
    self.render()

#########################
# HELPER METHODS
#########################
  # validate response is imgage/png
  def valid_type (self, raw_asset, response):
    logger.info('Validating mime_type of {}...'.format(raw_asset['media_id']))
    mime_type = raw_asset['mime_type']
    logger.debug(mime_type)
    logger.info('Found file of content-type {}'.format(response.headers['Content-Type']))
    try:
      if response.headers['Content-Type'] == mime_type:
        logger.info('Validated type of {}...'.format(raw_asset['media_id']))
        return True
      else:
        logger.error('Invalid type for {}, expected {}, instead saw {}...'.format(raw_asset['media_id'], mime_type, response.info()['Content-type']))
        raise Exception('Invalid type for {}, expected {}, instead saw {}...'.format(raw_asset['media_id'], mime_type, response.info()['Content-type']))
        return False
    except:
      raise


  # verify assets by checksum type and value
  def validate_checksum(self, raw_asset, response):
    logger.info('Validating checksum of {}...'.format(raw_asset['media_id']))
    # verify check type
    type_of_check = raw_asset['check']['type']
    value = raw_asset['check']['value']
    if type_of_check == 'sha1':
      logger.info('Validating checksum of {} using sha1...'.format(raw_asset['media_id']))
      hash_value = hashlib.sha1(response.content).hexdigest()
      logger.debug(hash_value)
    elif type_of_check == 'md5':
      logger.info('Validating checksum of {} using md5...'.format(raw_asset['media_id']))
      hash_value = hashlib.md5(response.content).hexdigest()

    if hash_value == value:
      logger.info('Valid checksum for {}...'.format(raw_asset['media_id']))
      return True
    else:
      logger.error('{} failed checksum validation, expected checksum {}, instead saw {}...'.format(raw_asset['media_id'], value, hash_value))
      raise Exception('{} failed checksum validation, expected checksum {}, instead saw {}...'.format(raw_asset['media_id'], value, hash_value))
      return False

  # retrieve content from url
  def url_response (self, url, redirect_count=0):
    if redirect_count > 3:
      raise Exception('Exceeded redirect counts for {}...'.format(url))
    logger.info('Downloading Skribble data {}...'.format(url))
    logger.debug(url)
    response = requests.get(url, stream=True)
    logger.debug('{} returned status code {}'.format(url, response.status_code))
    if response.status_code == 200:
      return response
    elif response.status_code == 301 | response.status_code == 302:
      logger.debug('{} is being redirected to {}'.format(url, response.headers['Location']))
      redirect_count += 1
      return url_response(response.headers['Location'], redirect_count)
    raise Exception('{} has an invalid response code {}'.format(url, response.status_code))

  # create string buffer for reading and writing data
  def string_buffer (self, response):
    return cStringIO.StringIO(response.content)

  # load image from a file in this case from the string buffer
  def image (self, file):
    logger.debug('Opening image...')
    return Image.open(file).convert('RGBA')

  # open image (currently used for debugging)
  def preview (self, rendered_asset):
    rendered_asset.show()

  # get an assets top left coordinate
  def get_anchor_coordinates (self, raw_asset):
    self.logger('info', 'Getting asset anchor points for {}...'.format(raw_asset['media_id']))
    x = raw_asset['state']['left']
    y = raw_asset['state']['top']
    return x,y

  # get an assets scale if any
  def get_scale_value (self, raw_asset):
    self.logger('info', 'Getting scale value for {}...'.format(raw_asset['media_id']))
    return raw_asset['state']['scale']

  # get an assets rotation if any
  def get_rotation_value (self, raw_asset):
    self.logger('info', 'Getting rotation value for {}...'.format(raw_asset['media_id']))
    return raw_asset['state']['rotation']

  # calculate all corners after asset is scaled
  def calculate_corners (self, processed_asset):
    self.logger('info', 'Calculating corners for {}...'.format(processed_asset['raw']['media_id']))
    try:
      corners = {}
      # dimensions
      w, h = processed_asset['resized_asset'].size
      corners['top_left'] = processed_asset['n_coordinates']
      corners['top_right'] = ((processed_asset['n_coordinates'][0] + w), processed_asset['n_coordinates'][1])
      corners['bottom_right'] = ((processed_asset['n_coordinates'][0] + w), (processed_asset['n_coordinates'][1] + h))
      corners['bottom_left'] = (processed_asset['n_coordinates'][0], (processed_asset['n_coordinates'][1] + h))
      self.logger('info', 'Calculated corners for {}...'.format(processed_asset['raw']['media_id']))
      return corners
    except:
      self.logger('error', 'Unable to calculate corners for {}...'.format(processed_asset['raw']['media_id']))
      raise Exception('Unable to calculate corners for {}...'.format(processed_asset['raw']['media_id']))

  # # verify that non-overlapable assets don't collide
  def collision_detected (self, processed_base_asset, processed_assets):
    base_corners = processed_base_asset['corners']
    self.logger('info', 'Starting collision tests...')
    for asset in processed_assets:
      asset_corners = asset['corners']
      if processed_base_asset['raw'] != asset['raw']:
        if (not processed_base_asset['raw']['can_overlap']) | (not asset['raw']['can_overlap']):
          if (base_corners['top_left'][0] >= asset_corners['top_left'][0]) | (asset_corners['top_left'][0] >= base_corners['top_left'][0]):
            if (base_corners['top_left'][0] <= asset_corners['top_right'][0]) | (asset_corners['top_left'][0] <= base_corners['top_right'][0]):
              if (base_corners['top_left'][1] >= asset_corners['top_left'][1]) | (asset_corners['top_left'][1] >= base_corners['top_left'][1]):
                if (base_corners['top_left'][1] <= asset_corners['bottom_left'][1]) | (asset_corners['top_left'][1] <= base_corners['bottom_left'][1]):
                  self.logger('error', 'Error, collision detected between {} and {}...'.format(base['raw']['media_id'], asset['raw']['media_id']))
                  raise Exception('Error, collision detected between {} and {}...'.format(base['raw']['media_id'], asset['raw']['media_id']))
                  return True

  # validate an assets url and type
  def validate_and_get_asset (self, raw_asset):
    try:
      self.logger('info', 'Validating {}...'.format(raw_asset['media_id']))
      self.valid_url(raw_asset)
      self.valid_type(raw_asset)
      self.validate_checksum(raw_asset)
      self.logger('info', 'Validated url, type, and checksum of {}...'.format(raw_asset['media_id']))
    except:
      raise

    try:
      response = self.url_response(raw_asset)
      file = self.string_buffer(response)
      self.logger('info', 'Fetching image for {}...'.format(raw_asset['media_id']))
      return self.image(file)
    except:
      self.logger('error', 'Unable to retrieve asset for {}...'.format(raw_asset['media_id']))
      raise Exception('Unable to retrieve asset for {}...'.format(raw_asset['media_id']))

  # recalculate new coordinates after asset is scaled
  def recalculate_coordinates (self, processed_asset):
    self.logger('info', 'Recalculating coordinates for {}...'.format(processed_asset['raw']['media_id']))
    try:
      # original dimensions
      o_width, o_height = processed_asset['asset'].size
      # resized dimensions
      r_width, r_height = processed_asset['resized_asset'].size
      # if asset has shrunk
      if (o_width > r_width) & (o_height > r_height):
        # dimension differences to calculate new coordinates
        width_difference = o_width - r_width
        height_difference = o_height - r_height
        # set new coordinates for x & y
        nx = (processed_asset['coordinates'][0] + (width_difference / 2))
        ny = (processed_asset['coordinates'][1] + (height_difference / 2))
      # if asset has expanded
      elif (o_width < r_width) & (o_height < r_height):
        # dimension differences to calculate new coordinates
        width_difference = r_width - o_width
        height_difference = r_height - o_height
        # set new coordinates for x & y
        nx = (processed_asset['coordinates'][0] - (width_difference / 2))
        ny = (processed_asset['coordinates'][1] - (width_difference / 2))
      self.logger('info', 'Recalculated coordinates for {}...'.format(processed_asset['raw']['media_id']))
      return (nx,ny)
    except:
      self.logger('error', 'Unable to recalculate coordinates for {}...'.format(processed_asset['raw']['media_id']))
      raise Exception('Unable to recalculate coordinates for {}...'.format(processed_asset['raw']['media_id']))

  def get_rotation_pivot (self, processed_asset):
    self.logger('info', 'Calculating rotation pivot for...'.format(processed_asset['raw']['media_id']))
    try:
      # calculate x coordinate of center
      center_x = processed_asset['n_coordinates'][0] + (processed_asset['resized_asset'].size[0] / 2)
      # calculate y coordinate of center
      center_y = processed_asset['n_coordinates'][1] + (processed_asset['resized_asset'].size[1] / 2)
      self.logger('info', 'Calculated rotation pivot for...'.format(processed_asset['raw']['media_id']))
      return center_x, center_y
    except:
      self.logger('error', 'Unable to calculate rotation pivot for {}...'.format(processed_asset['raw']['media_id']))
      raise Exception('Unable to calculate rotation pivot for {}...'.format(processed_asset['raw']['media_id']))

  def upload_skribble (self, rendered_asset, post_path):
    self.logger('info', 'Starting Skribble upload for {}...'.format(self.skribble_json['skribble_id']))
    try:
      encoded_image = base64.b64encode(rendered_asset.read())
      # Build the request
      request = urllib2.Request(post_path)
      request.add_header('Content-type', 'application/json')
      body = {
        'skribble_id': self.skribble_json['skribble_id'],
        'skribble': encoded_image
      }
      request.add_data(body)
      # outgoing data
      self.logger('info', 'Outgoing api data {}...'.format(request.get_data()))
      # server response
      self.logger('info', 'Submitting Skribble to API...')
      self.logger('info', urllib2.urlopen(request).read())
      self.logger('info', 'Successfully submitted Skribble {}...'.format(self.skribble_json['skribble_id']))
    except:
      self.logger('error', 'Unable to upload Skribble {}...'.format(self.skribble_json['skribble_id']))
      raise Exception('Unable to upload Skribble {}...'.format(self.skribble_json['skribble_id']))

#########################
# TRANSFORM METHODS
#########################

  # layer assets onto a base at given coordinates
  def paste (self, base, layer, coordinates=None):
    # add layer to base
    base.paste(layer, (int(coordinates[0]),int(coordinates[1])), layer)
    return base

  # resize an asset
  def resize (self, processed_asset):
    self.logger('info', 'Resizing asset {}...'.format(processed_asset['raw']['media_id']))
    try:
      # original width & height of asset
      o_width = round((processed_asset['asset'].size[0]), 14)
      o_height = round((processed_asset['asset'].size[1]), 14)
      # resized width & height
      r_width = int(o_width * processed_asset['scale_value'])
      r_height = int(o_height * processed_asset['scale_value'])
      # resized asset
      self.logger('info', 'Resized asset {}...'.format(processed_asset['raw']['media_id']))
      return processed_asset['asset'].resize((r_width, r_height), Image.ANTIALIAS)
    except:
      raise Exception('Unable to resize asset {}...'.format(processed_asset['raw']['media_id']))

  # center asset for rotation
  def center (self, base, processed_asset):
    self.logger('info', 'Centering asset {}...'.format(processed_asset['raw']['media_id']))
    try:
      # dimensions for base
      base_width, base_height = base.size
      # center of base
      center_x = base_width / 2
      center_y = base_height / 2
      # dimensions for asset
      asset_width, asset_height = processed_asset['resized_asset'].size
      x = center_x - (asset_width / 2)
      y = center_y - (asset_height / 2)
      self.logger('info', 'Centered asset {}...'.format(processed_asset['raw']['media_id']))
      return self.paste(base, processed_asset['resized_asset'], (x,y))
    except:
      self.logger('error', 'Unable to center asset {}...'.format(processed_asset['raw']['media_id']))
      raise Exception('Unable to center asset {}...'.format(processed_asset['raw']['media_id']))

  # crop asset from its center
  def crop_from_center (self, processed_asset, proposed_size):
    self.logger('info', 'Cropping asset {} from center...'.format(processed_asset['raw']['media_id']))
    try:
      # img size
      width, height = processed_asset['asset'].size
      # proposed dimensions
      proposed_width, proposed_height = proposed_size
      # coordinates for 4-tuple
      left = (width - proposed_width) / 2
      top = (height - proposed_height) / 2
      right = proposed_width + left
      bottom = proposed_height + top
      # crop asset from center
      self.logger('info', 'Cropped asset {} from center...'.format(processed_asset['raw']['media_id']))
      return processed_asset['asset'].crop((left, top, right, bottom))
    except:
      self.logger('error', 'Unable to crop asset {} from center...'.format(processed_asset['raw']['media_id']))
      raise Exception('Unable to crop asset {} from center...'.format(processed_asset['raw']['media_id']))

  # resize asset to fit within proposed size
  def resize_from_center(self, processed_asset, proposed_size):
    self.logger('info', 'Resizing asset {} from center...'.format(processed_asset['raw']['media_id']))
    try:
      # asset dimensions
      width, height = processed_asset['asset'].size
      # proposed dimensions
      proposed_width, proposed_height = proposed_size
      # calculate whether to scale to proposed width or proposed height
      width_difference = proposed_width - width
      height_difference = proposed_height - height
      # if width requires scaling priority scale by proposed width
      self.logger('info', 'Resized asset {} from center...'.format(processed_asset['raw']['media_id']))
      if width_difference > height_difference:
        r_width = proposed_width
        r_height = int((height * proposed_width) / width)
        return processed_asset['asset'].resize((r_width, r_height), Image.ANTIALIAS)
        # else scale by proposed height
      else:
        r_height = proposed_height
        r_width = int((width * proposed_height) / height)
        return processed_asset['asset'].resize((r_width, r_height), Image.ANTIALIAS)
    except:
      self.logger('error', 'Unable to resize asset {} from center...'.format(processed_asset['raw']['media_id']))
      raise Exception('Unable to resize asset {} from center...'.format(processed_asset['raw']['media_id']))

  # format background
  def transform_background(self, base, processed_asset):
    try:
      self.logger('info', 'Formatting background asset {}...'.format(processed_asset['raw']['media_id']))
      # if sizes are equal do nothing
      if base.size == processed_asset['asset'].size:
        return processed_asset['asset']
      # else check if layer needs to be resized
      else:
        base_width, base_height = base.size
        asset_width, asset_height = processed_asset['asset'].size
        # if either the width or height of the layer are smaller then the width or height of the base resize the layer to cover the base area
        if asset_width < base_width | asset_height < base_height:
          # resize the layer
          self.logger('info', 'Formatting background asset {}...'.format(processed_asset['raw']['media_id']))
          return self.resize_from_center(processed_asset, base.size)
        # crop the oversized layer from center to fit exactly within the base area
        self.logger('info', 'Formatting background asset {}...'.format(processed_asset['raw']['media_id']))
        return self.crop_from_center(processed_asset, base.size)
    except:
      self.logger('error', 'Formatting background asset {}...'.format(processed_asset['raw']['media_id']))
      raise

  def position_scale_rotate(self, processed_asset):
    self.logger('info', 'Positioning asset {}...'.format(processed_asset['raw']['media_id']))
    self.logger('info', 'Scaling asset {}...'.format(processed_asset['raw']['media_id']))
    self.logger('info', 'Rotating asset {}...'.format(processed_asset['raw']['media_id']))
    try:
      base = self.render_canvas()
      # # dimensions for base
      base_width, base_height = base.size
      # # dimensions for asset
      asset_width, asset_height = processed_asset['resized_asset'].size
      # # point of pivot (asset centerpoint)
      pivot_x, pivot_y = processed_asset['pivot']
      # # center of base
      center_x = base_width / 2
      center_y = base_height / 2
      # dimensions for asset
      x = center_x - (asset_width / 2)
      y = center_y - (asset_height / 2)
      # determine offset to reposition centered image after rotation
      x_shift = processed_asset['n_coordinates'][0] - x
      y_shift = processed_asset['n_coordinates'][1] - y
      # calculate padding for canvas
      x_padding = abs(x_shift)
      y_padding = abs(y_shift)
      # center image
      centered = self.center(base, processed_asset)
      # pad image
      padded = ImageOps.expand(centered, border=(int(x_padding), int(y_padding)))
      # rotate image
      rotated = padded.rotate(-processed_asset['rotation_value'])
      # reposition image using offset and reset asset in dictionary
      processed_asset['asset'] = ImageChops.offset(rotated, int(x_shift), int(y_shift))
      # crop bleed from offset
      cropped_asset = self.crop_from_center(processed_asset, base.size)
      self.logger('info', 'Positioned asset {}...'.format(processed_asset['raw']['media_id']))
      self.logger('info', 'Scaled asset {}...'.format(processed_asset['raw']['media_id']))
      self.logger('info', 'Rotated asset {}...'.format(processed_asset['raw']['media_id']))
      return cropped_asset
    except:
      self.logger('error', 'Unable to Position asset {}...'.format(processed_asset['raw']['media_id']))
      self.logger('error', 'Unable to Scale asset {}...'.format(processed_asset['raw']['media_id']))
      self.logger('error', 'Unable to Rotate asset {}...'.format(processed_asset['raw']['media_id']))
      raise

#########################
# PREFLIGHT METHODS
#########################

  # check background to see if cropping or resizing is required
  def preflight_background (self, base, raw_asset):
    self.logger('info', 'PREFLIGHT - BACKGROUND')
    self.logger('info', 'Performing background preflight...')
    # validate url, type, and generate asset
    try:
      processed_asset = {}
      processed_asset['raw'] = raw_asset
      processed_asset['asset'] = self.validate_and_get_asset(processed_asset['raw'])
      self.background = self.transform_background(base, processed_asset)
      self.logger('info', 'Background {} passed preflight...'.format(processed_asset['raw']['media_id']))
    except:
      self.logger('error', 'Background {} failed preflight, verify source URL and image type.'.format(processed_asset['raw']['media_id']))
      raise

  # check items and perform necessary manipulations
  def preflight_items (self, items):
    self.logger('info', 'PREFLIGHT - ITEMS')
    self.logger('info', 'Performing items preflight...')
    # store validated assets
    assets = []
    # iterate through items list
    for item in items:
      try:
        # create a new dictionary to store values
        processed_asset = {}
        # store reference to original item
        processed_asset['raw'] = item
        # validate url, type, and generate asset
        processed_asset['asset'] = self.validate_and_get_asset(processed_asset['raw'])
        # # get scale value
        processed_asset['scale_value'] = self.get_scale_value(processed_asset['raw'])
        # # get rotation value
        processed_asset['rotation_value'] = self.get_rotation_value(processed_asset['raw'])
        # # resize asset
        processed_asset['resized_asset'] = self.resize(processed_asset)
        # # get coordinates
        processed_asset['coordinates'] = self.get_anchor_coordinates(processed_asset['raw'])
        # # new coordinates after resize
        processed_asset['n_coordinates'] = self.recalculate_coordinates(processed_asset)
        # # calculate corners
        processed_asset['corners'] = self.calculate_corners(processed_asset)
        # # calculate pivote for rotation
        processed_asset['pivot'] = self.get_rotation_pivot(processed_asset)
        assets.append(processed_asset)
      except:
        self.logger('error', '{} failed preflight...'.format(processed_asset['raw']['media_id']))

    for asset in assets:
      # run collision test
      if self.collision_detected(asset, assets):
        self.logger('error', '{} failed preflight...'.format(asset['raw']['media_id']))
      else:
        # position scale and rotate asset
        transformed = self.position_scale_rotate(asset)
        # insert 0, transformed layer to layers list
        self.layers.append(transformed)
        self.logger('info', '{} passed preflight...'.format(asset['raw']['media_id']))

  # check messages and perform necessary manipulations
  def preflight_messages (self, messages):
    self.logger('info', 'PREFLIGHT - MESSAGES')
    self.logger('info', 'Performing messages preflight...')
    # store validated assets
    assets = []
    # # iterate through messages list
    for message in messages:
      try:
        # create a new dictionary to store values
        processed_asset = {}
        # store reference to original item
        processed_asset['raw'] = message
        # validate url, type, and generate asset
        processed_asset['asset'] = self.validate_and_get_asset(processed_asset['raw'])
        # get scale value
        processed_asset['scale_value'] = self.get_scale_value(processed_asset['raw'])
        # get rotation value
        processed_asset['rotation_value'] = self.get_rotation_value(processed_asset['raw'])
        # resize asset
        processed_asset['resized_asset'] = self.resize(processed_asset)
        # if a message passes validation
        processed_asset['coordinates'] = self.get_anchor_coordinates(processed_asset['raw'])
        # new coordinates after resize
        processed_asset['n_coordinates'] = self.recalculate_coordinates(processed_asset)
        # calculate corners
        processed_asset['corners'] = self.calculate_corners(processed_asset)
        # calculate pivote for rotation
        processed_asset['pivot'] = self.get_rotation_pivot(processed_asset)
        assets.append(processed_asset)
      except:
        self.logger('error', '{} failed preflight...'.format(processed_asset['raw']['media_id']))

    for asset in assets:
      # run collision test
      if self.collision_detected(asset, assets):
        self.logger('error', '{} failed preflight...'.format(asset['raw']['media_id']))
      else:
        # position scale and rotate asset
        transformed = self.position_scale_rotate(asset)
        # insert 0, transformed layer to layers list
        self.layers.append(transformed)
        self.logger('info', '{} passed preflight...'.format(asset['raw']['media_id']))

#########################
# RENDER METHODS
#########################

  # base canvas
  def render_canvas(self, size=(1280, 720)):
    # create new image instance width default canvas size and no fill
    self.logger('info', 'Generating canvas...')
    canvas = Image.new('RGBA', size, None)
    return canvas
    # image instance returned not original

  # render skribble
  def render(self):
    canvas = self.render_canvas()
    self.logger('info', 'PREFLIGHT')
    self.preflight_background(canvas, self.background_asset)
    self.preflight_items(self.item_assets)
    self.preflight_messages(self.message_assets)
    self.logger('info', 'PREFLIGHT COMPLETE')
    self.logger('info', '{} errors...'.format(len(self.errors)))

    if len(self.errors) > 0:
      self.logger('info', 'ERRORS:')
      for error in self.errors:
        self.logger('error', error)
    else:
      self.logger('info', 'RENDERING SKRIBBLE...')
      self.logger('info', '...')
      self.logger('info', '.........')
      self.logger('info', '...............')
      self.logger('info', '.....................')
      canvas = Image.alpha_composite(canvas, self.background)

      for layer in self.layers:
        canvas = Image.alpha_composite(canvas, layer)

      string_buffer = cStringIO.StringIO()
      canvas.save(string_buffer, 'PNG')
      self.preview(canvas)
      return string_buffer


def handler(event, context):
  # only getting skribble id will need to actually make api call to retrieve url
  # youll need to save to temp storage before returning
  # upload to temp lambda s3
  # upload to api

  # hardcoded bucket name, update if we'll be changing buckets
  bucket = 'temp-lamda'
  # create a key (file name) based on skribble id
  key = '{}'.format(event['skribble_id'])
  # create skribble instance
  skribble = Skribble(event)
  # render skribble
  render = skribble.render()
  # connect to s3
  s3 = boto3.resource('s3')
  # upload in memory buffer to bucket
  if render:
    s3.Bucket('temp-lamda').put_object(Key=key, Body=render.getvalue())

data = {
   "skribble_id": "82dd5620-df30-11e5-a52e-0800274f2cef",
   "skribble_url": "http://mockbin.com/bin/7a4dfb9f-6796-4521-83c9-27dbc98d5100",
   "post_back": "https://api-local.changemyworldnow.com/skribble/82dd5620-df30-11e5-a52e-0800274f2cef/image?a=BJEOJsdvioq:sad;er"
}
test = Skribble(data)
test.render()