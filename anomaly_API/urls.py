from django.urls import path

from . import SARIMA
from . import WGAUSS
from . import views
from .analysis import seasonality
from .analysis import detectMultivariateAnomalies

urlpatterns = [
    path('SARIMA', SARIMA.AD_SARIMA.as_view(), name='SARIMA'),
    path('ADWindowedStats', WGAUSS.ADWindowedStats.as_view(), name='ADWindowedStats'),
    path('read-data', views.ReadUploadedData.as_view(), name='read-data'),
    path('import-data', views.ImportData.as_view(), name='import-data'),

    # Daphne questions
    path('analysis/CheckSeasonality', seasonality.CheckSeasonality.as_view(), name='CheckSeasonality'),
    path('analysis/detectThreshold', detectMultivariateAnomalies.DetectMultivariateAnomaliesThreshold.as_view(),
         name='detectThreshold'),
    path('analysis/detectNumber', detectMultivariateAnomalies.DetectMultivariateAnomaliesNumber.as_view(),
         name='detectNumber')
]
