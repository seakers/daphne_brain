from django.urls import path, include

from . import views

urlpatterns = [
    path('command', views.EOSSCommand.as_view(), name='command'),
    path('history', views.EOSSHistory.as_view(), name='history'),
    path('commands', views.CommandList.as_view(), name='command_list'),
]