from django.urls import path

from . import views

urlpatterns = [
    path('command', views.EDLCommand.as_view(), name='command'),
]
