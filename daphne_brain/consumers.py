from channels import Group
from channels.sessions import channel_session
from messagebus.message import Message
import json
import hashlib

    
@channel_session
def ws_message(message):
    
    key = message.content['path'].lstrip('api/')
    
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    textMessage = message.content['text']
    
    # Deserialize message
    daphneMessage = Message.deserialize(textMessage)

    # Broadcast
    Group(hash_key).send({"text": textMessage})
    
    
@channel_session
def ws_connect(message):
    
    # Accept the connection request
    message.reply_channel.send({"accept": True})

    key = message.content['path'].lstrip('api/')  
        
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    # Add to the group
    Group(hash_key).add(message.reply_channel)

    
@channel_session
def ws_disconnect(message):
    
    key = message.content['path'].lstrip('api/')
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    # Remove from the group on clean disconnect
    Group(hash_key).discard(message.reply_channel)
    