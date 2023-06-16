from django.urls import path, include

from AT import views

urlpatterns = [
    path('dialogue/', include('AT.dialogue.urls')),
    path('recommendation/', include('AT.recommendation.urls')),
    # **********
    path('receiveSeclssFeed', views.SeclssFeed.as_view(), name='receiveSeclssFeed'),
    path('receiveHeraFeed', views.HeraFeed.as_view(), name='receiveHeraFeed'),
    path('user_response', views.UserResponse.as_view(), name='user_response'),
    path('yesorno', views.YesOrNO.as_view(), name='yesorno'),
    path('pride_status', views.PrideStatus.as_view(), name='pride_status'),
    path('astrobee_status', views.AstrobeeStatus.as_view(), name='astrobee_status'),
    path('start_astrobee_procedure', views.StartAstrobeeProcedure.as_view(), name='start_astrobee_procedure'),
    path('requestDiagnosis', views.RequestDiagnosis.as_view(), name='RequestDiagnosis'),
    path('loadAllAnomalies', views.LoadAllAnomalies.as_view(), name='LoadAllAnomalies'),
    path('retrieveProcedureFromAnomaly', views.RetrieveProcedureFromAnomaly.as_view(),
         name='retrieveProcedureFromAnomaly'),
    path('retrieveInfoFromProcedure', views.RetrieveInfoFromProcedure.as_view(),
         name='retrieveInfoFromProcedure'),
    path('tutorialStatus', views.TutorialStatus.as_view()),
    path('completeTutorial', views.CompleteTutorial.as_view()),
]
