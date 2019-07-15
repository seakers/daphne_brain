from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from daphne_API.consumers import DaphneConsumer
from anomaly_API.SARIMAX_AD import SARIMAX_AD
from anomaly_API.KNN import adaptiveKNN
from anomaly_API.I_Forest import iForest
from data_mining_API.consumers import DataMiningConsumer

# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html
from experiment_API.consumers import ExperimentConsumer

application = ProtocolTypeRouter({
    # Route all WebSocket requests to our custom chat handler.
    # We actually don't need the URLRouter here, but we've put it in for
    # illustration. Also note the inclusion of the AuthMiddlewareStack to
    # add users and sessions - see http://channels.readthedocs.io/en/latest/topics/authentication.html
    'websocket': AuthMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            path('api/daphne', DaphneConsumer),
            path('api/experiment', ExperimentConsumer),
            path('api/anomaly/SARIMAX_AD', SARIMAX_AD),
            path('api/anomaly/adaptiveKNN', adaptiveKNN),
            path('api/anomaly/iForest', iForest),
            path('api/ifeed/data-mining', DataMiningConsumer),
        ]),
    ),

})