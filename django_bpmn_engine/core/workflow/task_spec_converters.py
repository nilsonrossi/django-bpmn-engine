from SpiffWorkflow.bpmn.serializer.bpmn_converters import BpmnTaskSpecConverter

from django_bpmn_engine.core.workflow.task_specs import ServiceTask


class ServiceTaskConverter(BpmnTaskSpecConverter):
    def __init__(self, data_converter=None, typename=None):
        super().__init__(ServiceTask, data_converter, typename)

    def to_dict(self, spec):
        dct = self.get_default_attributes(spec)
        dct.update(self.get_bpmn_attributes(spec))
        dct["topic"] = spec.topic
        dct["properties"] = spec.extensions
        return dct

    def from_dict(self, dct):
        return self.task_spec_from_dict(dct)
