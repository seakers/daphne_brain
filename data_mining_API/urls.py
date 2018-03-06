from django.urls import path

from . import views

urlpatterns = [
    path('get-driving-features', views.GetDrivingFeatures.as_view()),
    path('get-marginal-driving-features-conjunctive', views.GetMarginalDrivingFeaturesConjunctive.as_view()),
    path('get-marginal-driving-features', views.GetMarginalDrivingFeatures.as_view())
]
