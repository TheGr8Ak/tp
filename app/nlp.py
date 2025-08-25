import spacy

# Note: You'll need to download the spaCy model first:
# python -m spacy download en_core_web_sm

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

def process_text(text):
    """Analyzes text to identify Salesforce-related keywords and entities."""
    if not nlp:
        return None, []
    
    doc = nlp(text)
    
    # Example: Simple keyword matching
    keywords = ["salesforce implementation", "salesforce migration", "salesforce consulting"]
    if any(keyword in text.lower() for keyword in keywords):
        return text, [ent.text for ent in doc.ents if ent.label_ in ["ORG", "GPE"]]
    
    return None, []

def score_lead(lead):
    """Scores a lead based on its content and industry."""
    score = 0
    if lead.get("industry") == "Real Estate":
        score += 30
    
    # Add more scoring logic here
    
    return score
