from channels import Group
from channels.sessions import channel_session
import json


    
def chat_ws_message(message):
    text = message.content['text']
    Group("chat").send({
            "text": text
    })

def chat_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    # Add to the group
    Group("chat").add(message.reply_channel)

# Connected to websocket.disconnect
def chat_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("chat").discard(message.reply_channel)
    