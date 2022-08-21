from rest_framework.routers import DefaultRouter

from django_bpmn_engine.drf.v1.viewsets import WorkflowViewSet

router = DefaultRouter()
router.register("workflow", WorkflowViewSet, "workflow-v1")