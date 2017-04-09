from channels.routing import route, include

from iFEED_API.consumers import ifeed_ws_message, ifeed_ws_connect, ifeed_ws_disconnect
from iFEED_API.consumers import ifeed_feature_metric_message, ifeed_feature_metric_connect, ifeed_feature_metric_disconnect
from iFEED_API.consumers import ifeed_feature_status_message, ifeed_feature_status_connect, ifeed_feature_status_disconnect

from chatbox_API.consumers import chat_ws_connect, chat_ws_disconnect, chat_ws_message
from mycroft_API.consumers import mycroft_ws_connect, mycroft_ws_disconnect, mycroft_ws_message





channel_routing = [
    
    route("websocket.receive", ifeed_feature_metric_message, path=r"/ifeed/feature/metric/"),
    route("websocket.connect", ifeed_feature_metric_connect, path=r"/ifeed/feature/metric/"),
    route("websocket.disconnect", ifeed_feature_metric_disconnect, path=r"/ifeed/feature/metric/"),
    
    route("websocket.receive", ifeed_feature_status_message, path=r"/ifeed/feature/status/"),
    route("websocket.connect", ifeed_feature_status_connect, path=r"/ifeed/feature/status/"),
    route("websocket.disconnect", ifeed_feature_status_disconnect, path=r"/ifeed/feature/status/"),
    
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



