from django.urls import path

from . import views

urlpatterns = [
    path('get-orbit-list', views.GetOrbitList.as_view()),
    path('get-instrument-list', views.GetInstrumentList.as_view()),
    
    path('evaluate-architecture', views.EvaluateArchitecture.as_view()),
    path('run-local-search', views.RunLocalSearch.as_view()),

    path('change-port', views.ChangePort.as_view()),

    path('start-ga', views.StartGA.as_view()),
    path('stop-ga', views.StopGA.as_view()),
    path('check-ga', views.CheckGA.as_view()),

    path('get-arch-details', views.GetArchDetails.as_view()),
    path('get-subobjective-details', views.GetSubobjectiveDetails.as_view())
]
