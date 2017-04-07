from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'get-driving-features/$', views.GetDrivingFeatures.as_view()),
]
