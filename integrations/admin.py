from django.contrib import admin

from integrations.models import ApiToken


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
	list_display = [ApiToken.fields.name, ApiToken.fields.user, ApiToken.fields.prefix, ApiToken.fields.created_at,
					ApiToken.fields.last_used_at]
	search_fields = [ApiToken.fields.name, ApiToken.fields.prefix]
	list_select_related = [ApiToken.fields.user]
	exclude = [ApiToken.fields.key_hash]
	readonly_fields = [ApiToken.fields.user, ApiToken.fields.name, ApiToken.fields.prefix, ApiToken.fields.last_used_at]
	ordering = [ApiToken.fields.created_at.desc()]

	def has_add_permission(self, request):
		return False
