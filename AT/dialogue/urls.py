from django.urls import path

from AT.dialogue import views

urlpatterns = [
    path('command', views.ATCommand.as_view(), name='command'),
    path('clear-history', views.ATClearHistory.as_view(), name='clear-history'),
]
