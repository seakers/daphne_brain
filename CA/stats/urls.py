from django.urls import path, include

from . import views

urlpatterns = [
    path('updatemodel', views.UpdateModel.as_view(), name='updatemodel'),
]