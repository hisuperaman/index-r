from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import (
	SocialAccountListView as _SocialAccountListView, SocialConnectView, SocialLoginView,
)

from iam.serializers import SocialAccountSerializer


class GoogleLogin(SocialLoginView):
	adapter_class = GoogleOAuth2Adapter
	callback_url = "postmessage"
	client_class = OAuth2Client


class GoogleConnect(SocialConnectView):
	adapter_class = GoogleOAuth2Adapter
	callback_url = "postmessage"
	client_class = OAuth2Client


class SocialAccountListView(_SocialAccountListView):
	"""Lists the caller's connected sign-in accounts."""
	serializer_class = SocialAccountSerializer
	pagination_class = None
