from django.urls import path

from . import views

urlpatterns = [
    path('get-orbit-list', views.GetOrbitList.as_view()),
    path('get-instrument-list', views.GetInstrumentList.as_view()),
    
    path('evaluate-architecture', views.EvaluateArchitecture.as_view()),
    path('evaluate-false-architectures', views.EvaluateFalseArchitecture.as_view()),

    path('run-local-search', views.RunLocalSearch.as_view()),

    path('get-arch-details', views.GetArchDetails.as_view()),
    path('get-subobjective-details', views.GetSubobjectiveDetails.as_view()),
    path('get-measurements', views.GetMultArchMeas.as_view()),
    path('get-scheduling-eval', views.GetSchedulingEval.as_view()),
    path('get-missions', views.GetMissions.as_view()),
    path('get-mission-measurements', views.GetMissions.as_view()),
    path('start-ga', views.StartSchedulingGA.as_view()),
    path('start-enumeration', views.StartEnumeration.as_view()),
    path('get-data-continuity', views.DataContinuityTable.as_view())
]
