from django.urls import path

from . import views

urlpatterns = [
    path('login', views.Login.as_view(), name='login'),
    path('logout', views.Logout.as_view(), name='logout'),
    path('register', views.Register.as_view(), name='register'),
    path('reset-password', views.ResetPassword.as_view(), name='reset-password'),
    path('check-status', views.CheckStatus.as_view(), name='check-status'),
    path('generate-session', views.GenerateSession.as_view(), name='generate-session'),
<<<<<<< HEAD

    path('check-status-hasura', views.CheckStatusHasura.as_view(), name='check-status-hasura'),
    path('get-user-pk', views.GetUserPk.as_view(), name='get-user-pk')
=======
    path('confirm-guest', views.ConfirmGuest.as_view(), name='confirm-guest')
>>>>>>> master
]
