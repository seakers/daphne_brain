from channels.routing import route

from iFEED_API.consumers import ifeed_ws_message, ifeed_ws_connect, ifeed_ws_disconnect
from iFEED_API.consumers import ifeedFeature_ws_message, ifeedFeature_ws_connect, ifeedFeature_ws_disconnect
from chatbox_API.consumers import chat_ws_connect, chat_ws_disconnect, chat_ws_message
from mycroft_API.consumers import mycroft_ws_connect, mycroft_ws_disconnect, mycroft_ws_message


channel_routing = [
    
    route("websocket.receive", ifeedFeature_ws_message, path=r"/ifeed/feature-status/"),
    route("websocket.connect", ifeedFeature_ws_connect, path=r"/ifeed/feature-status/"),
    route("websocket.disconnect", ifeedFeature_ws_disconnect, path=r"/ifeed/feature-status/"),
    
    route("websocket.receive", ifeed_ws_message, path=r"/ifeed/"),
    route("websocket.connect", ifeed_ws_connect, path=r"/ifeed/"),
    route("websocket.disconnect", ifeed_ws_disconnect, path=r"/ifeed/"),
    
    route("websocket.receive", chat_ws_message, path=r"/chat/"),
    route("websocket.connect", chat_ws_connect, path=r"/chat/"),
    route("websocket.disconnect", chat_ws_disconnect, path=r"/chat/"),
    
    route("websocket.receive", mycroft_ws_message, path=r"/mycroft/"),
    route("websocket.connect", mycroft_ws_connect, path=r"/mycroft/"),
    route("websocket.disconnect", mycroft_ws_disconnect, path=r"/mycroft/")    
    

    
    # HTTP requests are automatically routed to django views
]



