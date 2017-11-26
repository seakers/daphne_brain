from channels.routing import route, include

from daphne_API.consumers import ws_message, ws_connect, ws_disconnect


channel_routing = [
        
    route("websocket.receive", ws_message, path=r"^daphne$"),
    route("websocket.connect", ws_connect, path=r"^daphne$"),
    route("websocket.disconnect", ws_disconnect, path=r"^daphne$"),
    
    # HTTP requests are automatically routed to django views
]
