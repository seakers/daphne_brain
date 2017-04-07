from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^question$', views.Question.as_view(), name='question'),
]
