from django.urls import path

from . import views

urlpatterns = [
    path('evaluate-architecture', views.EvaluateArchitecture.as_view()),
]
