from django.contrib import admin
from django.db.models import ForeignKey
from django.db.models.fields.related import OneToOneField
from django_bpmn_engine.core.models import Workflow


class ModelAdminMixin(admin.ModelAdmin):
    ordering = ["created_at"]

    def __init__(self, model, admin_site):
        self.readonly_fields = ("created_at", "updated_at", "deleted_at") + tuple(self.readonly_fields)
        self.readonly_fields = tuple(set(self.readonly_fields))

        if self.list_display and self.list_display[0] == "__str__":
            self.list_display = [field.name for field in model._meta.fields]

        if not self.list_filter:
            self.list_filter = ["created_at", "updated_at"]

        if not self.raw_id_fields:
            # Only for FOREIGN KEY fields
            raw_id_fields = []

            for key, value in model._meta._forward_fields_map.items():
                if type(value) in [ForeignKey, OneToOneField] and not key.endswith("id"):
                    raw_id_fields.append(key)

            if raw_id_fields:
                self.raw_id_fields = raw_id_fields

        super(ModelAdminMixin, self).__init__(model, admin_site)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    search_fields = ["name", "workflow_process_id"]
    list_display = ["created_at", "updated_at", "name", "workflow_process_id"]

