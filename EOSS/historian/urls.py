from django.urls import path

from . import views

urlpatterns = [
    path('get-missions', views.GetMissions.as_view())
]
