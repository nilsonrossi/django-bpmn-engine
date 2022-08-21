from rest_framework import serializers
from django_bpmn_engine.core.models import Workflow


class WorkflowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        exclude = ["id"]