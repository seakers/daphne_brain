from django.urls import path, include

urlpatterns = [
    path('data/', include('EDL.data.urls')),
    path('dialogue/', include('EDL.dialogue.urls')),
]
