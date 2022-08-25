import json
import logging
import re
import time

from collections import defaultdict
from functools import partial
from typing import Any
from typing import Dict
from typing import List

from celery import shared_task
from django.db import transaction
from django.db.models import Count
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask
from SpiffWorkflow.bpmn.specs.events.event_definitions import CycleTimerEventDefinition
from SpiffWorkflow.bpmn.specs.events.event_definitions import MessageEventDefinition
from SpiffWorkflow.bpmn.specs.events.event_definitions import TimerEventDefinition
from SpiffWorkflow.bpmn.specs.events.event_types import CatchingEvent
from SpiffWorkflow.camunda.serializer.task_spec_converters import UserTaskConverter
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.dmn.serializer.task_spec_converters import BusinessRuleTaskConverter
from SpiffWorkflow.exceptions import WorkflowException
from SpiffWorkflow.task import Task
from SpiffWorkflow.task import TaskState
from SpiffWorkflow.util.deep_merge import DeepMerge

from django_bpmn_engine.core.models import Incident
from django_bpmn_engine.core.models import MessageTaskEvent
from django_bpmn_engine.core.models import MessageTaskEventState
from django_bpmn_engine.core.models import ServiceTask as ServiceTaskModel
from django_bpmn_engine.core.models import ServiceTaskState
from django_bpmn_engine.core.models import UserTask as UserTaskModel
from django_bpmn_engine.core.models import UserTaskState
from django_bpmn_engine.core.models import Workflow
from django_bpmn_engine.core.models import WorkflowInstance
from django_bpmn_engine.core.models import WorkflowState
from django_bpmn_engine.core.models import WorkflowTaskInstance
from django_bpmn_engine.core.workflow.parser import CustomParser
from django_bpmn_engine.core.workflow.serializer import CustomSerializer
from django_bpmn_engine.core.workflow.task_spec_converters import ServiceTaskConverter
from django_bpmn_engine.core.workflow.task_specs import ServiceTask
from django_bpmn_engine.core.workflow.workflow import CustomWorkflow

logger = logging.getLogger(__name__)


