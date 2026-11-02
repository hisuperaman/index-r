from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from integrations.models import ApiToken


class ApiTokenSerializer(ModelSerializer):
	token = CharField(source='raw_token', read_only=True)

	class Meta:
		model = ApiToken
		read_only_fields = [
			ApiToken.fields.id, ApiToken.fields.prefix, ApiToken.fields.created_at, ApiToken.fields.last_used_at, 'token',
		]
		fields = [*read_only_fields, ApiToken.fields.name]

	def create(self, validated_data):
		return ApiToken.objects.issue(validated_data[ApiToken.fields.user], validated_data[ApiToken.fields.name])
