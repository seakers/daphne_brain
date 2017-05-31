import logging

# Get an instance of a logger
logger = logging.getLogger('mycroft')

from channels import Group
from channels.sessions import channel_session
import json

    
def mycroft_ws_message(message):
    text = message.content['text']
    print(text)

def mycroft_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    
    logger.info('Mycroft ws connection made')
    
    # Add to the group
    Group("mycroft").add(message.reply_channel)

# Connected to websocket.disconnect
def mycroft_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("mycroft").discard(message.reply_channel)
    
