from django.urls import path, include

from AT import views

urlpatterns = [
    path('dialogue/', include('AT.dialogue.urls')),
    path('recommendation/', include('AT.recommendation.urls')),
    # **********
    path('receiveSeclssFeed', views.SeclssFeed.as_view(), name='receiveSeclssFeed'),
    path('requestDiagnosis', views.RequestDiagnosis.as_view(), name='RequestDiagnosis'),
    path('loadAllAnomalies', views.LoadAllAnomalies.as_view(), name='LoadAllAnomalies'),
    path('retrieveProcedureFromAnomaly', views.RetrieveProcedureFromAnomaly.as_view(),
         name='retrieveProcedureFromAnomaly'),
    path('retrieveInfoFromProcedure', views.RetrieveInfoFromProcedure.as_view(),
         name='retrieveInfoFromProcedure'),
]