class WorkflowService:

    def __init__(self):
        wf_spec_converter = CustomSerializer.configure_workflow_spec_converter([
            UserTaskConverter,
            BusinessRuleTaskConverter,
            ServiceTaskConverter
        ])
        self.serializer = CustomSerializer(wf_spec_converter)
        self.workflow_spec = None

    @staticmethod
    def get_workflow_stats(workflow: Workflow):
        queryset = WorkflowTaskInstance.objects.filter(workflow_instance__workflow=workflow).filter(
            state__in=[TaskState.COMPLETED, TaskState.READY, TaskState.WAITING]
        )
        instance_tasks = queryset.values("task_spec", "state").annotate(count_state=Count("state"))
        stats: Dict[str, Any] = defaultdict(dict)
        for stat in instance_tasks:
            stats[stat["task_spec"]][stat["state"]] = stat["count_state"]
        return {"workflow_name": workflow.name, "stats": stats}

    def parse_workflow(self, bpmn_xml: str, workflow_process_id: str):
        parser = CustomParser()
        parser.add_bpmn_from_str(bpmn_xml)
        try:
            self.workflow_spec = CustomWorkflow(
                parser.get_spec(workflow_process_id),
                subprocess_specs=parser.get_subprocess_specs(workflow_process_id)
            )
        except Exception as e:
            raise e

    def _update_task_instance(self, task_instance: WorkflowTaskInstance, task_dict: Dict[str, Any]):
        task_instance.last_state_change = task_dict["last_state_change"]
        task_instance.children = task_dict["children"]
        task_instance.state = task_dict["state"]
        task_instance.triggered = task_dict["triggered"]
        task_instance.internal_data = task_dict["internal_data"]
        task_instance.data = task_dict["data"]
        task_instance.last_state_change = task_dict["last_state_change"]
        task_instance.save()

    def create_workflow_instance_tasks(self, workflow_instance: WorkflowInstance, workflow_dct: Dict[str, Any]):
        create_instances: List[WorkflowInstance] = []

        # Get all task instances saved in database for update
        task_instances = WorkflowTaskInstance.objects.select_for_update().filter(
            workflow_instance=workflow_instance
        )
        map_task_instance_ids = {str(task_instance.id): task_instance for task_instance in task_instances}

        # Cria ou atualiza uma task no banco de dados
        for task in workflow_dct["tasks"].values():
            if task["id"] not in map_task_instance_ids.keys():
                create_instances.append(WorkflowTaskInstance(workflow_instance=workflow_instance, **task))
            elif map_task_instance_ids[task["id"]].state != task["state"]:
                self._update_task_instance(map_task_instance_ids[task["id"]], task)
    
        # Verifica se alguma task foi removida do workflow_dct e deleta também do banco de dados
        if diff_tasks:=list(set(map_task_instance_ids.keys()) - set(workflow_dct["tasks"].keys())):
            WorkflowTaskInstance.objects.filter(id__in=diff_tasks).delete()

        # Verifica se o workflow tem subprocessos, cria uma nova instancia e cria/atualiza as tasks
        for key, subprocess in workflow_dct["subprocesses"].items():
            task_instances = WorkflowTaskInstance.objects.select_for_update().filter(
                workflow_instance=key
            )
            map_task_instance_ids = {str(task_instance.id): task_instance for task_instance in task_instances}
            suboprocess_instance, _ = WorkflowInstance.objects.update_or_create(
                id=key,
                workflow_id=workflow_instance.workflow_id,
                parent=workflow_instance,
                defaults={
                    "root": subprocess["root"],
                    "last_task": subprocess["last_task"],
                    "success": subprocess["success"],
                }
            )
            for task in subprocess["tasks"].values():
                if task["id"] not in map_task_instance_ids.keys():
                    create_instances.append(WorkflowTaskInstance(workflow_instance=suboprocess_instance, **task))
                elif map_task_instance_ids[task["id"]].state != task["state"]:
                    self._update_task_instance(map_task_instance_ids[task["id"]], task)

            if diff_tasks:=list(set(map_task_instance_ids.keys()) - set(subprocess["tasks"].keys())):
                WorkflowTaskInstance.objects.filter(id__in=diff_tasks).delete()

        if create_instances:
            WorkflowTaskInstance.objects.bulk_create(create_instances)

    def start_workflow(self, wf_instance_obj) -> Workflow:
        #Carrega do workflow
        workflow_obj = wf_instance_obj.workflow
        
        # Faz o parse do workflow
        self.parse_workflow(bpmn_xml=workflow_obj.xml, workflow_process_id=workflow_obj.workflow_process_id)

        # Setando o payload inicial no node Start
        self.workflow_spec.task_tree.children[0].set_data(
            **self.serializer.data_converter.restore(wf_instance_obj.initial_data)
        )

        # Convertendo para dict
        workflow_dct = self.serializer.workflow_to_dict(self.workflow_spec)
        wf_instance_obj.root = workflow_dct["root"]
        wf_instance_obj.success = workflow_dct["success"]

        # Salva a instancia e as tasks
        with transaction.atomic():
            wf_instance_obj.save()
            self.create_workflow_instance_tasks(wf_instance_obj, workflow_dct)
        
        # Joga para a fila de execução
        # run_workflow.apply_async(args=[str(wf_instance_obj.id)], queue="run_workflow")
        run_workflow(str(wf_instance_obj.id))

        return wf_instance_obj

    def _get_tasks(self) -> List[Task]:
        ready_tasks = self.workflow_spec.get_tasks(TaskState.READY)
        waiting_tasks = self.workflow_spec.get_tasks(TaskState.WAITING)
        return ready_tasks + waiting_tasks

    def run_steps(self, workflow_instance: WorkflowInstance):
        # pega todas as tasks READY e WAITING
        tasks = self._get_tasks()
        while tasks:
            # Lista usada para saber se devemos continuar no while para executar tasks
            task_states = []
            for task in tasks:
                # execute engine steps
                if task._has_state(TaskState.READY) and self.workflow_spec._is_engine_task(task.task_spec):
                    task.complete()
                    task_states.append(True)
                elif task._has_state(TaskState.READY) and not self.workflow_spec._is_engine_task(task.task_spec):
                    self._execute_task(workflow_instance, task)
                    task_states.append(task.state == TaskState.COMPLETED) 
                        
                elif task._has_state(TaskState.WAITING):
                    task.task_spec._update(task)
                    self._execute_catching_event_task(workflow_instance, task)
                    task_states.append(task.state in [TaskState.COMPLETED, TaskState.READY])
  
            if any(task_states):
                tasks = self._get_tasks()
            else:
                tasks = []

    def _get_tasks_from_workflow_instance(self, workflow_instance: WorkflowInstance):
        return {
            str(task.id): {
                "id": str(task.id),
                "parent": task.parent,
                "children": task.children,
                "last_state_change": time.mktime(task.last_state_change.timetuple()),
                "state": task.state,
                "task_spec": task.task_spec,
                "triggered": task.triggered,
                "workflow_name": task.workflow_name,
                "internal_data": task.internal_data,
                "data": task.data
            }
            for task in WorkflowTaskInstance.objects.filter(workflow_instance=workflow_instance).iterator()
        }

    def _build_workflow_tree(self, workflow_instance: WorkflowInstance):
        process_dct = {
            "last_task": workflow_instance.last_task,
            "success": workflow_instance.success,
            "tasks": self._get_tasks_from_workflow_instance(workflow_instance),
            "subprocesses": {},
        }

        for subprocess in WorkflowInstance.objects.filter(parent=workflow_instance):
            process_dct["subprocesses"].update({
                str(subprocess.id): {
                    "data": {},
                    "last_task": subprocess.last_task,
                    "success": subprocess.success,
                    "tasks": self._get_tasks_from_workflow_instance(subprocess),
                    "root": str(subprocess.root),
                }
            })
        self.workflow_spec.task_tree = self.serializer.task_tree_from_dict(
            process_dct=process_dct,
            task_id=str(workflow_instance.root),
            parent_task=None,
            process=self.workflow_spec,
        )

    def build_workflow(self, workflow_instance: WorkflowInstance):
        workflow_obj = workflow_instance.workflow
        self.parse_workflow(
            bpmn_xml=workflow_obj.xml, workflow_process_id=workflow_obj.workflow_process_id
        )
        # Build the tasks states from last execution
        self._build_workflow_tree(workflow_instance)

    def _execute_task(self, workflow_instance: WorkflowInstance, task: Task):
        input_data = DeepMerge.merge(task.data, self.workflow_spec.data)
        if isinstance(task.task_spec, ServiceTask):

            # Ativa o service task (cria evento no model=ServiceTask)
            # Caso o evento já tenha sido criado, verifica se foi processado
            service_task = self._get_or_create_service_task(workflow_instance, task, input_data)

            if service_task.state == ServiceTaskState.COMPLETED:
                task.update_data(service_task.output_data)
                task.complete()
            elif service_task.state == ServiceTaskState.FAILURE:
                self.workflow_spec.catch_error(**service_task.output_data)
                if not task._has_state(TaskState.CANCELLED):
                    self.create_incident(workflow_instance, task, service_task.output_data)

        elif isinstance(task.task_spec, UserTask):
            user_task = self._get_or_create_user_task(workflow_instance, task, input_data)

            if user_task.state == UserTaskState.COMPLETED:
                for field in task.task_spec.form.fields:
                    if output:= user_task.form_fields.get(field.id):
                        task.update_data_var(field.id, output)
                task.complete()                

    def _execute_catching_event_task(self, workflow_instance: WorkflowInstance, task: Task):
        if isinstance(task.task_spec, CatchingEvent) and not task._has_state(TaskState.READY):
            if isinstance(task.task_spec.event_definition, MessageEventDefinition):
                input_data = DeepMerge.merge(task.data, self.workflow_spec.data)
                defaults = {
                    "input_data": input_data,
                    "message_name": task.task_spec.event_definition.name
                }
                message, _ = MessageTaskEvent.objects.get_or_create(
                    task_name=task.get_name(),
                    workflow_instance=workflow_instance,
                    defaults=defaults
                )
                if message.state == MessageTaskEventState.RECEIVED:
                    self.workflow_spec.catch_bpmn_message(message.message_name, message.output_data)
                
            elif isinstance(task.task_spec.event_definition, TimerEventDefinition):
                duration = task.task_spec.event_definition.dateTime
                match = re.match("timedelta\((.*)=(\d+)\)", duration)
                period, every = match.groups()  # type: ignore
                self._get_or_create_periodic_task(
                    workflow_instance_id=workflow_instance.id,
                    name=self._get_task_identification(task),
                    period=period,
                    every=every,
                )

            elif isinstance(task.task_spec.event_definition, CycleTimerEventDefinition):
                # TODO: criar o objeto Periodic Task with crontab
                pass

    def _get_task_identification(self, task: Task):
        return f"{task.workflow.spec.name}:{task.get_name()}"

    def _get_or_create_user_task(self, workflow_instance: WorkflowInstance, task: Task, input_data: Dict[str, Any]):
        task_identification = self._get_task_identification(task)
        try:
            return UserTaskModel.objects.get(
                task_name=task_identification, workflow_instance=workflow_instance
            )
        except UserTaskModel.DoesNotExist:
            return UserTaskModel.objects.create(
                task_name=task_identification,
                workflow_instance=workflow_instance,
                input_data=input_data,
                properties=task.task_spec.extensions,
                form_fields=UserTaskConverter().form_to_dict(task.task_spec.form),
            )
    
    def _get_or_create_service_task(self, workflow_instance: WorkflowInstance, task: Task, input_data: Dict[str, Any]):
        task_identification = self._get_task_identification(task)
        try:
            return ServiceTaskModel.objects.get(
                task_name=task_identification, workflow_instance=workflow_instance
            )
        except ServiceTaskModel.DoesNotExist:
            return ServiceTaskModel.objects.create(
                task_name=task_identification,
                workflow_instance=workflow_instance,
                input_data=input_data,
                properties=task.task_spec.extensions,
                queue_name=task.task_spec.topic,
            )

    def _get_or_create_periodic_task(self, workflow_instance_id, name, period, every):
        try:
            PeriodicTask.objects.get(name=name)
        except PeriodicTask.DoesNotExist:
            interval, _ = IntervalSchedule.objects.get_or_create(period=period, every=every)
            PeriodicTask.objects.create(
                interval=interval,
                name=name,
                task="django_bpmn_engine.core.workflow.service.run_workflow",
                queue="run_workflow",
                args=json.dumps([str(workflow_instance_id)]),
                one_off=True
            )

    def create_incident(self, workflow_instance: WorkflowInstance, task_name: str, error_data: Dict[str, Any]):
        workflow_instance.state = WorkflowState.FAILURE
        workflow_instance.save()
        Incident.objects.get_or_create(
            workflow_instance=workflow_instance,
            task_name=task_name,
            defaults={"error": error_data}
        )

    def send_service_tasks(self, workflow_instance: WorkflowInstance):
        service_tasks = ServiceTaskModel.objects.filter(
            workflow_instance=workflow_instance,
            state=ServiceTaskState.NEW
        )
        for service_task in service_tasks.iterator():
            run_service_task.apply_async(
                args=[
                    str(workflow_instance.id),
                    str(service_task.id),
                    service_task.input_data,
                    service_task.properties
                ],
                queue=service_task.queue_name
            )
            service_task.state = ServiceTaskState.ACTIVATED
            service_task.save()


