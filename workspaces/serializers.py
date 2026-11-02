from rest_framework import serializers
from workspaces.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        # Explicitly list fields. 'user' is read-only so clients can't spoof it.
        fields = ["id", "name", "user", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


