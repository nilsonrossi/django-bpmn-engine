from py_bpmn_engine.spiff.specs.spiff_task import SpiffBpmnTask

class ManualTask(SpiffBpmnTask):
    
    def is_engine_task(self):
        return False