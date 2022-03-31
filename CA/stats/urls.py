from django.urls import path, include

from . import views

urlpatterns = [
    path('updatemodel', views.UpdateModel.as_view(), name='updatemodel'),
    path('updatemodeltid', views.UpdateModelTID.as_view(), name='updatemodeltid'),
    path('adaptivequestion', views.AdaptiveQuestion.as_view(), name='adaptivequestion'),
]