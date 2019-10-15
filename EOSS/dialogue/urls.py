from django.urls import path, include

from dialogue.views import Command
from . import views

urlpatterns = [
    path('command', views.EOSSCommand.as_view(), name='command'),
    path('commands', views.CommandList.as_view(), name='command_list'),
]
