import requests
import json

def push_to_salesforce(lead):
    """Simulates pushing a lead to the Salesforce CRM."""
    # In a real implementation, you would use the Salesforce REST API
    # and proper authentication (OAuth 2.0)
    print(f"Pushing lead to Salesforce: {lead.project_description}") # Changed to project_description for better debug info
    
    # Example of what a real request might look like:
    # headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN"}
    # response = requests.post("https://your_instance.salesforce.com/services/data/v58.0/sobjects/Lead", json=lead.dict())
    
    # For this prototype, we'll just print the lead
    print(json.dumps(lead.dict(), indent=2))
    
    return True