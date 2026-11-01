from django.contrib import admin
from django.urls import path, include

urlpatterns = [
	path('admin/', admin.site.urls),
	path('iam/', include('iam.urls')),
    path('api/', include('workspaces.urls')),
]
