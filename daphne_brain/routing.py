from django.urls import path

from daphne_brain import settings
from experiment_at.consumers import ATExperimentConsumer

if "example_problem" in settings.ACTIVE_MODULES:
    from example_problem.consumers import ExampleConsumer
if "EOSS" in settings.ACTIVE_MODULES:
    from EOSS.consumers import EOSSConsumer
if "AT" in settings.ACTIVE_MODULES:
    # from AT.AD.algorithms.SARIMAX_AD import SARIMAX_AD
    # from AT.AD.algorithms.KNN import adaptiveKNN
    # from AT.AD.algorithms.I_Forest import iForest
    from AT.consumers import ATConsumer

from experiment.consumers import ExperimentConsumer
from daphne_ws.consumers import MycroftConsumer

# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html

ws_routes = []
if "example_problem" in settings.ACTIVE_MODULES:
    ws_routes.append(path('api/example_problem/ws', ExampleConsumer))
if "EOSS" in settings.ACTIVE_MODULES:
    ws_routes.append(path('api/eoss/ws', EOSSConsumer.as_asgi()))
if "AT" in settings.ACTIVE_MODULES:
    ws_routes.extend([
        path('api/at/ws', ATConsumer),
        path('api/at/experiment', ATExperimentConsumer)
    ])
ws_routes.extend([
    path('api/experiment', ExperimentConsumer.as_asgi()),
])
ws_routes.extend([
    path('api/mycroft', MycroftConsumer.as_asgi()),
])
