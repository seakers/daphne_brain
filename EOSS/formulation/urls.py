from django.urls import path

from . import views

urlpatterns = [

    # --> Start Agent
    path('toggle-agent', views.ToggleAgent.as_view()),
    path('formulation-change', views.FormulationChange.as_view()),

]
