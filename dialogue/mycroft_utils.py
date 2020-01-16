from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def forward_to_mycroft(context, phrase):
    if not context.mycroft_connection:
        return
    channel_layer = get_channel_layer()
    print(context.mycroft_connection)
    message = {'type': 'mycroft.forward', 'content': phrase}
    async_to_sync(channel_layer.send)(context.mycroft_channel_name, message)