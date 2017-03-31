"""daphne_brain URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns

from iFEED_API import views as iFEEDViews
from VASSAR_API import views as VASSARViews
from data_mining_API import views as DataMiningViews
from chatbox_API import views as ChatboxViews

urlpatterns = [
    url(r'ifeed/import-data/$', iFEEDViews.importData.as_view()),
    url(r'vassar/get-orbit-list/$', VASSARViews.getOrbitList.as_view()),
    url(r'vassar/get-instrument-list/$', VASSARViews.getInstrumentList.as_view()),
    url(r'vassar/intialize-jess/$', VASSARViews.initializeJess.as_view()),
    url(r'vassar/evaluate-architecture/$', VASSARViews.evaluateArchitecture.as_view()),
    url(r'data-mining/get-driving-features/$', DataMiningViews.getDrivingFeatures.as_view()),

    url(r'chat/update-utterance/$', ChatboxViews.updateUtterance.as_view()),

    url(r'^server/admin/', admin.site.urls),
    url(r'^server/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

urlpatterns = format_suffix_patterns(urlpatterns)


"""
Write functions interfacing with the front end

 - Sending WS messages
1. Send commands to iFEED
2. broadcast messages to chat and/or mycroft
3. Send questions and commands to mycroft for parsing
 
 - Receiving http commands
1. From iFEED
2. From Mycroft
3. From Chat server
"""









