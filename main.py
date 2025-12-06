import sys
import os

# Get the absolute path of the current directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


import logging
from dotenv import load_dotenv

from clients.airtable_client import AirtableClient 
from clients.clickup_client import ClickUpClient
from sync.sync_logic import start_sync 

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_sync():
    """Initializes configuration and runs the two-way synchronization process."""
    
    # 1. Load environment variables
    load_dotenv()
    logging.info("Configuration loaded. Starting synchronization...")

    # 2. Basic Configuration Checks
    try:
        # Check for both systems' required API keys
        if not os.getenv("AIRTABLE_API_KEY") or not os.getenv("CLICKUP_API_KEY"):
            raise ValueError("API keys are missing. Check your .env file.")
        
        # Check for Airtable configuration details
        if not os.getenv("AIRTABLE_BASE_ID") or not os.getenv("AIRTABLE_TABLE_NAME"):
            raise ValueError("Airtable BASE_ID or TABLE_NAME is missing from .env.")
        
    except ValueError as e:
        logging.critical(f"CRITICAL ERROR: {e}")
        return

    # 3. Initialize Clients
    try:
    
        airtable_client = AirtableClient()
        clickup_client = ClickUpClient()
    except Exception as e:
        
        logging.critical(f"Client initialization failed: {e}")
        return

    # 4. Start Sync Logic
    logging.info("--- Starting Two-Way Synchronization ---")
    start_sync(airtable_client, clickup_client)
    
    logging.info("Synchronization process completed.")


if __name__ == "__main__":

    run_sync()