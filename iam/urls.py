from dj_rest_auth.registration.views import SocialAccountDisconnectView
from django.urls import include, path

from iam.views import GoogleConnect, GoogleLogin, SocialAccountListView

urlpatterns = [
	path('', include('allauth.urls')),
	path('auth/', include('dj_rest_auth.urls')),
	path('auth/registration/', include('dj_rest_auth.registration.urls')),
	path('auth/google/', GoogleLogin.as_view(), name='google_login'),
	path('auth/google/connect/', GoogleConnect.as_view(), name='google_connect'),
	path('auth/social-accounts/', SocialAccountListView.as_view(), name='social_account_list'),
	path(
		'auth/social-accounts/<int:pk>/disconnect/', SocialAccountDisconnectView.as_view(),
		name='social_account_disconnect',
	),
]
