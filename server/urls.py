from django.contrib import admin
from django.urls import path, include

urlpatterns = [
	path('admin/', admin.site.urls),
	path('api/iam/', include('iam.urls')),
	path('api/papers/', include('papers.urls')),
	path('api/workspaces/', include('workspaces.urls')),
	path('api/integrations/', include('integrations.urls')),
]
