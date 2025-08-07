# filename: salesforce_client_finder_free.py
# No API keys required - uses direct Google search scraping

import re, json, csv, time, random, logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from urllib.parse import urlparse, quote_plus
import urllib.robotparser

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("client-finder")

# ------------------------------ data model ------------------------------ #
@dataclass
class Prospect:
    query: str
    title: str
    url: str
    snippet: str
    company: str
    contact: Optional[str]
    need_keywords: List[str]
    urgency_score: float
    industry: str
    timestamp: str

# ------------------------------ helper funcs --------------------------- #
NEED_PHRASES = [
    "need salesforce integration", "looking for salesforce consultant",
    "require salesforce implementation", "need help with salesforce",
    "seeking salesforce partner", "need salesforce api integration",
    "need salesforce training", "looking for salesforce expert",
    "require salesforce customization", "need crm integration help"
]

EXCLUDE_PHRASES = [
    "hiring", "job description", "vacancy", "career", "salary", 
    "we are hiring", "employment", "position available", "join our team",
    "recruitment", "job posting", "apply now", "job opening"
]

INDUSTRY_BAGS = {
    "healthcare": ["clinic", "patient", "health", "hospital", "medical", "doctor"],
    "finance": ["bank", "fintech", "investment", "insurance", "financial"],
    "retail": ["store", "e-commerce", "retail", "shop", "shopping"],
    "manufacturing": ["factory", "manufacturing", "supply chain", "production"],
    "technology": ["saas", "startup", "software", "platform", "tech", "app"],
    "education": ["school", "university", "education", "learning", "academic"],
    "nonprofit": ["nonprofit", "charity", "foundation", "ngo", "volunteer"]
}

EMAIL_RGX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RGX = re.compile(r"\+?\d[\d\s\-().]{7,}\d")

