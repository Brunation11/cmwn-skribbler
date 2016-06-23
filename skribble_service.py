# Ths skribble process will take in the skribble json specification and create a flattened image. The the process MUST accept in the id of the skribble to process. The skribble process MUST complete the following validataion on the specification:

      # All assets requested to be included MUST exist in the media server
      # All assets requested MUST match the check field from the media service in the matching specification
      # All assets that cannot overlap MUST NOT have points that intersect on the grid based on type of asset
      # For Effect, Sound and Background, there MUST NOT be more than one instance of that type
      # Status MUST BE "PROCESSING"

# The generated image MUST BE a png file that is web optimized. Once the image is generated, the image is then POSTed back to the api with the skribble id.

# Order of image manipulation
      # postion
      # scale
      # rotate

from __future__ import print_function
from PIL import Image, ImageChops
import logging, urllib2, cStringIO, json, boto3, os, sys, uuid, hashlib, base64
# PIL           Python Image Library
# urllib2       open arbitrary resources from url
# cstringIO     create string buffer (used to open virtual image from url)
# json          pretty print json
# boto3         aws client
# os            Miscellaneous operating system interfaces
# sys           System-specific parameters and functions
# uuid          UUID objects according to RFC 4122
# logging       info, error, debug messages
# base64        encoding for posting images

# initiate logger
logger = logging.getLogger()
# set base level for logger
logger.setLevel(logging.INFO)

class Skribble:
  # init instance by extracting background, items, and messages
  def __init__(self, event):
    url = event['skribble_url']
    self.skribble_json = json.load(urllib2.urlopen(url))
    self.background_asset = self.skribble_json['rules']['background']
    self.item_assets = self.skribble_json['rules']['items']
    self.message_assets = self.skribble_json['rules']['messages']
    self.background = None
    self.layers = []
    self.logs = []
    self.errors = []

