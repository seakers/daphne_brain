from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from daphne_brain import settings

if "EOSS" in settings.ACTIVE_MODULES:
    from EOSS.consumers import EOSSConsumer
if "AT" in settings.ACTIVE_MODULES:
    from AT.SARIMAX_AD import SARIMAX_AD
    from AT.KNN import adaptiveKNN
    from AT.I_Forest import iForest

from experiment_API.consumers import ExperimentConsumer

# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html

ws_routes = []
if "EOSS" in settings.ACTIVE_MODULES:
    ws_routes.append(path('api/eoss/ws', EOSSConsumer))
if "AT" in settings.ACTIVE_MODULES:
    ws_routes.extend([
        path('api/anomaly/SARIMAX_AD', SARIMAX_AD),
        path('api/anomaly/adaptiveKNN', adaptiveKNN),
        path('api/anomaly/iForest', iForest),
    ])
ws_routes.extend([
    path('api/experiment', ExperimentConsumer),
])

application = ProtocolTypeRouter({
    # Route all WebSocket requests to our custom chat handler.
    # We actually don't need the URLRouter here, but we've put it in for
    # illustration. Also note the inclusion of the AuthMiddlewareStack to
    # add users and sessions - see http://channels.readthedocs.io/en/latest/topics/authentication.html
    'websocket': AuthMiddlewareStack(
        URLRouter(ws_routes),
    ),
})
