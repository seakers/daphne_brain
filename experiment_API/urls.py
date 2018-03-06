from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'start-experiment$', views.StartExperiment.as_view()),
    url(r'start-stage$', views.StartStage.as_view()),
    url(r'finish-stage$', views.FinishStage.as_view()),
    url(r'add-action$', views.AddAction.as_view()),
    url(r'update-state$', views.UpdateState.as_view()),
    url(r'reload-experiment$', views.ReloadExperiment.as_view()),
    url(r'finish-experiment$', views.EndExperiment.as_view())
]
