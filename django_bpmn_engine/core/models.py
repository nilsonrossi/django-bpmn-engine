import uuid

from django.db import models
from django_jsonform.models.fields import JSONField
from SpiffWorkflow.task import TaskStateNames

from django_bpmn_engine.core.utils import convert_form_dict_to_json_schema


class WorkflowState(models.TextChoices):
    RUNNING = "RUNNING", "RUNNING"
    COMPLETED = "COMPLETED", "COMPLETED"
    CANCELED = "CANCELED", "CANCELED"
    FAILURE = "FAILURE", "FAILURE"


class ServiceTaskState(models.TextChoices):
    NEW = "NEW", "NEW"
    ACTIVATED = "ACTIVATED", "ACTIVATED"
    FAILURE = "FAILURE", "FAILURE"
    COMPLETED = "COMPLETED", "COMPLETED"


class UserTaskState(models.TextChoices):
    NEW = "NEW", "NEW"
    ASSIGNED = "ASSIGNED", "ASSIGNED"
    COMPLETED = "COMPLETED", "COMPLETED"


class MessageTaskEventState(models.TextChoices):
    WAITING = "WAITING", "WAITING"
    RECEIVED = "RECEIVED", "RECEIVED"


TaskStateChoices = [(key, value) for key, value in TaskStateNames.items()]


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.workflow_process_id})"


class WorkflowInstance(BaseModelMixin):
    workflow = models.ForeignKey(
        Workflow, related_name="instances", on_delete=models.CASCADE
    )
    state = models.CharField(
        max_length=20,
        choices=WorkflowState.choices,
        default=WorkflowState.RUNNING,
        verbose_name="State",
        db_index=True,
    )
    last_task = models.CharField(max_length=100, null=True, blank=True)
    initial_data = models.JSONField(default=dict, null=True, blank=True)
    root = models.UUIDField(null=True, blank=True)
    success = models.BooleanField(default=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "WorkflowInstance"
        verbose_name_plural = "WorkflowInstances"


class WorkflowTaskInstance(BaseModelMixin):
    workflow_instance = models.ForeignKey(
        WorkflowInstance, related_name="tasks", on_delete=models.CASCADE
    )
    parent = models.UUIDField(blank=True, null=True)
    children = models.JSONField(default=list)
    last_state_change = models.DateTimeField()
    state = models.PositiveSmallIntegerField(choices=TaskStateChoices)
    task_spec = models.CharField(max_length=50)
    triggered = models.BooleanField()
    workflow_name = models.CharField(max_length=50)
    internal_data = models.JSONField(default=dict)
    data = models.JSONField(default=dict)

    class Meta:
        verbose_name = "WorkflowTaskInstance"
        verbose_name_plural = "WorkflowTaskInstances"


class ServiceTask(BaseModelMixin):
    task_name = models.CharField(max_length=50)
    workflow_instance = models.ForeignKey(
        WorkflowInstance, related_name="service_tasks", on_delete=models.CASCADE
    )
    input_data = models.JSONField(default=dict, null=True, blank=True)
    output_data = models.JSONField(default=dict, null=True, blank=True)
    queue_name = models.CharField(max_length=50)
    properties = models.JSONField(default=dict, null=True, blank=True)
    state = models.CharField(
        max_length=20,
        choices=ServiceTaskState.choices,
        default=ServiceTaskState.NEW,
    )

    class Meta:
        verbose_name = "ServiceTask"
        verbose_name_plural = "ServiceTasks"


class UserTask(BaseModelMixin):
    task_name = models.CharField(max_length=50)
    workflow_instance = models.ForeignKey(
        WorkflowInstance, related_name="user_tasks", on_delete=models.CASCADE
    )
    input_data = models.JSONField(default=dict, null=True, blank=True)
    form_fields = JSONField(schema=convert_form_dict_to_json_schema, blank=True, null=True)
    properties = models.JSONField(default=dict, null=True, blank=True)
    state = models.CharField(
        max_length=20,
        choices=UserTaskState.choices,
        default=UserTaskState.NEW,
    )
    user = models.ForeignKey('auth.User', on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        verbose_name = "UserTask"
        verbose_name_plural = "UserTasks"


class MessageTaskEvent(BaseModelMixin):
    task_name = models.CharField(max_length=50)
    workflow_instance = models.ForeignKey(
        WorkflowInstance, related_name="message_tasks", on_delete=models.CASCADE
    )
    input_data = models.JSONField(default=dict, null=True, blank=True)
    output_data = models.JSONField(default=dict, null=True, blank=True)
    message_name = models.CharField(max_length=100)
    state = models.CharField(
        max_length=20,
        choices=MessageTaskEventState.choices,
        default=MessageTaskEventState.WAITING,
    )

    class Meta:
        verbose_name = "MessageTaskEvent"
        verbose_name_plural = "MessageTaskEvents"


class Incident(BaseModelMixin):
    workflow_instance = models.ForeignKey(
        WorkflowInstance, related_name="incidents", on_delete=models.CASCADE
    )
    task_name = models.CharField(max_length=50)
    error = models.JSONField()
    resolved = models.BooleanField(default=False)
    input = models.JSONField(default=dict, null=True, blank=True)

    class Meta:
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
