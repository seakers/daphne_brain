from django.urls import path, include

from . import views

urlpatterns = [
    path('command', views.CACommand.as_view(), name='command'),
    path('command_history', views.CACommandHistory.as_view(), name='command_history'),
    path('event', views.CAEvent.as_view(), name='event')
]