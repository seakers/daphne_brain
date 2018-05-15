from django.urls import path

from . import SARIMA
from . import WGAUSS
from . import views
from .analysis import seasonality
from .analysis import detectMultivariateAnomalies
from .analysis import AnomalyDetectionAgreements
from .analysis import Correlations
from .analysis import CountAnomalies

urlpatterns = [
    path('SARIMA', SARIMA.AD_SARIMA.as_view(), name='SARIMA'),
    path('ADWindowedStats', WGAUSS.ADWindowedStats.as_view(), name='ADWindowedStats'),
    path('read-data', views.ReadUploadedData.as_view(), name='read-data'),
    path('import-data', views.ImportData.as_view(), name='import-data'),

    # Daphne questions
    path('analysis/RemoveVariables', views.RemoveVariables.as_view(), name='RemoveVariables'),
    path('analysis/CheckSeasonality', seasonality.CheckSeasonality.as_view(), name='CheckSeasonality'),
    path('analysis/detectThreshold', detectMultivariateAnomalies.DetectMultivariateAnomaliesThreshold.as_view(),
         name='detectThreshold'),
    path('analysis/detectNumber', detectMultivariateAnomalies.DetectMultivariateAnomaliesNumber.as_view(),
         name='detectNumber'),
    path('analysis/MethodsAgreement', AnomalyDetectionAgreements.AgreementMethods.as_view(), name='MethodsAgreement'),
    path('analysis/Correlations', Correlations.Correlation.as_view(), name='Correlations'),
    path('analysis/CountAnomalies', CountAnomalies.CountAnomalies.as_view(), name='CountAnomalies')
]
