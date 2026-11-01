from allauth.account.admin import EmailAddressAdmin as BaseEmailAddressAdmin
from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from enums.User import UserField
from iam.forms import UserCreationForm, UserChangeForm
from iam.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	add_form = UserCreationForm
	form = UserChangeForm

	list_display = (UserField.email.value, UserField.first_name.value, UserField.last_name.value,
					UserField.is_staff.value, UserField.is_active.value)
	list_filter = (UserField.is_staff.value, UserField.is_active.value, UserField.is_superuser.value)

	ordering = (UserField.email.value,)
	search_fields = (UserField.email.value,)

	fieldsets = (
		(None, {"fields": (UserField.email.value, UserField.password.value)}),
		("Personal info", {"fields": (UserField.first_name.value, UserField.last_name.value)}),
		("Permissions", {
			"fields": (UserField.is_active.value, UserField.is_staff.value, UserField.is_superuser.value,
					   UserField.groups.value,
					   UserField.user_permissions.value)}),
		("Important dates", {"fields": (UserField.last_login.value, UserField.date_joined.value)}),
	)

	add_fieldsets = (
		(None, {
			"classes": ("wide",),
			"fields": (UserField.email.value, "password1", "password2", UserField.is_staff.value,
					   UserField.is_superuser.value, UserField.is_active.value),
		}),
	)


admin.site.unregister(EmailAddress)


@admin.register(EmailAddress)
class EmailAddressAdmin(BaseEmailAddressAdmin):
	readonly_fields = BaseEmailAddressAdmin.readonly_fields + (UserField.email.value,)
