from django.urls import path, include

from . import views

urlpatterns = [
    path('command', views.ExampleCommand.as_view(), name='command'),
    path('history', views.ExampleHistory.as_view(), name='history'),
    path('clear-history', views.ExampleClearHistory.as_view(), name='clear-history'),
    path('commands', views.CommandList.as_view(), name='command_list'),
]
