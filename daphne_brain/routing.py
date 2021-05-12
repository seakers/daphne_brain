from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from daphne_brain import settings
from experiment_at.consumers import ATExperimentConsumer
if "EOSS" in settings.ACTIVE_MODULES:
    from EOSS.consumers import EOSSConsumer
if "AT" in settings.ACTIVE_MODULES:
    # from AT.AD.algorithms.SARIMAX_AD import SARIMAX_AD
    # from AT.AD.algorithms.KNN import adaptiveKNN
    # from AT.AD.algorithms.I_Forest import iForest
    from AT.consumers import ATConsumer
from experiment.consumers import ExperimentConsumer
# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html

ws_routes = []
if "EOSS" in settings.ACTIVE_MODULES:
    ws_routes.append(path('api/eoss/ws', EOSSConsumer))
if "AT" in settings.ACTIVE_MODULES:
    ws_routes.extend([
        # path('api/at/SARIMAX_AD', SARIMAX_AD),
        # path('api/at/adaptiveKNN', adaptiveKNN),
        # path('api/at/iForest', iForest),
        path('api/at/ws', ATConsumer.as_asgi()),
        path('api/at/experiment', ATExperimentConsumer.as_asgi())
    ])
ws_routes.extend([
    path('api/experiment', ExperimentConsumer.as_asgi()),
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