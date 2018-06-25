""" basic example demonstrating client usage """

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import os
import sys
import io
import time
import yaml
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import simpleavs  # pylint: disable=wrong-import-position

_EXAMPLES_DIR = os.path.dirname(__file__)
_CONFIG_PATH = os.path.join(_EXAMPLES_DIR, 'client_config.yml')
_REQUEST_PATH = os.path.join(_EXAMPLES_DIR, 'request.wav')

# import logging
# ch = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s %(levelname)8s %(name)s | %(message)s')
# ch.setFormatter(formatter)
# logger = logging.getLogger('simpleavs')
# logger.addHandler(ch)
# logger.setLevel(logging.INFO)

def main():
    """ basic example demonstrating client usage """
    avs = None

    def handle_render_template(title):
        print(title)

    def handle_speak(speak_directive):
        """ called when a speak directive is received from AVS """
        print('Received a Speak directive from Alexa')
        print('Notifying AVS that we have started speaking')
        avs.speech_synthesizer.speech_started(speak_directive.token)

        # save the mp3 audio that AVS sent us as part of the Speak directive
        print('(play speak.mp3 to hear how Alexa responded)')
        with io.open('speak.mp3', 'wb') as speak_file:
            speak_file.write(speak_directive.audio_data)

        print('Notifying AVS that we have finished speaking')
        avs.speech_synthesizer.speech_finished(speak_directive.token)

    def handle_authorized(config):
        enable_templateruntime(config)

    def handle_device_authorization(user_code,verification_uri):
        print((user_code,verification_uri))

    def enable_templateruntime(config):
        """ Set capabilities to handle templateruntime
        
        Enable sending of RenderTemplate directive for devices with display
        """
        
        data = '{"envelopeVersion": "20160207","capabilities": [{"type": "AlexaInterface","interface": "TemplateRuntime","version": "1.0"}]}'
        headers = {"Content-Type": "application/json",  
                   "Content-Length": str(len(data.encode('utf-8'))),
                   "Authorization": "Bearer " +  str(config['access_token'])}
        r = requests.put('https://api.amazonalexa.com/v1/devices/@self/capabilities', headers=headers, data=data)

    with io.open(_CONFIG_PATH, 'r') as cfile:
        config = yaml.load(cfile)

    # Get a refresh token if needed
    if 'refresh_token' not in config:
        authorization = simpleavs.Authorization()
        authorization.authorized_event += handle_authorized
        authorization.device_authorization_event += handle_device_authorization
        config = authorization.authorize(config)
        if config == None:
            return
        with open(_CONFIG_PATH,'w') as outfile:
            yaml.dump(config, outfile)
        
    # AvsClient requires a dict with client_id, client_secret, refresh_token
    avs = simpleavs.AvsClient(config)

    # handle the Speak directive event when sent from AVS
    avs.speech_synthesizer.speak_event += handle_speak
    avs.template_runtime.render_template_event += handle_render_template    

    print('Connecting to AVS')
    avs.connect()

    # Set language
    header = {"namespace": "Settings",
              "name": "SettingsUpdated",
              "messageId": "12345"}
    payload = {'settings':  [{
        "key": "locale",
        "value": "ja-JP"
    }]}
    avs._connection.send_event(header, include_state=False, payload=payload)
   
    # send AVS a wav request (LE, 16bit, 16000 sample rate, mono)
    with io.open(_REQUEST_PATH, 'rb') as request_file:
        request_data = request_file.read()

    print('Sending Alexa a voice request')
    avs.speech_recognizer.recognize(audio_data=request_data,
                                    profile='NEAR_FIELD')

    # once AVS has processed the request we should receive a Speak event

    time.sleep(5)
    print('Disconnecting from AVS')
    avs.disconnect()


if __name__ == '__main__':
    main()
