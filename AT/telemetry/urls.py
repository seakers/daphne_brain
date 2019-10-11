from django.urls import path

from AT.telemetry import views

urlpatterns = [
    path('simulate', views.SimulateTelemetry.as_view(), name='SimulateTelemetry'),
]