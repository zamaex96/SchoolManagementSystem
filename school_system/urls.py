"""
URL configuration for school_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path

# AAPS_Management_System/urls.py
from django.contrib import admin
from django.urls import path, include # Make sure 'include' is imported
from django.conf import settings             # Import settings
from django.conf.urls.static import static # Import static
# Import the auth views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    # Tell Django that any request to the root URL ('')
    # should be handled by the URL patterns defined in 'core.urls'
    path('', include('core.urls')), # <-- ADD THIS LINE
    # --- ADD THIS FOR AUTH URLS (Login, Logout, Password Reset, etc.) ---
    path('accounts/', include('django.contrib.auth.urls')),
    # You could also use a prefix, like: path('app/', include('core.urls'))
    # Then your homepage would be at /app/ instead of /
    # Add authentication URLs


]

# --- Add this block for development media serving ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- End block ---