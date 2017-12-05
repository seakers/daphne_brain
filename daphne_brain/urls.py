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


urlpatterns = [

    url(r'api/daphne/', include('daphne_API.urls')),

    url(r'api/ifeed/', include('iFEED_API.urls')),
    
    url(r'api/vassar/', include('VASSAR_API.urls')),
    
    url(r'api/critic/', include('critic_API.urls')),
    
    url(r'api/data-mining/', include('data_mining_API.urls')),

    url(r'api/experiment/', include('experiment_API.urls')),
        
    url(r'^server/admin/', admin.site.urls),
    url(r'^server/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

urlpatterns = format_suffix_patterns(urlpatterns)