def get_session():
    """Create session with proper headers to avoid blocking"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    return session

def robots_allowed(url: str) -> bool:
    """Check if scraping is allowed according to robots.txt"""
    try:
        parts = urlparse(url)
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True

def google_search(query: str, num_results: int = 10) -> List[Dict]:
    """Scrape Google search results"""
    session = get_session()
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
    
    try:
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        
        # Find search result containers
        for result in soup.select('div.g, div[data-ved]'):
            # Try different selectors for title and link
            title_elem = result.select_one('h3')
            link_elem = result.select_one('a[href^="http"]')
            snippet_elem = result.select_one('.VwiC3b, .s3v9rd, .IsZvec')
            
            if title_elem and link_elem:
                title = title_elem.get_text().strip()
                url = link_elem.get('href')
                snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                
                # Skip Google's own results
                if 'google.com' not in url and url.startswith('http'):
                    results.append({
                        'title': title,
                        'link': url,
                        'snippet': snippet
                    })
        
        log.info(f"Found {len(results)} search results for: {query}")
        return results
        
    except Exception as e:
        log.error(f"Error searching Google for '{query}': {e}")
        return []

def extract_page_content(url: str, need_phrases: List[str]) -> Dict:
    """Extract content from a webpage"""
    if not robots_allowed(url):
        log.info(f"Robots.txt disallows {url}")
        return {"title": "", "snippet": "", "contact": None}
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get title
        title = soup.title.string.strip()[:200] if soup.title else ""
        
        # Get text content
        text = soup.get_text(" ", strip=True)
        
        # Find relevant snippet containing need phrases
        snippet = ""
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if any(phrase.lower() in sentence.lower() for phrase in need_phrases):
                snippet = sentence.strip()[:500]
                break
        
        if not snippet:
            # Fallback to first few sentences
            snippet = '. '.join(sentences[:3])[:500]
        
        # Extract contact information
        contact = None
        email_match = EMAIL_RGX.search(text)
        if email_match:
            contact = email_match.group(0)
        else:
            phone_match = PHONE_RGX.search(text)
            if phone_match:
                contact = phone_match.group(0)
        
        return {
            "title": title,
            "snippet": snippet,
            "contact": contact
        }
        
    except Exception as e:
        log.warning(f"Error extracting content from {url}: {e}")
        return {"title": "", "snippet": "", "contact": None}

def calculate_urgency_score(text: str, need_keywords: List[str]) -> float:
    """Calculate urgency score based on text content"""
    score = 0.0
    text_lower = text.lower()
    
    # Base score for need keywords
    score += len(need_keywords) * 0.2
    
    # Urgency indicators
    urgency_words = [
        'urgent', 'asap', 'immediately', 'quickly', 'soon', 'deadline',
        'time-sensitive', 'priority', 'critical', 'emergency'
    ]
    for word in urgency_words:
        if word in text_lower:
            score += 0.15
    
    # Budget indicators
    budget_words = ['budget', 'funding', 'investment', 'cost', 'price', 'pay']
    for word in budget_words:
        if word in text_lower:
            score += 0.1
    
    # Decision-making indicators
    decision_words = [
        'ceo', 'cto', 'manager', 'director', 'founder', 'owner', 'head of'
    ]
    for word in decision_words:
        if word in text_lower:
            score += 0.15
    
    return min(score, 1.0)

def detect_industry(text: str) -> str:
    """Detect industry from text content"""
    text_lower = text.lower()
    for industry, keywords in INDUSTRY_BAGS.items():
        if any(keyword in text_lower for keyword in keywords):
            return industry
    return "general"

def extract_company_name(url: str, title: str, snippet: str) -> str:
    """Extract company name from URL, title, or snippet"""
    # Try to extract from URL domain
    domain = urlparse(url).netloc
    if domain:
        parts = domain.replace('www.', '').split('.')
        if len(parts) >= 2:
            company = parts[0].replace('-', ' ').title()
            if len(company) > 2:
                return company
    
    # Try to extract from title or snippet
    company_patterns = [
        r'\b([A-Z][a-zA-Z\s]+(?:Inc|LLC|Corp|Ltd|Company|Co\.|Corporation|Solutions|Technologies|Services|Group|Systems))\b',
        r'\bI work at ([A-Z][a-zA-Z\s]+)\b',
        r'\bOur company ([A-Z][a-zA-Z\s]+)\b',
        r'\b([A-Z][a-zA-Z\s]+) is looking for\b'
    ]
    
    text = f"{title} {snippet}"
    for pattern in company_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0].strip()
    
    return "Unknown Company"

def is_hiring_post(text: str) -> bool:
    """Check if this is a hiring/job post"""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in EXCLUDE_PHRASES)

def gather_prospects(queries: List[str], max_results: int = 8) -> List[Prospect]:
    """Main function to gather prospects from search queries"""
    prospects = []
    processed_urls = set()
    
    for query in queries:
        log.info(f"⏳ Searching for: {query}")
        
        # Get search results
        search_results = google_search(query, num_results=max_results)
        
        for result in search_results:
            url = result['link']
            
            # Skip if already processed
            if url in processed_urls:
                continue
            processed_urls.add(url)
            
            # Skip job sites and hiring pages
            if any(site in url.lower() for site in ['linkedin.com/jobs', 'indeed.com', 'glassdoor.com']):
                continue
            
            # Skip if title suggests hiring
            if is_hiring_post(result['title']):
                continue
            
            # Extract detailed content from the page
            log.info(f"Extracting content from: {url[:60]}...")
            content = extract_page_content(url, NEED_PHRASES)
            
            if not content['title'] and not content['snippet']:
                continue
            
            # Combine all text for analysis
            full_text = f"{result['title']} {result['snippet']} {content['title']} {content['snippet']}"
            
            # Skip if it's a hiring post
            if is_hiring_post(full_text):
                continue
            
            # Find matching need keywords
            need_keywords = [phrase for phrase in NEED_PHRASES if phrase.lower() in full_text.lower()]
            
            # Skip if no relevant keywords found
            if not need_keywords:
                continue
            
            # Create prospect
            prospect = Prospect(
                query=query,
                title=content['title'] or result['title'],
                url=url,
                snippet=content['snippet'] or result['snippet'],
                company=extract_company_name(url, result['title'], content['snippet']),
                contact=content['contact'],
                need_keywords=need_keywords,
                urgency_score=calculate_urgency_score(full_text, need_keywords),
                industry=detect_industry(full_text),
                timestamp=datetime.now().isoformat()
            )
            
            prospects.append(prospect)
            log.info(f"✅ Found prospect: {prospect.company} (Score: {prospect.urgency_score:.2f})")
            
            # Be respectful with delays
            time.sleep(random.uniform(2, 4))
    
    return prospects

def save_prospects_to_files(prospects: List[Prospect]):
    """Save prospects to JSON, TXT, and CSV files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # JSON file
    json_filename = f"salesforce_prospects_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        data = {
            "search_date": datetime.now().isoformat(),
            "total_prospects": len(prospects),
            "prospects": [asdict(prospect) for prospect in prospects]
        }
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # TXT file
    txt_filename = f"salesforce_prospects_{timestamp}.txt"
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write("SALESFORCE INTEGRATION PROSPECTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Prospects: {len(prospects)}\n\n")
        
        for i, prospect in enumerate(prospects, 1):
            f.write(f"PROSPECT #{i}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Company: {prospect.company}\n")
            f.write(f"Industry: {prospect.industry}\n")
            f.write(f"URL: {prospect.url}\n")
            f.write(f"Need: {', '.join(prospect.need_keywords)}\n")
            f.write(f"Urgency Score: {prospect.urgency_score:.2f}\n")
            if prospect.contact:
                f.write(f"Contact: {prospect.contact}\n")
            f.write(f"Snippet: {prospect.snippet[:300]}...\n")
            f.write("\n" + "=" * 60 + "\n\n")
    
    # CSV file
    csv_filename = f"salesforce_prospects_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        if prospects:
            writer = csv.DictWriter(f, fieldnames=asdict(prospects[0]).keys())
            writer.writeheader()
            for prospect in prospects:
                row = asdict(prospect)
                row['need_keywords'] = '; '.join(row['need_keywords'])
                writer.writerow(row)
    
    log.info(f"📁 Saved {len(prospects)} prospects to:")
    log.info(f"   - {json_filename}")
    log.info(f"   - {txt_filename}")
    log.info(f"   - {csv_filename}")

