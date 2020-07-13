from django.urls import path, include

from AT import views

urlpatterns = [
    path('dialogue/', include('AT.dialogue.urls')),
    path('recommendation/', include('AT.recommendation.urls')),
    # **********
    # Choose just one of the two following lines
    path('start_fake_telemetry', views.SimulateTelemetry.as_view(), name='SimulateTelemetry'),
    path('start_real_telemetry', views.StartSeclssFeed.as_view(), name='startSeclssFeed'),
    # **********
    path('start_hub_thread', views.StartHubThread.as_view(), name='Start Hub Thread'),
    path('start_real_at_thread', views.StartRealATThread.as_view(), name='Start Real AT Thread'),
    path('start_fake_at_thread', views.StartFakeATThread.as_view(), name='Start Fake AT Thread'),
    path('stop_real_telemetry', views.StopRealTelemetry.as_view(), name='StopRealTelemetry'),
    path('stop_fake_telemetry', views.StopFakeTelemetry.as_view(), name='StopFakeTelemetry'),
    path('receiveSeclssFeed', views.SeclssFeed.as_view(), name='receiveSeclssFeed'),
    path('requestDiagnosis', views.RequestDiagnosis.as_view(), name='RequestDiagnosis'),
    path('loadAllAnomalies', views.LoadAllAnomalies.as_view(), name='LoadAllAnomalies'),
    path('retrieveProcedureFromAnomaly', views.RetrieveProcedureFromAnomaly.as_view(),
         name='retrieveProcedureFromAnomaly'),
    path('retrieveInfoFromProcedure', views.RetrieveInfoFromProcedure.as_view(),
         name='retrieveInfoFromProcedure'),
]
