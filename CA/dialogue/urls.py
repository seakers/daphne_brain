from django.urls import path, include

from . import views

urlpatterns = [
    path('cacommand', views.CACommand.as_view(), name='cacommand'),
    path('lmcommand', views.LMCommand.as_view(), name='lmcommand')
]
