from django.contrib import admin

from enums.Workspace import WorkspaceLookup
from workspaces.models import TrackedTopic, Workspace


class TrackedTopicInline(admin.TabularInline):
	model = TrackedTopic
	fields = [TrackedTopic.fields.query, TrackedTopic.fields.checked_at]
	readonly_fields = [TrackedTopic.fields.checked_at]
	extra = 0


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
	list_display = [Workspace.fields.name, Workspace.fields.user, Workspace.fields.papers_only, Workspace.fields.created_at]
	list_filter = [Workspace.fields.papers_only]
	search_fields = [Workspace.fields.name, WorkspaceLookup.user__email.value]
	list_select_related = [Workspace.fields.user]
	ordering = [Workspace.fields.created_at.desc()]
	inlines = [TrackedTopicInline]
