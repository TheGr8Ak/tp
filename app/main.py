from fastapi import FastAPI, BackgroundTasks
from datetime import datetime
import asyncio
import glob
import json

from .config import load_sources
from .fetcher import fetch_all_sources
from .nlp import process_text, score_lead
from .database import save_leads
from .models import Lead
from .salesforce import push_to_salesforce

app = FastAPI()

async def prospect_task():
    """The core lead prospecting task."""
    print("Starting prospecting task...")
    sources = load_sources()
    raw_results = await fetch_all_sources(sources)
    print(f"Debug: raw_results = {raw_results}") # Debug print

    leads = []
    if raw_results:
        for result_list in raw_results:
            print(f"Debug: Processing result_list = {result_list}") # Debug print
            if not result_list:
                continue
            # The result from fetch_all_sources is a list of lists, so iterate over the inner list
            if isinstance(result_list, list):
                for item in result_list:
                    print(f"Debug: Processing item = {item}") # Debug print
                    # Normalize data from different source types (RSS vs API)
                    if 'title' in item and 'link' in item: # RSS - CHANGED THIS LINE
                        text = item['title'] + " " + item.get('summary', '')
                        link = item['link']
                        source_platform = item.get('source', {}).get('title', 'Unknown')
                        print(f"Debug: Extracted text = {text}, link = {link}") # Debug print
                    elif isinstance(item, dict) and 'data' in item: # Reddit
                        text = item['data'].get('title', '') + " " + item['data'].get('selftext', '')
                        link = item['data'].get('url', '')
                        source_platform = "Reddit"
                        print(f"Debug: Extracted text (Reddit) = {text}, link = {link}") # Debug print
                    else:
                        print(f"Debug: Item skipped due to missing title/link or data: {item}") # Debug print
                        continue

                    processed_text, entities = process_text(text)
                    print(f"Debug: processed_text = {processed_text}") # Debug print
                    if processed_text:
                        lead = Lead(
                            project_description=processed_text,
                            source_platform=source_platform,
                            source_link=link,
                            date_found=datetime.now().isoformat(),
                            priority_score=0 # Score will be calculated next
                        )
                        lead.priority_score = score_lead(lead.dict())
                        print(f"Debug: Lead created: {lead.dict()}") # Debug print
                        leads.append(lead)

                        if lead.priority_score > 80: # High-priority
                            push_to_salesforce(lead)

    if leads:
        print(f"Debug: About to save {len(leads)} leads.") # Debug print
        save_leads(leads)
    else:
        print("Debug: No leads to save.") # Debug print

    print(f"Prospecting task finished. Found {len(leads)} leads.")

@app.on_event("startup")
async def startup_event():
    # Run the prospecting task every 10 minutes
    async def schedule_prospecting():
        while True:
            await prospect_task()
            await asyncio.sleep(600) # 10 minutes
    
    asyncio.create_task(schedule_prospecting())

@app.get("/")
def read_root():
    return {"message": "Salesforce Lead Prospecting Tool"}

@app.post("/prospect/run")
async def run_prospecting_now(background_tasks: BackgroundTasks):
    """Manually trigger the prospecting task."""
    background_tasks.add_task(prospect_task)
    return {"status": "Prospecting task started in the background"}

@app.get("/leads")
def get_leads():
    """Retrieves all saved leads from the data directory."""
    lead_files = glob.glob("data/leads_*.json")
    all_leads = []
    for file_path in sorted(lead_files, reverse=True):
        with open(file_path, "r") as f:
            all_leads.extend(json.load(f))
    return all_leads