from django.urls import path

from . import views

urlpatterns = [
    path('get-subject-features', views.GetSubjectFeatures.as_view()),


    path('get-subject-sensitivities', views.GetSubjectSensitivities.as_view()),


    path('get-subject-objective-space', views.GetSubjectObjectiveSpace.as_view()),


    path('get-subject-design-space', views.GetSubjectDesignSpace.as_view())
]
