from django.urls import path

from . import SARIMA
from . import WGAUSS

urlpatterns = [
    path('SARIMA', SARIMA.AD_SARIMA.as_view(), name='SARIMA'),
    path('WGAUSS', WGAUSS.AD_WGAUSS.as_view(), name='WGAUSS')
]