import logging
import ConfigParser

config = ConfigParser.RawConfigParser()

config.add_section('aws')
config.add_section('rollbar')
config.add_section('cmwn')
config.add_section('media')

config.set('aws', 'aws_s3_bucket', 'cmwn-skribble')

config.set('rollbar', 'access_token', '88f9491d19be4d5aa91e1f3bb073d75f')
config.set('rollbar', 'env', 'local')
config.set('rollbar', 'version', '0.2.0')
config.set('rollbar', 'level', logging.ERROR)

config.set('cmwn', 'api_user', 'lambda')
config.set('cmwn', 'api_pass', 'tFe4ueVduWPRDwjof3t')
config.set('cmwn', 'verify_ssl', False)
config.set('cmwn', 'max_redirects', 5)
config.set('cmwn', 'api_base', 'https://api.changemyworldnow.com/')

config.set('media', 'media_base_url', 'https://media.changemyworldnow.com/')
config.set('media', 'max_redirects', 5)
config.set('media', 'verify_ssl', False)
config.set('media', 'verify_file_hash', False)

with open('skramble.cfg', 'wb') as configfile:
    config.write(configfile)
