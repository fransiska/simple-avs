import requests
import time
import json
import io
import yaml
from commands import getoutput
from eventhook import EventHook

""" Authorize device using Code-Based Linking method
"""

class Authorization(object):
  def __init__(self):
    self.authorized_event = EventHook()            # Called when refresh token is obtained
    self.device_authorization_event = EventHook()  # Called when device needs to be authorized
    
  def authorize(self, config):
    """ Get a new refresh token
    display    
    """

    # Get user_code
    headers = {"Accept-Language": "ja-JP",'Content-type': 'application/x-www-form-urlencoded'}
    start = time.time()
    device_sn = "cube-{}".format(getoutput('cat /sys/class/net/*/address | grep -v 00:00:00:00:00:00 | head -1 | sed -e "s/:/-/g"'))
    config['access_token'] = None
    config['refresh_token'] = None
    data = [('response_type','device_code'),
            ('client_id',config['client_id']),
            ('scope', 'alexa:all'),
            ('scope_data', '{"alexa:all":{"productID":"'+config['product_id']+'","productInstanceAttributes":{"deviceSerialNumber": "'+device_sn+'"}}}')]
    r = requests.post("https://api.amazon.com/auth/O2/create/codepair", headers=headers, data=data, verify=False)
    device_code = r.json()['device_code']
    user_code = r.json()['user_code']
    verification_uri = r.json()['verification_uri']
    self.device_authorization_event(user_code,verification_uri)

    # Poll for authorization result
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    while time.time()-start < 600:
      time.sleep(2)      
      r = requests.post('https://api.amazon.com/auth/O2/token', headers=headers,
                        data={'grant_type':'device_code',
                              'device_code':device_code,
                              'user_code':user_code
                        })
      if 'access_token' in r.json():
        config['access_token'] = r.json()['access_token']
        config['refresh_token'] = r.json()['refresh_token']        
        break
    if config['access_token']:
      self.authorized_event(config)
      return config
    else:
      return None

