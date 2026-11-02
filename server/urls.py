from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/iam/', include('iam.urls')),
    # Include the workspace URLs
    path('api/', include('workspaces.urls')),
]

