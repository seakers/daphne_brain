from channels.routing import route, include

channel_routing = [
    
    include('daphne_API.routing.channel_routing', path=r"^/api/daphne"),
    
    # HTTP requests are automatically routed to django views
]



