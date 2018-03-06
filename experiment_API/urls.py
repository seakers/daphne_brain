from django.urls import path

from . import views

urlpatterns = [
    path('start-experiment', views.StartExperiment.as_view()),
    path('start-stage', views.StartStage.as_view()),
    path('finish-stage', views.FinishStage.as_view()),
    path('add-action', views.AddAction.as_view()),
    path('update-state', views.UpdateState.as_view()),
    path('reload-experiment', views.ReloadExperiment.as_view()),
    path('finish-experiment', views.EndExperiment.as_view())
]
