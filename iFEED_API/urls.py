from django.conf.urls import url

from . import views

urlpatterns = [
    
    url(r'import-data/$', views.ImportData.as_view()),
    url(r'set-target/$', views.SetTargetRegion.as_view()),
    
    
    # url(r'venn-diagram-distance/$', views.VennDiagramDistance.as_view()),
]
