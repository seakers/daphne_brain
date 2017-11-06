from channels.routing import route, include

from daphne_brain.consumers import ws_message, ws_connect, ws_disconnect


channel_routing = [
    route("websocket.receive", ws_message, path=r"^/api/"),
    route("websocket.connect", ws_connect, path=r"^/api/"),
    route("websocket.disconnect", ws_disconnect, path=r"^/api/"),
    
    # HTTP requests are automatically routed to django views
]



