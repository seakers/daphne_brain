from django.urls import path

from . import views

urlpatterns = [
    path('criticize-architecture', views.CriticizeArchitecture.as_view()),
]
