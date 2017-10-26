from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'get-orbit-list/$', views.GetOrbitList.as_view()),
    url(r'get-instrument-list/$', views.GetInstrumentList.as_view()),
    
    url(r'evaluate-architecture/$', views.EvaluateArchitecture.as_view()),
    
    url(r'critique-architecture/$', views.CritiqueArchitecture.as_view()),
    
    url(r'initialize-jess/$', views.InitializeJess.as_view()),
]
