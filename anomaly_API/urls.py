from django.urls import path

from . import SARIMA
from . import WGAUSS
from . import views

urlpatterns = [
    path('SARIMA', SARIMA.AD_SARIMA.as_view(), name='SARIMA'),
    path('ADWindowedStats', WGAUSS.ADWindowedStats.as_view(), name='ADWindowedStats'),
    path('import-data', views.ImportData.as_view(), name='import-data')
]