from django.urls import path

from . import views

urlpatterns = [
    path('command', views.Command.as_view(), name='command'),
    path('commands', views.CommandList.as_view(), name='command_list'),
]
