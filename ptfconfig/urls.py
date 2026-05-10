"""
URL configuration for ptfconfig project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
#ptfconfig
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('ptfapp1.urls', namespace='ptfapp1')),   # portfolio is at root
    path('dashboard/',include('ptfapp2.urls', namespace='ptfapp2')),   # dashboard at /dashboard/
    
    # This registers: /accounts/google/login/
    #                 /accounts/google/login/callback/
    path('accounts/', include('allauth.urls')),   # for sign up - new users 
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
