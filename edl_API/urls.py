from django.urls import path

from . import views

urlpatterns = [
    path('metrics-of-interest', views.MetricsOfInterest.as_view(), name='import_names'),
    path('sensitivity-analysis', views.SensitivityAnalysis.as_view(), name = 'sensitivity_analysis'),
    path('import-data', views.ImportDataAvail.as_view(), name ="import_data")
]
