from django.urls import path

from daphne_brain import settings

if "EOSS" in settings.ACTIVE_MODULES:
    from EOSS.consumers import EOSSConsumer
if "AT" in settings.ACTIVE_MODULES:
    from AT.SARIMAX_AD import SARIMAX_AD
    from AT.KNN import adaptiveKNN
    from AT.I_Forest import iForest

from experiment.consumers import ExperimentConsumer

# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html

ws_routes = []
if "EOSS" in settings.ACTIVE_MODULES:
    ws_routes.append(path('api/eoss/ws', EOSSConsumer.as_asgi()))
if "AT" in settings.ACTIVE_MODULES:
    ws_routes.extend([
        path('api/anomaly/SARIMAX_AD', SARIMAX_AD.as_asgi()),
        path('api/anomaly/adaptiveKNN', adaptiveKNN.as_asgi()),
        path('api/anomaly/iForest', iForest.as_asgi()),
    ])
ws_routes.extend([
    path('api/experiment', ExperimentConsumer.as_asgi()),
])
