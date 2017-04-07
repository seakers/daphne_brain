from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'update-utterance/$', views.updateUtterance.as_view()),
    url(r'update-system-response/$', views.updateSystemResponse.as_view()),
]
