from django.urls import path

from . import views

urlpatterns = [

    # --> Features
    path('get-subject-features', views.GetSubjectFeatures.as_view()),

    # --> Sensitivities
    path('get-subject-sensitivities', views.GetSubjectSensitivities.as_view()),

    # --> Objective Space
    path('get-subject-objective-space', views.GetSubjectObjectiveSpace.as_view()),
    path('get-objective-group-information', views.GetObjectiveGroupInformation.as_view()),

    # --> Design Space
    path('get-subject-design-space', views.GetSubjectDesignSpace.as_view()),

    # --> Proactive Mode
    path('set-proactive-mode', views.SetProactiveMode.as_view())
]
