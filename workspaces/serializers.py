from rest_framework.serializers import ModelSerializer

from workspaces.models import Workspace


class WorkspaceSerializer(ModelSerializer):
	class Meta:
		model = Workspace
		fields = [Workspace.fields.id, Workspace.fields.name, Workspace.fields.created_at, Workspace.fields.updated_at]
		read_only_fields = [Workspace.fields.id, Workspace.fields.created_at, Workspace.fields.updated_at]
