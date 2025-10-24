from locust import HttpUser, task, between

class NeoBotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def send_message(self):
        self.client.post("/webhook/whatsapp", json={
            "tenant_id": 1,
            "from_number": "237690000000",
            "message": "Test charge"
        })
    
    @task(1)
    def get_analytics(self):
        self.client.get("/api/tenants/1/analytics")
