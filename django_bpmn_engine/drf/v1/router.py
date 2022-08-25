from rest_framework.routers import DefaultRouter

from django_bpmn_engine.drf.v1.viewsets import MessageTaskEventViewSet
from django_bpmn_engine.drf.v1.viewsets import ServiceTaskViewSet
from django_bpmn_engine.drf.v1.viewsets import WorkflowInstanceViewSet
from django_bpmn_engine.drf.v1.viewsets import WorkflowTaskInstanceViewSet
from django_bpmn_engine.drf.v1.viewsets import WorkflowViewSet

router = DefaultRouter()
router.register("workflow", WorkflowViewSet, "workflow-v1")
router.register("workflowinstance", WorkflowInstanceViewSet, "workflowinstance-v1")
router.register(
    "workflowtaskinstance", WorkflowTaskInstanceViewSet, "workflowtaskinstance-v1"
)
router.register("service_task", ServiceTaskViewSet, "service-task-v1")
router.register("message_task", MessageTaskEventViewSet, "message-task-v1")
