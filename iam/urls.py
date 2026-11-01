from django.urls import path, include

from iam.views import GoogleLogin

urlpatterns = [
	path('', include('allauth.urls')),
	path('auth/', include('dj_rest_auth.urls')),
	path('auth/registration/', include('dj_rest_auth.registration.urls')),
	path('auth/google/', GoogleLogin.as_view(), name='google_login'),
]
