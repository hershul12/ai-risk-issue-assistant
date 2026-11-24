"""Locust load test for RiskPilot: simulates people using the dashboard.

Read-only endpoints only. /suggest and /extract are deliberately NOT called because each
request makes a paid Azure OpenAI call.

Run headless from the project root (backend running at http://127.0.0.1:8000):

    venv\\Scripts\\locust -f backend/loadtest/locustfile.py --host http://127.0.0.1:8000 ^
        --headless -u 20 -r 5 -t 1m --csv backend/loadtest/results/riskpilot --only-summary

Or open the web UI with: venv\\Scripts\\locust -f backend/loadtest/locustfile.py --host http://127.0.0.1:8000
"""

import random

from locust import HttpUser, between, task


class DashboardUser(HttpUser):
    """A Project Manager, Risk Owner or Programme Lead browsing the register.

    Opening the app loads the register and the summary; the person then reads,
    clicks into records (detail drawer + audit history) and refreshes now and then.
    """

    # Time a person spends reading before the next click.
    wait_time = between(2, 6)

    def on_start(self):
        # Opening the dashboard: the app loads the register and the summary together.
        self.item_ids = []
        with self.client.get("/items", name="/items", catch_response=True) as res:
            if res.status_code == 200:
                self.item_ids = [item["id"] for item in res.json()]
                res.success()
            else:
                res.failure(f"status {res.status_code}")
        self.client.get("/dashboard/summary", name="/dashboard/summary")

    def _random_id(self):
        return random.choice(self.item_ids) if self.item_ids else 1

    @task(4)
    def open_record(self):
        # Clicking a row opens the drawer, which loads the record and its audit history.
        item_id = self._random_id()
        self.client.get(f"/items/{item_id}", name="/items/{id}")
        self.client.get(f"/items/{item_id}/audit", name="/items/{id}/audit")

    @task(3)
    def refresh_register(self):
        # After a change the app reloads the list and the summary.
        self.client.get("/items", name="/items")
        self.client.get("/dashboard/summary", name="/dashboard/summary")

    @task(2)
    def filter_register(self):
        # Filters are applied in the browser, but people also reload the summary strip.
        self.client.get("/dashboard/summary", name="/dashboard/summary")

    @task(1)
    def health(self):
        # Stand-in for a monitoring probe hitting /health.
        self.client.get("/health", name="/health")
