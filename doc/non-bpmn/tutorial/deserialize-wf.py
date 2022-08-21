from py_bpmn_engine import Workflow
from py_bpmn_engine.serializer.json import JSONSerializer

serializer = JSONSerializer()
with open('workflow.json') as fp:
    workflow_json = fp.read()
workflow = Workflow.deserialize(serializer, workflow_json)
