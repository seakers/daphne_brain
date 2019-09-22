from django.urls import path, include

urlpatterns = [
    path('engineer/', include('EOSS.engineer.urls')),
    path('analyst/', include('EOSS.analyst.urls')),
    path('explorer/', include('EOSS.explorer.urls')),
    # path('historian/', include('EOSS.historian.urls')),  # No APIs for now
    path('critic/', include('EOSS.critic.urls')),
    path('data/', include('EOSS.data.urls')),
    path('settings/', include('EOSS.settings.urls')),
    path('dialogue/', include('EOSS.dialogue.urls')),
]
