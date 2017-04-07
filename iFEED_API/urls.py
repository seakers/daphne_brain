from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'import-data/$', views.ImportData.as_view()),
    url(r'apply-filter/$', views.ApplyFilter.as_view()),
    url(r'cancel-selections/$', views.CancelSelections.as_view()),
    url(r'venn-diagram-distance/$', views.VennDiagramDistance.as_view()),
    url(r'update-feature-status-chart/$', views.UpdateFeatureStatusChart.as_view()),
]
