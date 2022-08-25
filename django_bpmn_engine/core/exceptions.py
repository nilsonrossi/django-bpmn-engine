from typing import Any
from typing import Dict


class WorkflowTaskError(Exception):
    def __init__(self, task_id: str, message: Dict[str, Any]):
        self.task_id = task_id
        self.message = message

    def __str__(self):
        return f"Error on task ({self.task_id=}): {self.message}"
