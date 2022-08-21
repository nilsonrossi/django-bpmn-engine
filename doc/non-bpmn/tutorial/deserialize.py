from py_bpmn_engine.specs import WorkflowSpec
from py_bpmn_engine.serializer.json import JSONSerializer

serializer = JSONSerializer()
with open('workflow-spec.json') as fp:
    workflow_json = fp.read()
spec = WorkflowSpec.deserialize(serializer, workflow_json)
