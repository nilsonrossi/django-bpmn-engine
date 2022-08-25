import logging

from time import sleep

from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.db import transaction

from django_bpmn_engine.core.models import WorkflowInstance
from django_bpmn_engine.core.models import WorkflowState
from django_bpmn_engine.core.workflow.service import WorkflowService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run instances workflow"
    running = True
    count = 0

    def handle(self, *args, **options):
        try:
            self._execute_workflows()
        except KeyboardInterrupt:
            self._exit()

    def _waiting(self, msg):
        self.stdout.write(f"{msg}{'.' * self.count}\nQuit with CONTROL-C")
        self.count += 1 if self.count < 3 else -3
        sleep(1)
        # os.system("clear")

    def _execute_workflows(self):
        service = WorkflowService()
        while self.running:
            workflow_instances: WorkflowInstance = (
                WorkflowInstance.objects.select_related("workflow")
                .select_for_update()
                .filter(state=WorkflowState.RUNNING, parent__isnull=True)
            )
            try:
                with transaction.atomic():
                    for workflow_instance in workflow_instances.iterator():
                        # Build the workflow spec
                        service.build_workflow(workflow_instance)
                        workflow_spec = service.workflow_spec

                        # Process the workflow

                        # workflow_spec.do_engine_steps()
                        # service.execute_ready_tasks(workflow_instance)
                        # service.execute_message_tasks(workflow_instance)
                        # workflow_spec.do_engine_steps()
                        # workflow_spec.refresh_waiting_tasks()
                        service.run_steps(workflow_instance)

                        workflow_dct = service.serializer.workflow_to_dict(
                            workflow_spec
                        )
                        service.create_workflow_instance_tasks(
                            workflow_instance, workflow_dct
                        )

                        # Need to check if workflow is complete again because of
                        # `do_engine_steps` and `refresh_waiting_tasks` can complete the workflow
                        if workflow_spec.is_completed():
                            workflow_instance.state = WorkflowState.COMPLETED
                            WorkflowInstance.objects.filter(
                                parent=workflow_instance
                            ).update(state=WorkflowState.COMPLETED)

                        # Update the last task executed
                        workflow_instance.last_task = (
                            workflow_spec.last_task.task_spec.name
                            if workflow_spec.last_task
                            else None
                        )
                        workflow_instance.save()
            except DatabaseError:
                self._waiting("Starting publisher 🤔")
            else:
                self._waiting("Waiting for messages to be published 😋")
