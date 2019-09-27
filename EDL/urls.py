from django.urls import path, include
from . import views

urlpatterns = [
    path('data/', include('EDL.data.urls')),
    path('dialogue/', include('EDL.dialogue.urls')),
    path('metrics-of-interest', views.MetricsOfInterest.as_view(), name='import_names'),
    path('sensitivity-analysis', views.SensitivityAnalysis.as_view(), name='sensitivity_analysis'),
    path('import-data', views.ImportDataAvail.as_view(), name="import_data")
]

