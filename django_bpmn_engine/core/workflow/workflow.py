from SpiffWorkflow.bpmn.specs.events.event_definitions import ErrorEventDefinition
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow


class CustomWorkflow(BpmnWorkflow):
    def catch_error(self, error_name: str, error_code: str):
        event_definition = ErrorEventDefinition(error_name, error_code)
        self.catch(event_definition)
