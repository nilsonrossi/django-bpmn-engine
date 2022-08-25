from lxml import etree
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnParser
from SpiffWorkflow.bpmn.parser.BpmnParser import full_tag
from SpiffWorkflow.camunda.specs.UserTask import UserTask

from django_bpmn_engine.core.models import Workflow
from django_bpmn_engine.core.workflow.task_parser import MyUserTaskParser
from django_bpmn_engine.core.workflow.task_parser import ServiceTaskParser
from django_bpmn_engine.core.workflow.task_specs import ServiceTask


class CustomParser(BpmnParser):
    OVERRIDE_PARSER_CLASSES = {
        full_tag("serviceTask"): (ServiceTaskParser, ServiceTask),
        full_tag('userTask'): (MyUserTaskParser, UserTask),
    }

    def get_process_parser(self, process_id_or_name):
        if process_id_or_name in self.process_parsers_by_name:
            return self.process_parsers_by_name[process_id_or_name]
        elif process_id_or_name in self.process_parsers:
            return self.process_parsers[process_id_or_name]

        workflow = Workflow.objects.filter(
            workflow_process_id=process_id_or_name
        ).first()
        if workflow:
            self.add_bpmn_from_str(workflow.xml)
            return self.get_process_parser(process_id_or_name)

    def add_bpmn_from_str(self, xml_str: str):
        """
        Add bpmn xml string to the parser's set.
        """
        self.add_bpmn_xml(etree.fromstring(xml_str.encode()))
