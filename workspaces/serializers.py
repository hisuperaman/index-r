from rest_framework import serializers

from .models import Workspace
from .permissions import OWNER_FIELD


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        exclude = [OWNER_FIELD]
