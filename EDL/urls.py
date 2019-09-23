from django.urls import path, include

from daphne_brain import settings

if "EDL" in settings.ACTIVE_MODULES:
    urlpatterns = [
        path('data/', include('EDL.data.urls')),
        path('dialogue/', include('EDL.dialogue.urls')),
    ]
