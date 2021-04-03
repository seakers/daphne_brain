from django.urls import path

from . import views

urlpatterns = [
    path('connect', views.Connect.as_view(), name="vassar_connect"),
]
