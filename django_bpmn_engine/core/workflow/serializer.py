from datetime import datetime

from django.utils.timezone import make_aware
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer


class CustomSerializer(BpmnWorkflowSerializer):
    def task_to_dict(self, task):
        last_state_change = datetime.fromtimestamp(
            task.last_state_change
        )  # .strftime("%Y-%m-%d %H:%M:%S")
        task.last_state_change = make_aware(last_state_change)
        return super().task_to_dict(task)
