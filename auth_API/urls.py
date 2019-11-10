from django.urls import path

from . import views

urlpatterns = [
    path('login', views.Login.as_view(), name='login'),
    path('logout', views.Logout.as_view(), name='logout'),
    path('register', views.Register.as_view(), name='register'),
    path('reset-password', views.ResetPassword.as_view(), name='reset-password'),
    path('check-status', views.CheckStatus.as_view(), name='check-status'),
    path('generate-session', views.GenerateSession.as_view(), name='generate-session')
]