#########################
# HELPER METHODS
#########################

  # validate url
  def valid_url (self, url):
    try:
      self.logs.append('Validated URL {}...'.format(url))
      return urllib2.urlopen(urllib2.Request(url))
    except:
      self.errors.append('Invalid URL {}...'.format(url))
      return False

  # validate response is imgage/png
  def valid_type (self, asset, response):
    mime_type = asset['mime_type']
    try:
      self.logs.append('Validated type as {}...'.format(mime_type))
      return response.info()['Content-type'] == mime_type
    except:
      self.errors.append('Invalid type, expected {}, instead saw {}...'.format(mime_type, response.info()['Content-type']))

  # verify assets by checksum type and value
  def validate_checksum(self, asset, response):
    # verify check type
    self.logs.append('Validating checksum of {}...'.format(asset['media_id'], asset['src']))
    type_of_check = asset['check']['type']
    value = asset['check']['value']
    if type_of_check == 'sha1':
      hash_value = hashlib.sha1(response).hexdigest()
    elif type_of_check == 'md5':
      hash_value = hashlib.md5(response).hexdigest()
    if hash_value == value:
      self.logs.append('{} passed checksum validation...'.format(asset['media_id']))
    else:
      self.errors.append('{} failed checksum validation, expected checksum {}, instead saw {}...'.format(asset['media_id'], value, hash_value))
    return hash_value == value

  # retrieve content from url
  def url_response (self, url):
    self.logs.append('Fetching response for {}...'.format(url))
    return urllib2.urlopen(url)

  # create string buffer for reading and writing data
  def string_buffer (self, response):
    self.logs.append('Creating buffer for response...')
    return cStringIO.StringIO(response.read())

  # load image from a file in this case from the string buffer
  def image (self, file):
    return Image.open(file).convert('RGBA')

  # open image (currently used for debugging)
  def preview (self, asset):
    asset.show()

  # get an assets top left coordinate
  def get_anchor_coordinates (self, asset):
    self.logs.append('Getting asset anchor points...')
    x = asset['state']['left']
    y = asset['state']['top']
    return x,y

  # get an assets scale if any
  def get_scale_value (self, asset):
    self.logs.append('Getting asset scale value...')
    return asset['state']['scale']

  # get an assets rotation if any
  def get_rotation_value (self, asset):
    self.logs.append('Getting asset rotation value...')
    return asset['state']['rotation']

  # calculate all corners after asset is scaled
  def calculate_corners (self, resized_asset, n_coordinates):
    self.logs.append('Calculating corners...')
    corners = {}
    # dimensions
    w, h = resized_asset.size
    corners['top_left'] = n_coordinates
    corners['top_right'] = ((n_coordinates[0] + w), n_coordinates[1])
    corners['bottom_right'] = ((n_coordinates[0] + w), (n_coordinates[1] + h))
    corners['bottom_left'] = (n_coordinates[0], (n_coordinates[1] + h))
    return corners

  # # verify that non-overlapable assets don't collide
  def collision_test (self, base, base_corners, items):
    self.logs.append('Starting collision test...')
    for item in items:
      asset = self.validate_and_get_asset(item)
      scale_value = self.get_scale_value(item)
      resized_asset = self.resize(asset, scale_value)
      coordinates = self.get_anchor_coordinates(item)
      n_coordinates = self.recalculate_coordinates(asset, resized_asset, coordinates)
      corners = self.calculate_corners(resized_asset, n_coordinates)
      if item != base:
        if (not base['can_overlap']) | (not item['can_overlap']):
          if (corners['top_left'][0] > base_corners['top_left'][0]) | (base_corners['top_left'][0] > corners['top_left'][0]):
            if (corners['top_left'][0] < base_corners['top_right'][0]) | (base_corners['top_left'][0] < corners['top_right'][0]):
              if (corners['top_left'][1] > base_corners['top_left'][1]) | (base_corners['top_left'][1] > corners['top_left'][1]):
                if (corners['top_left'][1] < base_corners['bottom_left'][1]) | (base_corners['top_left'][1] < corners['bottom_left'][1]):
                  self.errors.append('Error, collision detected: {}...'.format(base['src']))
      self.logs.append('No collisions detected: asset {}...'.format(base['src']))

  # validate an assets url and type
  def validate_and_get_asset (self, asset):
    url = asset['src']
    self.logs.append('Validating {}...'.format(url))
    if self.valid_url(url):
      response = self.url_response(url)
      if self.valid_type(asset, response):
        file = self.string_buffer(response)
        if self.validate_checksum(asset, response):
          self.logs.append('Validated {}...'.format(url))
          return self.image(file)
        else:
          self.errors.append('Error, invalid checksum for {}...'.format(url))
      else:
        self.errors.append('Error, invalid type for {}...'.format(url))
    else:
      self.errors.append('Error, invalid url for {}...'.format(url))

  # recalculate new coordinates after asset is scaled
  def recalculate_coordinates (self, asset, resized_asset, coordinates):
    self.logs.append('Recalculating coordinates...')
    # original dimensions
    o_width, o_height = asset.size
    # resized dimensions
    r_width, r_height = resized_asset.size
    # if asset has shrunk
    if (o_width > r_width) & (o_height > r_height):
    # dimension differences to calculate new coordinates
      width_difference = o_width - r_width
      height_difference = o_height - r_height
      # set new coordinates for x & y
      nx = (coordinates[0] + (width_difference / 2))
      ny = (coordinates[1] + (height_difference / 2))
    # if asset has expanded
    elif (o_width < r_width) & (o_height < r_height):
      # dimension differences to calculate new coordinates
      width_difference = r_width - o_width
      height_difference = r_height - o_height
      # set new coordinates for x & y
      nx = (coordinates[0] - (width_difference / 2))
      ny = (coordinates[1] - (width_difference / 2))
    return (nx,ny)

  def get_rotation_pivot (self, asset, scale, coordinates):
    self.logs.append('Calculating rotation pivot...')
    # resize asset to determin new size
    resized_asset = self. resize(asset, scale)
    # calculate coordinates for resized asset
    n_coordinates = self.recalculate_coordinates(asset, resized_asset, coordinates)
    # calculate x coordinate of center
    center_x = n_coordinates[0] + (resized_asset.size[0] / 2)
    # calculate y coordinate of center
    center_y = n_coordinates[1] + (resized_asset.size[1] / 2)
    return center_x, center_y

  def upload_skribble (self, rendered_skribble, post_path):
    encoded_image = base64.b64encode(rendered_skribble.read())
    # Build the request
    request = urllib2.Request(post_path)
    request.add_header('Content-type', 'application/json')
    body = {
      'skribble_id': self.skribble_json['skribble_id'],
      'skribble': encoded_image
    }
    request.add_data(body)
    # outgoing data
    self.logs.append('Outgoing api data {}...'.format(request.get_data()))
    # server response
    self.logs.append('Submitting Skribble to API...')
    self.logs.append(urllib2.urlopen(request).read())

