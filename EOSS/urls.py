from django.urls import path, include

urlpatterns = [

    # --> Regular Operations
    path('data/', include('EOSS.data.urls')),
    path('settings/', include('EOSS.settings.urls')),

    # --> Dialogue
    path('dialogue/', include('EOSS.dialogue.urls')),

    # --> Roles
    path('analyst/', include('EOSS.analyst.urls')),
    path('critic/', include('EOSS.critic.urls')),
    path('engineer/', include('EOSS.engineer.urls')),
    path('explorer/', include('EOSS.explorer.urls')),
    path('teacher/', include('EOSS.teacher.urls'))
]
