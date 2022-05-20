from django.urls import path

from . import views

urlpatterns = [
    path('start-experiment', views.StartExperiment.as_view()),
    path('start-stage/<int:stage>', views.StartStage.as_view()),
    path('finish-stage/<int:stage>', views.FinishStage.as_view()),
    path('reload-experiment', views.ReloadExperiment.as_view()),
    path('finish-experiment', views.FinishExperiment.as_view()),
    path('situational-awareness', views.SituationalAwareness.as_view()),
    path('workload', views.Workload.as_view()),
    path('confidence', views.Confidence.as_view()),
    path('send-msg-correct', views.SendMsgCorrect.as_view()),
    path('send-msg-incorrect', views.SendMsgIncorrect.as_view()),
    path('subject-list', views.SubjectList.as_view()),
    path('get-state', views.GetState.as_view()),
    path('finish-experiment-from-mcc', views.FinishExperimentFromMcc.as_view()),
    path('force-finish-experiment-from-mcc', views.ForceFinishExperimentFromMcc.as_view()),
    path('turn-off-alarms', views.TurnOffAlarms.as_view())
]
