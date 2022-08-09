from django.urls import path, include

urlpatterns = [
    path('analyst/', include('EOSS.analyst.urls')),
    path('critic/', include('EOSS.critic.urls')),
    path('data/', include('EOSS.data.urls')),
    path('dialogue/', include('EOSS.dialogue.urls')),
    path('engineer/', include('EOSS.engineer.urls')),
    path('explorer/', include('EOSS.explorer.urls')),
    path('settings/', include('EOSS.settings.urls')),
    path('teacher/', include('EOSS.teacher.urls')),
    path('vassar/', include('EOSS.vassar.urls'))
]
