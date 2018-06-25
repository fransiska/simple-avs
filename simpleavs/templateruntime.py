""" owns all TemplateRuntime AVS namespace interaction

    https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/templateruntime
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import logging
import json
from .objectdict import ObjectDict
from .eventhook import EventHook

_LOG = logging.getLogger(__name__)

class TemplateRuntime(object):
    """ owns all TemplateRuntime AVS namespace interaction """
    def __init__(self, connection):
        self._connection = connection
        self._connection.message_received += self._handle_message
        self.render_template_event = EventHook()
        
    def _handle_render_template(self, message):
        directive = message['directive']
        header = directive['header']
        payload = directive['payload']
        template = payload['type']
        maintitle = payload['title']['mainTitle']        
        subtitle = payload['title']['subTitle']
        self.render_template_event((maintitle,subtitle))
        
    def _handle_message(self, message):
        if 'directive' not in message:
            return

        header = message['directive']['header']

        if header['namespace'] != 'TemplateRuntime':
            return

        name = header['name']        
        _LOG.info('TemplateRuntime received directive: ' + name)

        if name == 'RenderTemplate':
            self._handle_render_template(message)
        else:
            _LOG.warning('TemplateRuntime received ' +
                         'an unrecognised directive: ' +
                         json.dumps(message))
