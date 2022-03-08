from django.urls import path

from . import views

urlpatterns = [
    # Run data mining
    path('get-driving-features', views.GetDrivingFeatures.as_view()),
]