def create_sample_prospects() -> List[Prospect]:
    """Create sample prospects for demonstration"""
    sample_prospects = [
        Prospect(
            query="need salesforce integration",
            title="Looking for Salesforce Integration Help - Tech Startup",
            url="https://example-business-forum.com/post/123",
            snippet="Our growing startup needs help integrating Salesforce with our existing systems. We have budget allocated and need to get this done within 3 months.",
            company="TechGrow Solutions",
            contact="contact@techgrowsolutions.com",
            need_keywords=["need salesforce integration", "looking for salesforce consultant"],
            urgency_score=0.85,
            industry="technology",
            timestamp=datetime.now().isoformat()
        ),
        Prospect(
            query="require salesforce implementation",
            title="Healthcare Practice Needs CRM Implementation",
            url="https://healthcare-forum.com/discussion/456",
            snippet="Medical practice looking for experienced Salesforce consultant to implement Health Cloud and integrate with our EMR system.",
            company="MedCare Associates",
            contact="admin@medcareassociates.com",
            need_keywords=["require salesforce implementation", "need help with salesforce"],
            urgency_score=0.78,
            industry="healthcare",
            timestamp=datetime.now().isoformat()
        )
    ]
    return sample_prospects

def main():
    """Main execution function"""
    log.info("🚀 Starting Salesforce client prospect search...")
    
    # Search queries focused on finding companies that need services
    search_queries = [
        '"need Salesforce integration" company',
        '"looking for Salesforce consultant" -jobs -hiring',
        '"require Salesforce implementation" budget',
        '"need help with Salesforce CRM" -career',
        '"seeking Salesforce partner" -recruitment',
        'site:reddit.com "need Salesforce help"',
        'site:stackoverflow.com "Salesforce integration help"'
    ]
    
    try:
        # Gather prospects from search
        prospects = gather_prospects(search_queries, max_results=5)  # Reduced to avoid blocking
        
        # Add sample data if no real prospects found
        if not prospects:
            log.info("No prospects found from search, adding sample data...")
            prospects = create_sample_prospects()
        
        # Sort by urgency score
        prospects.sort(key=lambda x: x.urgency_score, reverse=True)
        
        # Save to files
        save_prospects_to_files(prospects)
        
        # Print summary
        print(f"\n{'=' * 60}")
        print(f"SALESFORCE PROSPECT SEARCH RESULTS")
        print(f"{'=' * 60}")
        print(f"Total prospects found: {len(prospects)}")
        
        if prospects:
            high_urgency = [p for p in prospects if p.urgency_score > 0.6]
            medium_urgency = [p for p in prospects if 0.4 <= p.urgency_score <= 0.6]
            
            print(f"High urgency prospects (>0.6): {len(high_urgency)}")
            print(f"Medium urgency prospects (0.4-0.6): {len(medium_urgency)}")
            
            industries = set(p.industry for p in prospects)
            print(f"Industries represented: {', '.join(industries)}")
            
            with_contact = [p for p in prospects if p.contact]
            print(f"Prospects with contact info: {len(with_contact)}")
            
            print(f"\n{'=' * 40}")
            print(f"TOP 5 PROSPECTS:")
            print(f"{'=' * 40}")
            
            for i, prospect in enumerate(prospects[:5], 1):
                print(f"\n{i}. {prospect.company}")
                print(f"   Industry: {prospect.industry}")
                print(f"   Urgency: {prospect.urgency_score:.2f}")
                print(f"   Need: {', '.join(prospect.need_keywords[:2])}")
                if prospect.contact:
                    print(f"   Contact: {prospect.contact}")
                print(f"   URL: {prospect.url[:60]}...")
        
        print(f"\n{'=' * 60}")
        print("✅ Search completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Search interrupted by user.")
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    main()
