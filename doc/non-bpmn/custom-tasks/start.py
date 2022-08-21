import json
from py_bpmn_engine import Workflow
from py_bpmn_engine.specs import WorkflowSpec
from serializer import NuclearSerializer

# Load from JSON
with open('nuclear.json') as fp:
    workflow_json = fp.read()
serializer = NuclearSerializer()
spec = WorkflowSpec.deserialize(serializer, workflow_json)

# Create the workflow.
workflow = Workflow(spec)

# Execute until all tasks are done or require manual intervention.
# For the sake of this tutorial, we ignore the "manual" flag on the
# tasks. In practice, you probably don't want to do that.
workflow.complete_all(halt_on_manual=False)
