from django.urls import path

from . import views

urlpatterns = [
    path('check-ga', views.CheckGA.as_view()),
]
