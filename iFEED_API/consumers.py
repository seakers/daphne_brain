from channels import Group
from channels.sessions import channel_session
import json


    
@channel_session
def ifeed_ws_message(message):
    text = message.content['text']
    Group("ifeed").send({"text": text})
    
# Connected to websocket.connect
@channel_session
def ifeed_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    # Add to the group
    Group("ifeed").add(message.reply_channel)
# Connected to websocket.disconnect
@channel_session
def ifeed_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("ifeed").discard(message.reply_channel)
    
    
    
    
    
    
def ifeedFeature_ws_message(message):
    text = message.content['text']
    Group("ifeed-feature").send({"text": text})
# Connected to websocket.connect
def ifeedFeature_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    # Add to the group
    Group("ifeed-feature").add(message.reply_channel)
# Connected to websocket.disconnect
def ifeedFeature_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("ifeed-feature").discard(message.reply_channel)
    
    
    
    
    
    
    
    
    
    
def server_ws_message(message):
    server_message = message.content['text']
    print(server_message)
    """
    Group("ifeed").send({
            "text": server_message
    })"""

def server_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    # Add to the group
    Group("server").add(message.reply_channel)

# Connected to websocket.disconnect
def server_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("server").discard(message.reply_channel)
    