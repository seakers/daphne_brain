from django.conf.urls import url

from . import views

urlpatterns = [
    
    url(r'import-data/$', views.ImportData.as_view()),
    url(r'venn-diagram-distance/$', views.VennDiagramDistance.as_view()),

    url(r'update-utterance/$', views.UpdateUtterance.as_view()),
    url(r'update-system-response/$', views.UpdateSystemResponse.as_view()),
        
    url(r'apply-feature-expression/$',views.ApplyFeatureExpression.as_view()),
]
