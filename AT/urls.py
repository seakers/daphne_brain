from django.urls import include
from django.urls import path

from AT import views

urlpatterns = [
    path('dialogue/', include('AT.dialogue.urls')),
    path('simulate', views.SimulateTelemetry.as_view(), name='SimulateTelemetry'),
    path('stop', views.StopTelemetry.as_view(), name='StopTelemetry'),
    path('receiveSeclssFeed', views.SeclssFeed.as_view(), name='SeclssFeed')
]

