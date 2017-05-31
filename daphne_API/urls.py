from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^command$', views.Command.as_view(), name='command'),
    url(r'^commands$', views.CommandList.as_view(), name='question'),
]
