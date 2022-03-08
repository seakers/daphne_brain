from django.urls import path

from . import views

urlpatterns = [
    path('check-connection', views.CheckConnection.as_view()),
]