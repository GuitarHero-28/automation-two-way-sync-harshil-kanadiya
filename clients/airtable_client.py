import requests
import os
import logging
import time

from clients.custom_exceptions import ApiError, RateLimitError

class AirtableClient:
    """
    Client for interacting with the Airtable REST API (The Lead Tracker).
    Handles reading leads and updating their ClickUp Task ID for sync.
    """
    def __init__(self):
        # 1. Configuration Check (Proactive Error Handling)
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME")
        
        if not self.api_key or not self.base_id or not self.table_name:
            raise ValueError("Airtable credentials (KEY, BASE_ID, TABLE_NAME) must be set in the .env file.")

        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logging.info("AirtableClient initialized.")

    def _make_request(self, method, endpoint, **kwargs):
        """Internal helper to centralize API calls and error handling."""
        url = self.base_url if endpoint == '/' else f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status() 
            
            # 429 Rate Limit Handling 
            if response.status_code == 429:

                logging.warning("Airtable rate limit hit (429). Pausing for 5 seconds.")
                time.sleep(5)

                raise RateLimitError("Airtable rate limit exceeded.")

            return response.json()

        except requests.exceptions.HTTPError as e:
            # Handle specific API errors
            status_code = response.status_code
            logging.error(f"Airtable API Error ({status_code}) on {url}: {response.text[:100]}...")
            
            # Specific error handling to avoid crashing on a single bad record
            if status_code in (404, 422):
                raise ApiError(f"Record not found or invalid data for {endpoint}", status_code)
            
            raise ApiError(f"HTTP Error: {e}", status_code)
        
        except requests.exceptions.ConnectionError as e:
             logging.error(f"Airtable Connection Error: {e}")
             raise ApiError(f"Connection Error: {e}")

    def get_leads(self):
        """
        Retrieves leads from Airtable, filtering out LOST status.
        Uses the 'fields' parameter to only fetch necessary data.
        """
        logging.info("Fetching leads from Airtable...")
        
        params = {
            "fields": ["Name", "Email", "Status", "Source", "ClickUp Task ID"],
            # Filter leads that are NOT LOST, as required by the functional requirements.
            "filterByFormula": "NOT({Status} = 'LOST')"
        }

        try:
            # Endpoint is just the base URL for listing records
            data = self._make_request("GET", '/', params=params)
            return data.get('records', [])
        except ApiError as e:
            logging.error(f"Failed to retrieve leads: {e.message}")
            return [] # Return empty list to prevent crash on single failure

    def update_lead(self, record_id, fields_to_update):
        """
        Updates a single lead record in Airtable (used primarily to write back the ClickUp Task ID).
        """
        logging.info(f"Updating Airtable lead {record_id} with new data...")
        
        payload = {
            "fields": fields_to_update
        }
        
        try:
         
            self._make_request("PATCH", record_id, json=payload)
            logging.info(f"Successfully updated lead {record_id}.")
            return True
        except ApiError as e:
            logging.error(f"Failed to update lead {record_id}: {e.message}")
          
            return False