import requests
import os
import logging
import time
from datetime import datetime, timedelta

from .custom_exceptions import ApiError, RateLimitError

class ClickUpClient:
    """
    Client for interacting with the ClickUp REST API (The Work Tracker).
    """
    def __init__(self):
        # 1. Configuration Check
        self.api_key = os.getenv("CLICKUP_API_KEY")
        self.list_id = os.getenv("CLICKUP_LIST_ID")
        self.custom_field_id = os.getenv("CLICKUP_CUSTOM_FIELD_ID")

        
        if not self.api_key or not self.list_id or not self.custom_field_id:
            raise ValueError(
                "ClickUp credentials (CLICKUP_API_KEY, CLICKUP_LIST_ID, CLICKUP_CUSTOM_FIELD_ID) "
                "must be set in the .env file."
            )

        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": self.api_key,  # Sending just "pk_..."
            "Content-Type": "application/json"
        }
        logging.info("ClickUpClient initialized successfully.")


    def _make_request(self, method, endpoint, **kwargs):
        """Internal helper to centralize all ClickUp API requests (v2 only)."""
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)

            if response.status_code == 429:
                logging.warning("ClickUp rate limit hit (429). Sleeping for 10 seconds...")
                time.sleep(10)
                raise RateLimitError("ClickUp rate limit exceeded.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status = response.status_code
            text = response.text[:200]

            logging.error(f"ClickUp API Error ({status}) on {url}: {text}")

            if status in (400, 404):
                raise ApiError(f"ClickUp non-critical error: {text}", status)

            raise ApiError(f"ClickUp critical error: {e}", status)

        except requests.exceptions.ConnectionError as e:
            logging.error(f"ClickUp Connection Error: {e}")
            raise ApiError(f"Connection Error: {e}")

    def create_task(self, task_payload):
        """Creates a new task inside the configured ClickUp list using v2."""
        endpoint = f"list/{self.list_id}/task"

        logging.info("Creating new ClickUp task...")

        try:
            data = self._make_request("POST", endpoint, json=task_payload)
            task_id = data.get("id")

            logging.info(f"Successfully created ClickUp task: {task_id}")
            return task_id

        except ApiError as e:
            logging.error(f"Failed to create task: {e.message}")
            raise

    def get_updated_tasks(self, since_minutes=60):
        """
        Returns tasks updated within last X minutes.
        """
        time_threshold = datetime.now() - timedelta(minutes=since_minutes)
        timestamp_ms = int(time_threshold.timestamp() * 1000)

        endpoint = f"list/{self.list_id}/task"

        params = {
            "include_closed": True,
            "subtasks": False,
            "date_updated_gt": timestamp_ms,
            #"custom_fields": [self.custom_field_id] 
        }

        logging.info(f"Fetching ClickUp tasks updated in last {since_minutes} minutes...")

        try:
            data = self._make_request("GET", endpoint, params=params)
            return data.get("tasks", [])

        except ApiError as e:
            logging.error(f"Failed to retrieve updated tasks: {e.message}")
            return []
        
    def update_task_status(self, task_id, new_status):
        """Updates task status in v2."""
        endpoint = f"task/{task_id}"

        payload = {"status": new_status}

        try:
            self._make_request("PUT", endpoint, json=payload)
            logging.info(f"Updated task {task_id} → status '{new_status}'")
            return True

        except ApiError as e:
            logging.error(f"Failed to update ClickUp task {task_id}: {e.message}")
            return False