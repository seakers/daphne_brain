from channels import Group
from channels.sessions import channel_session
import json
import hashlib

    
@channel_session
def ifeed_ws_message(message):
    
    key = message.content['path'].lstrip('ifeed/')
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    text = message.content['text']
    Group(hash_key).send({"text": text})
    
    
@channel_session
def ifeed_ws_connect(message):
    
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    
    key = message.content['path'].lstrip('ifeed/')
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    # Add to the group
    Group(hash_key).add(message.reply_channel)

    
@channel_session
def ifeed_ws_disconnect(message):
    
    key = message.content['path'].lstrip('ifeed/')
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    # Remove from the group on clean disconnect
    Group(hash_key).discard(message.reply_channel)
    
    

    
    
    
    
    
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
    