# -*- coding: utf-8 -*-


from SpiffWorkflow.bpmn.specs.BpmnSpecMixin import BpmnSpecMixin
from SpiffWorkflow.specs.Simple import Simple


class ServiceTask(Simple, BpmnSpecMixin):

    """
    Task Spec for a bpmn:serviceTask node.
    """

    def __init__(self, wf_spec, name, topic, **kwargs):
        """
        Constructor.

        :param script: the script that must be executed by the script engine.
        """
        super(ServiceTask, self).__init__(wf_spec, name, **kwargs)
        self.topic = topic

    def is_engine_task(self):
        return False

    def serialize(self, serializer):
        return serializer.serialize_service_task(self)

    @classmethod
    def deserialize(self, serializer, wf_spec, s_state):
        return serializer.deserialize_service_task(wf_spec, s_state)
