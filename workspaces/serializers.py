from rest_framework import serializers

from workspaces.models import Paper, Workspace


class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = ["id", "title", "file", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkspaceSerializer(serializers.ModelSerializer):
    papers = PaperSerializer(many=True, read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "name", "papers", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]