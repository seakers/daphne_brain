from django.urls import path

from . import views

urlpatterns = [
    path('change-port', views.ChangePort.as_view()),
    path('clear-session', views.ClearSession.as_view(), name='clear_session'),
    path('active-feedback-settings', views.ActiveFeedbackSettings.as_view(), name='set_active_feedback_settings'),
]
