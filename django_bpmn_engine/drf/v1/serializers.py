from rest_framework import serializers

from django_bpmn_engine.core.models import MessageTaskEvent
from django_bpmn_engine.core.models import ServiceTask
from django_bpmn_engine.core.models import Workflow
from django_bpmn_engine.core.models import WorkflowInstance
from django_bpmn_engine.core.models import WorkflowTaskInstance


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        exclude = ["id"]


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowInstance
        exclude = ["id"]


class WorkflowTaskInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTaskInstance
        exclude = ["id"]


class ServiceTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTask
        exclude = ["id"]


class MessageTaskEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTaskEvent
        exclude = ["id"]


class WorkflowStatsSerializer(serializers.Serializer):
    workflow_name = serializers.CharField()
    stats = serializers.DictField()
