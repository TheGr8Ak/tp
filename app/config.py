import json

def load_sources():
    """Loads the data sources from the whitelist file."""
    with open("sources_whitelist.json", "r") as f:
        return json.load(f)
