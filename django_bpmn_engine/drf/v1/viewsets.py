import logging

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django_bpmn_engine.core.models import MessageTaskEvent
from django_bpmn_engine.core.models import ServiceTask
from django_bpmn_engine.core.models import ServiceTaskState
from django_bpmn_engine.core.models import Workflow
from django_bpmn_engine.core.models import WorkflowTaskInstance
from django_bpmn_engine.core.workflow.service import WorkflowService
from django_bpmn_engine.core.workflow.service import run_workflow
from django_bpmn_engine.drf.v1.serializers import MessageTaskEventSerializer
from django_bpmn_engine.drf.v1.serializers import ServiceTaskSerializer
from django_bpmn_engine.drf.v1.serializers import WorkflowInstanceSerializer
from django_bpmn_engine.drf.v1.serializers import WorkflowSerializer
from django_bpmn_engine.drf.v1.serializers import WorkflowStatsSerializer
from django_bpmn_engine.drf.v1.serializers import WorkflowTaskInstanceSerializer

logger = logging.getLogger(__name__)


class BaseSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 50


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().order_by("-created_at")
    serializer_class = WorkflowSerializer

    @action(detail=True, methods=["get"])
    def stats(self, request, pk):
        workflow = self.get_object()
        results = WorkflowService.get_workflow_stats(workflow)
        serializer = WorkflowStatsSerializer(data=results)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk):
        data = request.data
        workflow = self.get_object()
        serializer = WorkflowInstanceSerializer(
            data={"initial_data": data["initial_data"], "workflow": workflow.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        service = WorkflowService()
        service.start_workflow(serializer.instance)
        return Response(serializer.data)


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    queryset = WorkflowTaskInstance.objects.all().order_by("-created_at")
    serializer_class = WorkflowInstanceSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)
        service = WorkflowService()
        service.start_workflow(serializer.instance)


class WorkflowTaskInstanceViewSet(viewsets.ModelViewSet):
    queryset = WorkflowTaskInstance.objects.all().order_by("-created_at")
    serializer_class = WorkflowTaskInstanceSerializer
    filterset_fields = ["state", "workflow_name", "task_spec", "workflow_instance_id"]


class ServiceTaskViewSet(
    viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.ListModelMixin
):
    queryset = ServiceTask.objects.all().order_by("-created_at")
    serializer_class = ServiceTaskSerializer

    def update_state(self, state, data):
        service_task = self.get_object()
        if service_task.state == state:
            return ValidationError({"error": "error"})
        service_task.state = state
        service_task.output_data = data.get("output_data", {})
        service_task.save()
        # run_workflow.apply_async(
        #     args=[str(service_task.workflow_instance.id)], queue="run_workflow"
        # )
        run_workflow(str(service_task.workflow_instance.id))
        return service_task

    @action(detail=True, methods=["patch"])
    def complete(self, request, *args, **kwargs):
        service_task = self.update_state(ServiceTaskState.COMPLETED, request.data)
        return Response(ServiceTaskSerializer(instance=service_task).data)

    @action(detail=True, methods=["patch"])
    def failure(self, request, *args, **kwargs):
        service_task = self.update_state(ServiceTaskState.FAILURE, request.data)
        return Response(ServiceTaskSerializer(instance=service_task).data)


class MessageTaskEventViewSet(
    viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.ListModelMixin
):
    queryset = MessageTaskEvent.objects.all().order_by("-created_at")
    serializer_class = MessageTaskEventSerializer
