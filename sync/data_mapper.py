import os

# =========================================================================
# 1. STATUS MAPPING DICTIONARIES
# =========================================================================

# Maps Airtable Status to ClickUp Status 
LEAD_TO_TASK_STATUS = {
    "NEW": "To Do",
    "CONTACTED": "In Progress",
    "QUALIFIED": "Complete",
    "LOST": "Complete" 
}

# Maps ClickUp Status to Airtable Status 
TASK_TO_LEAD_STATUS = {
    "to do": "NEW",
    "in progress": "CONTACTED",
    "complete": "QUALIFIED"
}

# =========================================================================
# 2. PAYLOAD CONSTRUCTION FUNCTION
# =========================================================================

def map_lead_fields_to_task_payload(lead_record):
    """
    Transforms an Airtable lead record into the JSON payload required 
    by the ClickUp API for task creation or update.
    """
    CLICKUP_CUSTOM_FIELD_ID = os.getenv("CLICKUP_CUSTOM_FIELD_ID")
    if not CLICKUP_CUSTOM_FIELD_ID:
        raise ValueError("CLICKUP_CUSTOM_FIELD_ID is not set in environment. Check your .env file.")

    fields = lead_record.get('fields', {})
    lead_id = lead_record.get('id')
    
    lead_status = fields.get('Status', 'NEW')
    lead_name = fields.get('Name', 'Unknown Lead')
    lead_source = fields.get('Source', 'N/A')
    
    title = f"[{lead_status}] Follow-up: {lead_name} from {lead_source}"
    notes = f"**Lead Details:**\nEmail: {fields.get('Email')}\nSource: {lead_source}\n\nThis task is linked to Airtable record {lead_id}."
    
    clickup_status = LEAD_TO_TASK_STATUS.get(lead_status, "To Do")
    
    payload = {
        "name": title,
        "description": notes,
        "status": clickup_status,
        
        "custom_fields": [
            {
                "id": CLICKUP_CUSTOM_FIELD_ID,
                "value": lead_id 
            }
        ]
    }
    return payload