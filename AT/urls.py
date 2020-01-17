from django.urls import path, include

from AT import views

urlpatterns = [
    path('dialogue/', include('AT.dialogue.urls')),
    path('recommendation/', include('AT.recommendation.urls')),
    path('simulate', views.SimulateTelemetry.as_view(), name='SimulateTelemetry'),
    path('stop', views.StopTelemetry.as_view(), name='StopTelemetry'),
    path('startSeclssFeed', views.StartSeclssFeed.as_view(), name='startSeclssFeed'),
    path('receiveSeclssFeed', views.SeclssFeed.as_view(), name='receiveSeclssFeed')
]
