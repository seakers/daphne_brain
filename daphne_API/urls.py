from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^command$', views.Command.as_view(), name='question'),
]
