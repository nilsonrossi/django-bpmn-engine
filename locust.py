from locust import HttpUser, task, constant
from random import randrange

class MyUser(HttpUser):
    wait_time = constant(1)

    @task
    def workflowinstance(self):
        var = randrange(3)
        payload = {
            "initial_data": {"var": var},
            "workflow": "0b9e9fc3-353b-40f1-aae1-69b60a7a3dd4"
        }
        self.client.post("/api/v1/workflowinstance/", json=payload)