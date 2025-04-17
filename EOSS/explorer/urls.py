from django.urls import path

from . import views

urlpatterns = [
    path('start-ga', views.StartGA.as_view()),
    path('stop-ga', views.StopGA.as_view()),
    path('check-ga', views.CheckGA.as_view()),
]
