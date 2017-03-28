from channels import Group

def ws_message(message):
    # ASGI WebSocket packet-received and send-packet message types
    # both have a "text" key for their textual data.
    message.reply_channel.send({
        "text": message.content['text'],
    })
    
    
# @receiver(post_save, sender=BlogUpdate)
# def send_update(sender, instance, **kwargs):
#     Group("liveblog").send({
#         "text": json.dumps({
#             "id": instance.id,
#             "content": instance.content
#         })
#     })



# Connected to websocket.connect
def ws_connect(message):
    # Add to the group
    Group("ifeed").add(message.reply_channel)
    # Accept the connection request
    message.reply_channel.send({"accept": True})

# Connected to websocket.disconnect
def ws_disconnect(message):
    # Remove from the group on clean disconnect
    Group("ifeed").discard(message.reply_channel)