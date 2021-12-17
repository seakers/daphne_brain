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
    path('evaluate-architecture-set', views.EvaluateArchitectureSet.as_view())
]
