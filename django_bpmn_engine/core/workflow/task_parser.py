from SpiffWorkflow.bpmn.parser.TaskParser import TaskParser
from SpiffWorkflow.bpmn.parser.util import xpath_eval
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException
from SpiffWorkflow.camunda.parser.UserTaskParser import UserTaskParser
from SpiffWorkflow.camunda.specs.UserTask import Form, FormField

CAMUNDA_MODEL_NS = "http://camunda.org/schema/1.0/bpmn"


class ServiceTaskParser(TaskParser):
    def __init__(self, process_parser, spec_class, node, lane=None):
        super(ServiceTaskParser, self).__init__(process_parser, spec_class, node, lane)
        self.xpath = xpath_eval(node, extra_ns={"camunda": CAMUNDA_MODEL_NS})

    def create_task(self):
        implementation_type = self.node.attrib["{" + CAMUNDA_MODEL_NS + "}type"]
        if implementation_type != "external":
            raise ValidationException(
                "Only 'external' type is accepted in Service Task"
            )
        topic = self.node.attrib["{" + CAMUNDA_MODEL_NS + "}topic"]
        return self.spec_class(
            self.spec,
            self.get_task_spec_name(),
            topic,
            lane=self.lane,
            position=self.position,
            description=self.node.get("name", None),
        )


class MyUserTaskParser(UserTaskParser):
    def get_form(self):
        """Camunda provides a simple form builder, this will extract the
        details from that form and construct a form model from it. """
        form = Form()
        for xml_field in self.xpath('.//camunda:formData/camunda:formField'):
            if xml_field.get('type') == 'enum':
                field = self.get_enum_field(xml_field)
            else:
                field = FormField()

            field.id = xml_field.get('id')
            field.type = xml_field.get('type')
            field.label = xml_field.get('label')
            field.default_value = xml_field.get('defaultValue')

            for child in xml_field:
                if child.tag == '{' + CAMUNDA_MODEL_NS + '}properties':
                    for p in child:
                        field.add_property(p.get('id'), p.get('value'))

                if child.tag == '{' + CAMUNDA_MODEL_NS + '}validation':
                    for v in child:
                        field.add_validation(v.get('name'), v.get('config'))

            form.add_field(field)
        return form
