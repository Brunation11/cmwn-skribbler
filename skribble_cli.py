#!/usr/bin/env python

from skribble_service import handle_cli, real, logging
import sys
import argparse  # parse args from the command line

formatter = logging.Formatter('%(levelname)s\t - %(message)s')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

parser = argparse.ArgumentParser(description='Process a skribble', prog='skribble')

parser.add_argument('skribble_id', help='Id of the skribble to process')
parser.add_argument('user_id', help='User id for the user who created the skribble')

parser.add_argument('--api', help='Api domain to call', default='https://api.changemyworldnow.com/')
parser.add_argument('--media', help='Api domain to call', default='https://media.changemyworldnow.com/')
parser.add_argument('--verbose', help='Turn on verbose logging', action='store_true')
parser.add_argument('--debug', help='Turn on debug logging', action='store_true')
parser.add_argument('--preview', help='Preview the skribble locally', action='store_true')

args = parser.parse_args()

if args.verbose:
    real.setLevel(logging.INFO)

if args.debug:
    real.setLevel(logging.DEBUG)

real.addHandler(console_handler)

data = {
    "skribble_id": args.skribble_id,
    "skribble_url": '{}/user/{}/skribble/{}'.format(args.api, args.user_id, args.skribble_id),
    "post_back": '{}/user/{}/skribble/{}/notice'.format(args.api, args.user_id, args.skribble_id),
    "media_url": '{}/a'.format(args.media),
    "preview": args.preview
}

handle_cli(data)
