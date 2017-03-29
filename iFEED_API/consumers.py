from channels import Group
from channels.sessions import channel_session
import json


    
@channel_session
def ifeed_ws_message(message):
    
    Group("ifeed").send({
        "text": "This is a message generated from ifeed ws"
    })
    # payload = json.loads(message.content['text'])
    # print(payload['id'])
    # if payload['id']=='save_info':
    #     message.channel_session['info'] = payload['info']
    #     
    # elif payload['id']=='extract_info':
    #     print(message.channel_session['info'])
    #     Group('ifeed').send({
    #         "text":message.channel_session['info']
    #     })
    # else:
    #     Group("ifeed").send({
    #             "text":"ifeed web socket"
    #     })
    

# @receiver(post_save, sender=BlogUpdate)
# def send_update(sender, instance, **kwargs):
#     Group("liveblog").send({
#         "text": json.dumps({
#             "id": instance.id,
#             "content": instance.content
#         })
#     })


# Connected to websocket.connect
@channel_session
def ifeed_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    # Store the channel session info
    message.channel_session['temp'] = 'save channel session info'
    # Add to the group
    Group("ifeed").add(message.reply_channel)

    
# Connected to websocket.disconnect
@channel_session
def ifeed_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("ifeed").discard(message.reply_channel)
    
    
    
def server_ws_message(message):
    server_message = message.content['text']
    if server_message == 'apply_pareto_filter':
        Group("ifeed").send({
                "text":'apply_pareto_filter'
        })
    

def server_ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    # Add to the group
    Group("server").add(message.reply_channel)

# Connected to websocket.disconnect
def server_ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("server").discard(message.reply_channel)
    