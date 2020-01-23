from django.urls import path, include
from . import views

urlpatterns = [
    path('data/', include('EDL.data.urls')),
    path('dialogue/', include('EDL.dialogue.urls')),
    path('metrics-of-interest', views.MetricsOfInterest.as_view(), name='import_names'),
    path('sensitivity-analysis', views.SensitivityAnalysis.as_view(), name='sensitivity_analysis'),
    path('import-data', views.ImportDataAvail.as_view(), name="import_data"),
    path('import-data-db', views.ImportDataToDB.as_view(), name="import_data_to_db"),
    path('edl-data-mining', views.EDLDataMining.as_view(), name="edl_data_mining"),
    path('chat-history', views.ChatHistory.as_view(), name="edl_chat"),

]

