from py_bpmn_engine.spiff.specs.spiff_task import SpiffBpmnTask

class UserTask(SpiffBpmnTask):
    
    def is_engine_task(self):
        return False