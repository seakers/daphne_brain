from django.urls import path, include

urlpatterns = [
    path('dialogue/', include('CA.dialogue.urls')),
]
