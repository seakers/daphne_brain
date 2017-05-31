from channels.routing import route, include

from daphne_brain.consumers import ws_message, ws_connect, ws_disconnect
from mycroft_API.consumers import mycroft_ws_connect, mycroft_ws_disconnect, mycroft_ws_message


channel_routing = [
    
    route("websocket.receive", mycroft_ws_message, path=r"/api/mycroft/"),
    route("websocket.connect", mycroft_ws_connect, path=r"/api/mycroft/"),
    route("websocket.disconnect", mycroft_ws_disconnect, path=r"/api/mycroft/"),  
    
    route("websocket.receive", ws_message, path=r"^/api/"),
    route("websocket.connect", ws_connect, path=r"^/api/"),
    route("websocket.disconnect", ws_disconnect, path=r"^/api/"),
    
    # HTTP requests are automatically routed to django views
]



