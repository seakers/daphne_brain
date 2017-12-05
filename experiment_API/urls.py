from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'start-experiment$', views.StartExperiment.as_view()),
    url(r'reload-experiment$', views.ReloadExperiment.as_view()),
    url(r'stop-experiment$', views.EndExperiment.as_view())
    
]
