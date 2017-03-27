from channels.routing import route
from iFEED_API.consumers import ws_message

channel_routing = [
    route("websocket.receive", ws_message),
]