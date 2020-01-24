from django.urls import path, include

from AT import views

urlpatterns = [
    path('dialogue/', include('AT.dialogue.urls')),
    path('recommendation/', include('AT.recommendation.urls')),
    # **********
    # Choose just one of the two following lines
    path('startTelemetry', views.SimulateTelemetry.as_view(), name='SimulateTelemetry'),
    # path('startTelemetry', views.StartSeclssFeed.as_view(), name='startSeclssFeed'),
    # **********
    path('stop', views.StopTelemetry.as_view(), name='StopTelemetry'),
    path('receiveSeclssFeed', views.SeclssFeed.as_view(), name='receiveSeclssFeed'),
    path('requestDiagnosis', views.RequestDiagnosis.as_view(), name='RequestDiagnosis')
]
