from django.conf.urls import url

from . import views

urlpatterns = [
    
    url(r'import-data/$', views.ImportData.as_view()),
    url(r'venn-diagram-distance/$', views.VennDiagramDistance.as_view()),
    
    url(r'update-feature-application-status/$', views.UpdateFeatureApplicationStatus.as_view()),
    url(r'request-feature-application-status/$',views.RequestFeatureApplicationStatus.as_view()),
    
    url(r'apply-feature-expression/$',views.ApplyFeatureExpression.as_view()),
]
