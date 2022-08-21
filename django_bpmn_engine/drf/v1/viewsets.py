import logging

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from django_bpmn_engine.core.models import Workflow
from django_bpmn_engine.drf.v1.serializers import WorkflowSerializer

logger = logging.getLogger(__name__)


class BaseSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 50


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().order_by("-created_at")
    serializer_class = WorkflowSerializer