#########################
# TRANSFORM METHODS
#########################

  # layer assets onto a base at given coordinates
  def paste (self, base, layer, coordinates=None):
    # add layer to base
    base.paste(layer, (int(coordinates[0]),int(coordinates[1])), layer)
    return base

  # resize an asset
  def resize (self, asset, scale):
    self.logs.append('Resizing asset...')
    # original width & height of asset
    o_width = round((asset.size[0]), 14)
    o_height = round((asset.size[1]), 14)
    # resized width & height
    r_width = int(o_width * scale)
    r_height = int(o_height * scale)
    # resized asset
    return asset.resize((r_width, r_height), Image.ANTIALIAS)

 # center asset for rotation
  def center (self, base, asset):
    # # dimensions for base
    base_width, base_height = base.size
    # # center of base
    center_x = base_width / 2
    center_y = base_height / 2
    # dimensions for asset
    asset_width, asset_height = asset.size
    x = center_x - (asset_width / 2)
    y = center_y - (asset_height / 2)
    return self.paste(base, asset, (x,y))

  # crop asset from its center
  def crop_from_center (self, asset, proposed_size):
    # img size
    width, height = asset.size
    # proposed dimensions
    proposed_width = proposed_size[0]
    proposed_height = proposed_size[1]
    # coordinates for 4-tuple
    left = (width - proposed_width) / 2
    top = (height - proposed_height) / 2
    right = proposed_width + left
    bottom = proposed_height + top
    # crop asset from center
    return asset.crop((left, top, right, bottom))

  # resize asset to fit within proposed size
  def resize_from_center(self, asset, proposed_size):
    # asset dimensions
    width, height = asset.size
    # proposed dimensions
    proposed_width = proposed_size[0]
    proposed_height = proposed_size[1]
    # calculate whether to scale to proposed width or proposed height
    width_difference = proposed_width - width
    height_difference = proposed_height - height
    # if width requires scaling priority scale by proposed width
    if width_difference > height_difference:
      r_width = proposed_width
      r_height = int((height * proposed_width) / width)
      return asset.resize((r_width, r_height), Image.ANTIALIAS)
      # else scale by proposed height
    else:
      r_height = proposed_height
      r_width = int((width * proposed_height) / height)
      return asset.resize((r_width, r_height), Image.ANTIALIAS)

  # format background
  def transform_background(self, base, asset):
    self.logs.append('Formatting background asset...')
    # if sizes are equal do nothing
    if base.size == asset.size:
      return asset
    # else check if layer needs to be resized
    else:
      base_width, base_height = base.size
      asset_width, asset_height = asset.size
      # if either the width or height of the layer are smaller then the width or height of the base resize the layer to cover the base area
      if asset_width < base_width | asset_height < base_height:
        # resize the layer
        return self.resize_from_center(asset, base.size)
      # crop the oversized layer from center to fit exactly within the base area
      return self.crop_from_center(asset, base.size)

  def position_scale_rotate(self, asset, resized_asset, scale, coordinates, angle):
    self.logs.append('Positioning asset...')
    self.logs.append('Scaling asset...')
    self.logs.append('Rotating asset...')
    base = self.render_canvas()
    # calculate new coordinates for resized asset
    n_coordinates = self.recalculate_coordinates(asset, resized_asset, coordinates)
    # # get pivot point
    pivot = self.get_rotation_pivot(asset, scale, coordinates)
    # # dimensions for base
    base_width, base_height = base.size
    # # dimensions for asset
    asset_width, asset_height = resized_asset.size
    # # point of pivot (asset centerpoint)
    pivot_x, pivot_y = pivot
    # # center of base
    center_x = base_width / 2
    center_y = base_height / 2
    # dimensions for asset
    asset_width, asset_height = resized_asset.size
    x = center_x - (asset_width / 2)
    y = center_y - (asset_height / 2)
    # determine offset to reposition centered image after rotation
    x_shift = n_coordinates[0] - x
    y_shift = n_coordinates[1] - y
    # center image
    centered = self.center(base, resized_asset)
    # rotate image
    rotated = centered.rotate(-angle)
    # reposition image using offset
    return ImageChops.offset(rotated, int(x_shift), int(y_shift))

