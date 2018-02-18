from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'get-driving-features/$', views.GetDrivingFeatures.as_view()),
    url(r'get-driving-features-automated/$', views.GetDrivingFeaturesAutomated.as_view()),
    url(r'get-marginal-driving-features/$', views.GetMarginalDrivingFeatures.as_view()),
    url(r'cluster-data/$', views.ClusterData.as_view()),
    url(r'get-cluster/$', views.GetCluster.as_view()),
]
