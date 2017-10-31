from django.conf.urls import url

from . import views

urlpatterns = [
    
    url(r'criticize-architecture/$', views.CriticizeArchitecture.as_view()),

]
