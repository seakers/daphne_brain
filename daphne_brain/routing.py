from django.urls import path

from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack

from daphne_API.consumers import DaphneConsumer
from anomaly_API.SARIMAX_AD import SARIMAX_AD
from anomaly_API.KNN import adaptiveKNN

# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html
application = ProtocolTypeRouter({
    # Route all WebSocket requests to our custom chat handler.
    # We actually don't need the URLRouter here, but we've put it in for
    # illustration. Also note the inclusion of the AuthMiddlewareStack to
    # add users and sessions - see http://channels.readthedocs.io/en/latest/topics/authentication.html
    'websocket': SessionMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            path('api/daphne', DaphneConsumer),
            path('api/anomaly/SARIMAX_AD', SARIMAX_AD),
            path('api/anomaly/adaptiveKNN', adaptiveKNN)
        ]),
    ),

})