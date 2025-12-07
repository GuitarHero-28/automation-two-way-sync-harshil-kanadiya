# 🚀 Two-Way Sync Automation: Airtable ↔ ClickUp

This project delivers a robust, **idempotent synchronization layer** between a Lead Tracking system (Airtable) and a Work Management system (ClickUp), built in Python. It ensures data consistency so sales activity updates the lead record, and lead status changes update the task for the team.

- **Lead Tracker (CRM):** Airtable  
- **Work Tracker (Tasks):** ClickUp  
- **Core Technology:** Python 3.10+ and REST APIs for both services.

---

## 🏗️ Architecture & Sync Flow

### Status Mapping

The following mapping translates statuses between Airtable and ClickUp, based on the three statuses available in the ClickUp List (`To Do`, `In Progress`, `Complete`).

| Lead Tracker (Airtable Status) | Work Tracker (ClickUp Status) | Direction of Sync | Notes |
| :--- | :--- | :--- | :--- |
| **NEW** | To Do | Lead → Task | Initial task state. |
| **CONTACTED** | In Progress | Lead ↔ Task | Active work being done. |
| **QUALIFIED** | Complete | Lead ↔ Task | Final success state. |
| **LOST** | Complete | Lead → Task | Task marked complete/closed when lead is lost. |

---

## 🔁 Architectural Flow

The sync logic runs sequentially to maintain order and data integrity.

```mermaid
graph TD
    A[Airtable Leads] -->|1. Poll Leads (AirtableClient)| B(sync_logic.py);
    B -->|2. Check Cross-Ref ID| C{Task Exists?};
    C -- YES --> D[ClickUp Task Update (PUT)];
    C -- NO --> E[ClickUp Task Create (POST)];
    E -->|3. Write New ClickUp ID Back| A;
    
    B -->|4. Poll Recently Updated Tasks (ClickUpClient)| F{Check Task Status Change};
    F -->|5. Update Lead Status| A;
