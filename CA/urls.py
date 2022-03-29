from django.urls import path, include

urlpatterns = [
    path('dialogue/', include('CA.dialogue.urls')),
    path('stats/', include('CA.stats.urls')),
]
