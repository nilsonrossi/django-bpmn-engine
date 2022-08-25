from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import ForeignKey
from django.db.models.fields.related import OneToOneField

from django_bpmn_engine.core.models import Incident
from django_bpmn_engine.core.models import MessageTaskEvent
from django_bpmn_engine.core.models import MessageTaskEventState
from django_bpmn_engine.core.models import ServiceTask
from django_bpmn_engine.core.models import ServiceTaskState
from django_bpmn_engine.core.models import UserTask
from django_bpmn_engine.core.models import UserTaskState
from django_bpmn_engine.core.models import Workflow
from django_bpmn_engine.core.models import WorkflowInstance
from django_bpmn_engine.core.models import WorkflowState
from django_bpmn_engine.core.models import WorkflowTaskInstance
from django_bpmn_engine.core.workflow.service import WorkflowService
from django_bpmn_engine.core.workflow.service import run_workflow
from django_bpmn_engine.core.utils import convert_form_dict_to_json_schema


class ModelAdminMixin(admin.ModelAdmin):
    ordering = ["created_at"]

    def __init__(self, model, admin_site):
        self.readonly_fields = ("created_at", "updated_at") + tuple(
            self.readonly_fields
        )
        self.readonly_fields = tuple(set(self.readonly_fields))

        if self.list_display and self.list_display[0] == "__str__":
            self.list_display = [field.name for field in model._meta.fields]

        if not self.list_filter:
            self.list_filter = ["created_at", "updated_at"]

        if not self.raw_id_fields:
            # Only for FOREIGN KEY fields
            raw_id_fields = []

            for key, value in model._meta._forward_fields_map.items():
                if type(value) in [ForeignKey, OneToOneField] and not key.endswith(
                    "id"
                ):
                    raw_id_fields.append(key)

            if raw_id_fields:
                self.raw_id_fields = raw_id_fields

        super(ModelAdminMixin, self).__init__(model, admin_site)


@admin.register(Workflow)
class WorkflowAdmin(ModelAdminMixin):
    search_fields = ["name", "workflow_process_id"]
    list_display = ["created_at", "updated_at", "name", "workflow_process_id"]
    readonly_fields = ("version",)

    def save_model(self, request, obj, form, change) -> None:
        with transaction.atomic():
            service = WorkflowService()

            # Validate the workflow
            service.parse_workflow(obj.xml, obj.workflow_process_id)

            workflow = super().save_model(request, obj, form, change)
            return workflow


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(ModelAdminMixin):
    exclude = ("success",)
    search_fields = ["workflow__workflow_process_id", "workflow__name"]
    list_display = ["created_at", "updated_at", "workflow", "state", "last_task"]
    list_filter = ["created_at", "updated_at", "state"]
    readonly_fields = ("state", "last_task")

    def save_model(self, request, obj, form, change) -> None:
        service = WorkflowService()
        service.start_workflow(obj)


@admin.register(WorkflowTaskInstance)
class WorkflowTaskInstanceAdmin(ModelAdminMixin):
    search_fields = [
        "workflow_instance__workflow__workflow_process_id",
        "workflow_instance__workflow__name",
        "workflow_instance__id",
    ]
    list_display = ["created_at", "updated_at", "workflow", "state", "task_spec"]
    list_filter = ["created_at", "updated_at", "state"]

    @admin.display(description="Workflow", ordering="workflow_instance__workflow__name")
    def workflow(self, obj):
        return f"{obj.workflow_instance.workflow.name} ({obj.workflow_instance.workflow.workflow_process_id})"

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ServiceTask)
class ServiceTaskAdmin(ModelAdminMixin):
    list_display = ["created_at", "updated_at", "task_name", "queue_name", "state"]
    list_filter = ["created_at", "updated_at", "state"]

    def save_model(self, request, obj, form, change) -> None:
        obj.save()
        if obj.state in [
            ServiceTaskState.COMPLETED,
            ServiceTaskState.FAILURE,
        ]:
            run_workflow.apply_async(
                args=[str(obj.workflow_instance.id)], queue="run_workflow"
            )
            # run_workflow(str(obj.workflow_instance.id))


@admin.register(MessageTaskEvent)
class MessageTaskEventAdmin(ModelAdminMixin):
    list_display = ["created_at", "updated_at", "task_name", "message_name", "state"]
    list_filter = ["created_at", "updated_at", "state"]

    def save_model(self, request, obj, form, change) -> None:
        obj.save()
        if obj.state == MessageTaskEventState.RECEIVED:
            run_workflow.apply_async(
                args=[str(obj.workflow_instance.id)], queue="run_workflow"
            )
            # run_workflow(str(obj.workflow_instance.id))


@admin.register(Incident)
class IncidentAdmin(ModelAdminMixin):
    list_display = ["created_at", "updated_at", "task_name", "resolved"]
    list_filter = ["created_at", "updated_at", "task_name"]

    def save_model(self, request, obj, form, change) -> None:
        obj.save()
        if obj.resolved:
            obj.workflow_instance.state = WorkflowState.RUNNING
            obj.workflow_instance.save()
            run_workflow.s(
                str(obj.workflow_instance.id), extra_data=obj.input
            ).apply_async(queue="run_workflow")
            # run_workflow(str(obj.workflow_instance.id))


class UserTaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # manually set the current instance on the widget
        self.fields['form_fields'].widget.instance = self.instance


@admin.register(UserTask)
class UserTaskAdmin(ModelAdminMixin):
    form = UserTaskForm
    list_display = ["created_at", "updated_at", "task_name", "user", "state"]
    list_filter = ["created_at", "updated_at", "state"]

    def save_model(self, request, obj, form, change) -> None:
        obj.user = request.user
        obj.save()

        if obj.state == UserTaskState.COMPLETED:
            # run_workflow.apply_async(
            #     args=[str(obj.workflow_instance.id)], queue="run_workflow"
            # )
            run_workflow(str(obj.workflow_instance.id))
