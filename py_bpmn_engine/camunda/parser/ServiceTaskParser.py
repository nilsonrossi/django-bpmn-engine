from py_bpmn_engine.bpmn.parser.TaskParser import TaskParser
from py_bpmn_engine.bpmn.parser.ValidationException import ValidationException
from py_bpmn_engine.bpmn.parser.util import xpath_eval

CAMUNDA_MODEL_NS = 'http://camunda.org/schema/1.0/bpmn'


class ServiceTaskParser(TaskParser):
    def __init__(self, process_parser, spec_class, node, lane=None):
        super(ServiceTaskParser, self).__init__(process_parser, spec_class, node, lane)
        self.xpath = xpath_eval(node, extra_ns={'camunda': CAMUNDA_MODEL_NS})

    def create_task(self):
        _type = self.node.attrib['{' + CAMUNDA_MODEL_NS + '}type']
        if _type != 'external':
            raise ValidationException("Only 'external' type is accepted in Service Task")
        topic = self.node.attrib['{' + CAMUNDA_MODEL_NS + '}topic']
        properties = {}
        for xml_field in self.xpath('.//camunda:properties/camunda:property'):
            properties[xml_field.get("name")] = xml_field.get("value")
        return self.spec_class(self.spec, self.get_task_spec_name(), topic, properties,
                               lane=self.lane,
                               position=self.position,
                               description=self.node.get('name', None))
