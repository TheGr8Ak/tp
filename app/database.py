import json
from datetime import datetime
import os

def save_leads(leads):
    """Saves a list of leads to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/leads_{timestamp}.json"
    
    # Create the data directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, "w") as f:
        # Convert Lead objects to dictionaries before saving
        leads_data = [lead.dict() for lead in leads]
        json.dump(leads_data, f, indent=2)
    
    print(f"Saved {len(leads)} leads to {filename}")