@shared_task
def run_workflow(workflow_instance_id: str, extra_data=None):
    try:
        service_instance = WorkflowService()
        workflow_instance: WorkflowInstance = WorkflowInstance.objects.select_related("workflow").get(
            id=workflow_instance_id
        )
        with transaction.atomic():
            # Build the workflow spec
            service_instance.build_workflow(workflow_instance)
            workflow_spec = service_instance.workflow_spec

            if extra_data:
                workflow_spec.set_data(**extra_data)

            service_instance.run_steps(workflow_instance)

            workflow_dct = service_instance.serializer.workflow_to_dict(workflow_spec)
            service_instance.create_workflow_instance_tasks(workflow_instance, workflow_dct)
            
            if workflow_spec.is_completed():
                workflow_instance.state = WorkflowState.COMPLETED
                WorkflowInstance.objects.filter(parent=workflow_instance).update(
                    state=WorkflowState.COMPLETED
                )
            
            # Update the last task executed
            workflow_instance.last_task = (
                workflow_spec.last_task.task_spec.name if workflow_spec.last_task else None
            )
            workflow_instance.save()
            transaction.on_commit(partial(service_instance.send_service_tasks, workflow_instance))

    except WorkflowException as e:
        service_instance.create_incident(workflow_instance, e.sender.name, {"error": str(e)})
        logger.error(f"Error on task {e.sender.name}: {str(e)}")

@shared_task(name="run_service_task")
def run_service_task(*args, **kwargs):
    pass
