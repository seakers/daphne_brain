from django.urls import path, include

from dialogue.views import Command
from . import views

urlpatterns = [
    path('command', views.ATCommand.as_view(), name='command'),
]
