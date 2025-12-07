import logging
import os
from clients.custom_exceptions import ApiError

from sync.data_mapper import (LEAD_TO_TASK_STATUS, TASK_TO_LEAD_STATUS, 
                              map_lead_fields_to_task_payload) 

def get_airtable_id_from_task(task, custom_field_id):
    """
    Extracts the Airtable Lead ID from the ClickUp task's custom fields.
    Returns the ID string or None if not found.
    """
    for field in task.get('custom_fields', []):
        if field.get('id') == custom_field_id:
            return field.get('value')
    return None

# =========================================================================
# PHASE 1: LEAD TRACKER -> WORK TRACKER 
# =========================================================================

def sync_leads_to_tasks(airtable_client, clickup_client):
    """
    Reads all active leads from Airtable and ensures a corresponding task 
    exists and is updated in ClickUp. Implements idempotency.
    """
    logging.info("\n--- PHASE 1: Starting LEAD -> TASK Sync (Airtable is Source) ---")
    
    leads = airtable_client.get_leads()
    logging.info(f"Retrieved {len(leads)} active leads for processing.")

    for lead in leads:
        lead_id = lead.get('id')
        lead_name = lead.get('fields', {}).get('Name', 'N/A')
        
        existing_task_id = lead.get('fields', {}).get('ClickUp Task ID')
        
        try:
            task_payload = map_lead_fields_to_task_payload(lead) 

            if existing_task_id:
                # 2. IDEMPOTENCY PATH: Task already exists. Just update the status.
                target_status = task_payload['status']
                
                logging.info(f"Existing Lead '{lead_name}'. Target status: {target_status}.")
                
                clickup_client.update_task_status(existing_task_id, target_status)

            else:
                # 3. CREATION PATH: Task does not exist. Create and Link Back.
                logging.info(f"New Lead '{lead_name}'. Creating task...")
                
                new_task_id = clickup_client.create_task(task_payload)

                airtable_client.update_lead(lead_id, {'ClickUp Task ID': new_task_id})
            
        except ApiError as e:
            logging.error(f"Failed to process lead '{lead_name}' ({lead_id}). Error: {e.message}. Continuing sync.")
        except Exception as e:
             logging.error(f"Unhandled error during Lead->Task sync for '{lead_name}': {e}. Continuing.")


# =========================================================================
# PHASE 2: WORK TRACKER -> LEAD TRACKER (Reverse Status Sync)
# =========================================================================

def sync_tasks_to_leads(airtable_client, clickup_client):

    logging.info("\n--- PHASE 2: Starting TASK -> LEAD Sync (ClickUp is Source) ---")
    
    tasks = clickup_client.get_updated_tasks(since_minutes=60) 
    logging.info(f"Retrieved {len(tasks)} recently updated tasks from ClickUp.")

    custom_field_id = os.getenv("CLICKUP_CUSTOM_FIELD_ID")

    for task in tasks:
        task_id = task.get('id')
        task_status_name = task.get('status', {}).get('status')

        airtable_lead_id = get_airtable_id_from_task(task, custom_field_id)
        
        if not airtable_lead_id:
            logging.debug(f"Task {task_id} skipped: No Airtable Lead ID found. (Internal task)")
            continue 

        target_lead_status = TASK_TO_LEAD_STATUS.get(task_status_name)

        if not target_lead_status:
            logging.warning(f"ClickUp status '{task_status_name}' has no mapping in TASK_TO_LEAD_STATUS. Skipping update for {airtable_lead_id}.")
            continue 

        logging.info(f"Task {task_id} status changed to '{task_status_name}'. Updating Lead {airtable_lead_id} to '{target_lead_status}'.")
        
        airtable_client.update_lead(airtable_lead_id, {'Status': target_lead_status})


# =========================================================================
# MAIN SYNC ENTRY POINT
# =========================================================================

def start_sync(airtable_client, clickup_client):
    """
    Runs the full two-way synchronization process, handling potential critical errors.
    """
    try:
        sync_leads_to_tasks(airtable_client, clickup_client)
        sync_tasks_to_leads(airtable_client, clickup_client)
        
    except Exception as e:
        logging.critical(f"A critical error stopped the synchronization process: {e}")