import uuid
from django.db import models


class WorkflowState(models.TextChoices):
    RUNNING = "RUNNING", "Running"
    COMPLETED = "COMPLETED", "Completed"
    CANCELED = "CANCELED", "Canceled"


class BaseModelMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Workflow(BaseModelMixin):
    xml = models.TextField()
    workflow_process_id = models.CharField(max_length=100)
    version = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"


class WorkflowInstance(BaseModelMixin):
    workflow_id = models.ForeignKey(Workflow, related_name="instances", on_delete=models.CASCADE)
    instance_id = models.CharField(max_length=100)
    state = models.CharField(max_length=20, choices=WorkflowState.choices, default=WorkflowState.RUNNING, verbose_name="State")

    class Meta:
        verbose_name = "WorkflowInstance"
        verbose_name_plural = "WorkflowInstances"