#########################
# PREFLIGHT METHODS
#########################

  # check background to see if cropping or resizing is required
  def preflight_background (self, base, item):
    self.logs.append('Performing background preflight...')
    # validate url, type, and generate asset
    try:
      asset = self.validate_and_get_asset(item)
      transformed = self.transform_background(base, asset)
      self.background = transformed
      self.logs.append('Background passed preflight...')
    except:
      self.errors.append('Background failed preflight, verify source URL and image type.')

  # check items and perform necessary manipulations
  def preflight_items (self, items):
    self.logs.append('Performing items preflight...')
    # iterate through items list
    for item in items:
      try:
        # validate url, type, and generate asset
        asset = self.validate_and_get_asset(item)
        # get scale value
        scale_value = self.get_scale_value(item)
        # get rotation value
        rotation_value = self.get_rotation_value(item)
        # resize asset
        resized_asset = self.resize(asset, scale_value)
        # get coordinates
        coordinates = self.get_anchor_coordinates(item)
        # new coordinates after resize
        n_coordinates = self.recalculate_coordinates(asset, resized_asset, coordinates)
        # calculate corners
        corners = self.calculate_corners(resized_asset, n_coordinates)
        # run collision test
        self.collision_test(item, corners, items)
        # position scale and rotate asset
        transformed = self.position_scale_rotate(asset, resized_asset, scale_value, coordinates, rotation_value)
        # append transformed layer to layers list
        self.layers.append(transformed)
        self.logs.append('{} passed preflight...'.format(item['media_id']))
      except:
        self.errors.append('{} failed preflight...'.format(item['media_id']))

  # check messages and perform necessary manipulations
  def preflight_messages (self, messages):
    self.logs.append('Performing messages preflight...')
    # # iterate through messages list
    for message in messages:
      try:
        # validate url, type, and generate asset
        asset = self.validate_and_get_asset(message)
        # get scale value
        scale_value = self.get_scale_value(message)
        # get rotation value
        rotation_value = self.get_rotation_value(message)
        # resize asset
        resized_asset = self.resize(asset, scale_value)
        # if a message passes validation
        coordinates = self.get_anchor_coordinates(message)
        # new coordinates after resize
        n_coordinates = self.recalculate_coordinates(asset, resized_asset, coordinates)
        # calculate corners
        corners = self.calculate_corners(resized_asset, n_coordinates)
        # run collision test
        self.collision_test(message, corners, messages)
        # position scale and rotate asset
        transformed = self.position_scale_rotate(asset, resized_asset, scale_value, coordinates, rotation_value)
        # append transformed layer to layers list
        self.layers.append(transformed)
        self.logs.append('{} passed preflight...'.format(message['media_id']))
      except:
        self.errors.append('{} failed preflight...'.format(message['media_id']))

#########################
# RENDER METHODS
#########################

  # base canvas
  def render_canvas(self):
    # create new image instance width default canvas size and no fill
    canvas = Image.new('RGBA', (1280, 720), None)
    return canvas
    # image instance returned not original

  # render skribble
  def render(self):
    canvas = self.render_canvas()
    self.preflight_background(canvas, self.background_asset)
    self.preflight_items(self.item_assets)
    self.preflight_messages(self.message_assets)

    logs = set(self.logs)
    for log in logs:
      logger.info(log)
      # print(log)

    if len(self.errors) > 0:
      errors = set(self.errors)
      for error in errors:
        logger.error(error)
        # print(error)
    else:
      canvas = Image.alpha_composite(canvas, self.background)
      for layer in self.layers:
        canvas = Image.alpha_composite(canvas, layer)
      string_buffer = cStringIO.StringIO()
      canvas.save(string_buffer, 'PNG')
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
