from django.urls import path

from . import views

urlpatterns = [
    path('import-data', views.ImportData.as_view()),
    path('set-target', views.SetTargetRegion.as_view()),
    path('venn-diagram-distance', views.VennDiagramDistance.as_view()),
]
