from django.urls import path, include

from . import views

urlpatterns = [
    path('tse-assigning-data', views.TseAssigningData.as_view(), name='tse-assigning-data'),
    path('start-assigning-tse', views.StartAssigningTSE.as_view(), name='start-assigning-tse'),
    path('start-combining-tse', views.StartCombiningTSE.as_view(), name='start-combining-tse'),
    path('add-ga-design', views.AddGADesign.as_view(), name='add-ga-design'),
    path('poll-ga-designs', views.PollGADesigns.as_view(), name='poll-ga-designs'),
]