import feedparser
import requests
import json
import time
from datetime import datetime, timedelta
import re
import schedule
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import logging

# Suppress unnecessary warnings
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Configuration
load_dotenv()
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

class HybridNewsScraper:
    def __init__(self):
        self.perplexity_api_key = PERPLEXITY_API_KEY
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.rss_sources, self.api_sources = self.get_diverse_news_sources()
    
    def get_diverse_news_sources(self):
        """Multiple diverse news sources for unbiased coverage"""
        # RSS Feeds
        rss_sources = {
            # === PURE TECH NEWS ===
            'TechCrunch': 'https://techcrunch.com/feed/',
            'The Verge': 'https://www.theverge.com/rss/index.xml',
            'Ars Technica': 'http://feeds.arstechnica.com/arstechnica/index/',
            'Wired': 'https://www.wired.com/feed/rss',
            'MIT Technology Review': 'https://www.technologyreview.com/feed/',
            
            # === AI-FOCUSED ===
            'AI News': 'https://www.artificialintelligence-news.com/feed/',
            'TechCrunch AI': 'https://techcrunch.com/category/artificial-intelligence/feed/',
            'VentureBeat AI': 'https://venturebeat.com/category/ai/feed/',
            'AI Magazine': 'https://aimagazine.com/feed',
            
            # === B2B & ENTERPRISE ===
            'InfoWorld': 'https://www.infoworld.com/feed/',
            'SiliconANGLE': 'https://siliconangle.com/feed/',
            'Harvard Business Review': 'https://hbr.org/feed',
            
            # === SALES & B2B MARKETING ===
            'Demand Gen Report': 'https://www.demandgenreport.com/feed/',
            'MarTech B2B': 'https://martech.org/category/b2b-marketing/feed/',
            
            # === BUSINESS/TECH ===
            'Bloomberg Tech': 'https://www.bloomberg.com/technology/feed',
            'Financial Times Tech': 'https://www.ft.com/technology?format=rss',
            
            # === SALESFORCE OFFICIAL ===
            'Salesforce Blog': 'https://www.salesforce.com/blog/feed/',
            'Salesforce AI': 'https://www.salesforce.com/blog/ai/feed/',
            'Salesforce Data': 'https://www.salesforce.com/blog/data/feed/',
            'Salesforce Digital Transformation': 'https://www.salesforce.com/blog/category/digital-transformation/feed/',
            'Salesforce Newsroom': 'https://www.salesforce.com/news/feed/',
            'Salesforce Developers': 'https://developer.salesforce.com/blogs/feed',
            
            # === SALESFORCE COMMUNITY ===
            'Salesforce Ben': 'https://www.salesforceben.com/feed/',
            'The Wizard News': 'https://thewizardnews.com/feed/',
            'SFDCFanboy': 'https://www.sfdcfanboy.com/feed/',
        }
        
        # News APIs
        api_sources = {
            'newsdata_io': {
                'url': 'https://newsdata.io/api/1/news',
                'params': {
                    'apikey': 'pub_58084c4c8f9b5c4d5a1c8f0e9c4a8d8b8c8d8',
                    'category': 'technology,business',
                    'language': 'en'
                }
            }
        }
        
        return rss_sources, api_sources
    
    def calculate_keyword_score(self, title, summary, content=""):
        """Calculate relevance score based on keyword presence"""
        # High-priority keywords (weight: 3 points each)
        high_priority = [
            'artificial intelligence', 'salesforce', 'crm', 'ai', 'machine learning',
            'b2b', 'enterprise software', 'saas', 'automation', 'digital transformation'
        ]
        
        # Medium-priority keywords (weight: 2 points each)
        medium_priority = [
            'cloud computing', 'data analytics', 'cybersecurity', 'startup', 'funding',
            'api', 'integration', 'business intelligence', 'venture capital', 'fintech'
        ]
        
        # Low-priority keywords (weight: 1 point each)
        low_priority = [
            'technology', 'software', 'platform', 'innovation', 'developer',
            'application', 'system', 'solution', 'product', 'service'
        ]
        
        text = (title + " " + summary + " " + content).lower()
        score = 0
        
        # Count keyword matches
        for keyword in high_priority:
            if keyword in text:
                score += 3
        
        for keyword in medium_priority:
            if keyword in text:
                score += 2
        
        for keyword in low_priority:
            if keyword in text:
                score += 1
        
        # Normalize to 1-10 scale
        normalized_score = min(10, max(1, score))
        return normalized_score
    
    def filter_relevant_content(self, title, description="", content=""):
        """Filter for tech, AI, Salesforce, B2B content"""
        relevant_keywords = [
            'artificial intelligence', 'ai', 'machine learning', 'ml', 'deep learning',
            'salesforce', 'crm', 'customer relationship', 'saas', 'software as a service',
            'b2b', 'business to business', 'enterprise software', 'business intelligence',
            'automation', 'digital transformation', 'cloud computing', 'api', 'integration',
            'startup', 'fintech', 'martech', 'adtech', 'proptech', 'healthtech',
            'venture capital', 'funding', 'ipo', 'acquisition', 'merger',
            'cybersecurity', 'data analytics', 'big data', 'blockchain', 'cryptocurrency'
        ]
        
        unwanted_keywords = [
            'amazon prime', 'black friday', 'cyber monday', 'discount', 'sale', 'deal',
            'iphone', 'samsung galaxy', 'playstation', 'xbox', 'nintendo',
            'movie review', 'tv show', 'celebrity', 'sports', 'weather',
            'recipe', 'fashion', 'beauty', 'travel deals', 'hotel booking'
        ]
        
        text = (title + " " + description + " " + content).lower()
        is_relevant = any(keyword in text for keyword in relevant_keywords)
        has_unwanted = any(keyword in text for keyword in unwanted_keywords)
        
        return is_relevant and not has_unwanted
    
    def extract_simple_content(self, url):
        """Simple content extraction with fallback"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            content_selectors = ['article', '.article-body', '.entry-content', 'main']
            content = ''
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text().strip()
                    break
            
            if not content:
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text().strip() for p in paragraphs[:5]])
            
            return content[:1000]
        except:
            return ""
    
    def enhance_with_perplexity(self, article):
        """Enhanced article analysis using Perplexity API"""
        try:
            prompt = f"""Analyze this article briefly:
Title: {article['title']}
Summary: {article['summary']}

Provide only:
1. Relevance score (1-10) for tech/AI/Salesforce/B2B topics
2. Brief summary (1-2 sentences)

Format: "Score: X | Summary: Your summary here"
"""
            
            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a tech news analyst. Provide concise, accurate analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.2,
                "top_p": 0.9
            }
            
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.perplexity_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                if "Score:" in content and "|" in content:
                    parts = content.split("|")
                    score_part = parts[0].strip()
                    summary_part = parts[1].strip() if len(parts) > 1 else ""
                    
                    score_match = re.search(r'(\d+)', score_part)
                    score = int(score_match[1]) if score_match else 5
                    
                    summary = summary_part.replace("Summary:", "").strip()
                    
                    return {
                        'perplexity_score': min(max(score, 1), 10),
                        'perplexity_summary': summary if summary else article['summary']
                    }
            
            # Fallback to keyword-based scoring
            keyword_score = self.calculate_keyword_score(
                article['title'], 
                article['summary'],
                article.get('full_content', '')
            )
            return {
                'perplexity_score': keyword_score,
                'perplexity_summary': article['summary']
            }
            
        except Exception as e:
            print(f"⚠️ Perplexity failed, using keyword scoring: {str(e)[:50]}")
            keyword_score = self.calculate_keyword_score(
                article['title'], 
                article['summary'],
                article.get('full_content', '')
            )
            return {
                'perplexity_score': keyword_score,
                'perplexity_summary': article['summary']
            }
    
    def scrape_rss_feeds(self):
        """RSS scraping with keyword filtering"""
        articles = []
        
        for source_name, feed_url in self.rss_sources.items():
            print(f"📡 Fetching from {source_name}...")
            try:
                feed = feedparser.parse(feed_url)
                print(f"   Found {len(feed.entries)} entries")
                
                for entry in feed.entries[:10]:
                    try:
                        title = entry.get('title', 'No Title')
                        summary = entry.get('summary', entry.get('description', 'No Summary'))
                        url = entry.get('link', '#')
                        
                        if self.filter_relevant_content(title, summary):
                            extra_content = self.extract_simple_content(url)
                            
                            article = {
                                'source': source_name,
                                'title': title,
                                'summary': summary[:400] + '...' if len(summary) > 400 else summary,
                                'full_content': extra_content,
                                'url': url,
                                'published_date': entry.get('published', 'Unknown'),
                                'scrape_time': datetime.now().isoformat()
                            }
                            
                            enhancement = self.enhance_with_perplexity(article)
                            article.update(enhancement)
                            
                            articles.append(article)
                            print(f"✅ Added: {title[:50]}... (Score: {article['perplexity_score']})")
                            time.sleep(1)
                    
                    except Exception as e:
                        print(f"❌ Error processing article: {str(e)}")
                        continue
            
            except Exception as e:
                print(f"❌ Error with feed {source_name}: {str(e)}")
                continue
            
            time.sleep(2)
        
        return articles
    
    def scrape_news_apis(self):
        """API scraping"""
        articles = []
        search_terms = [
            'artificial intelligence business',
            'salesforce enterprise',
            'B2B technology',
            'startup funding',
            'SaaS platform'
        ]
        
        for term in search_terms:
            print(f"🔍 API searching: {term}")
            try:
                params = self.api_sources['newsdata_io']['params'].copy()
                params['q'] = term
                params['size'] = 5
                
                response = requests.get(
                    self.api_sources['newsdata_io']['url'],
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('results', []):
                        title = item.get('title', 'No Title')
                        description = item.get('description', 'No Description')
                        
                        if self.filter_relevant_content(title, description):
                            article = {
                                'source': f"NewsAPI - {item.get('source_id', 'Unknown')}",
                                'title': title,
                                'summary': description[:400] + '...' if len(description) > 400 else description,
                                'full_content': description,
                                'url': item.get('link', '#'),
                                'published_date': item.get('pubDate', 'Unknown'),
                                'scrape_time': datetime.now().isoformat()
                            }
                            
                            enhancement = self.enhance_with_perplexity(article)
                            article.update(enhancement)
                            
                            articles.append(article)
                            print(f"✅ API Article: {title[:50]}... (Score: {article['perplexity_score']})")
                            time.sleep(3)
            
            except Exception as e:
                print(f"❌ API Error: {str(e)}")
                continue
        
        return articles
    
    def remove_duplicates_and_sort(self, articles):
        """Remove duplicates and sort by SCORE (highest first)"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            title_words = set(article['title'].lower().split())
            is_duplicate = False
            
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                if len(title_words.intersection(seen_words)) >= 3:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(article['title'].lower())
        
        # Sort by score (HIGHEST FIRST)
        unique_articles.sort(
            key=lambda x: x.get('perplexity_score', 5),
            reverse=True
        )
        
        return unique_articles[:50]
    
    def save_articles(self, articles):
        """Save articles to hybrid_tech_news.txt (overwrites each time)"""
        public_dir = "public"
        if not os.path.exists(public_dir):
            os.makedirs(public_dir)
            print(f"📁 Created '{public_dir}' directory")
        
        # Always use the same filename
        filename = os.path.join(public_dir, "hybrid_tech_news.txt")
        
        # Use Unix line endings
        with open(filename, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f"HYBRID TECH NEWS SCRAPER RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 100 + "\n")
            f.write(f"Total Articles: {len(articles)} | Sources: {len(set(a['source'] for a in articles))}\n")
            
            scores = [a.get('perplexity_score', 5) for a in articles]
            avg_score = sum(scores) / len(scores) if scores else 0
            f.write(f"Average Relevance Score: {avg_score:.1f}/10\n")
            f.write("=" * 100 + "\n\n")
            
            for i, article in enumerate(articles, 1):
                f.write(f"ARTICLE #{i}\n")
                f.write("-" * 80 + "\n")
                f.write(f"TITLE: {article['title']}\n")
                f.write(f"SOURCE: {article['source']}\n")
                f.write(f"PUBLISHED: {article['published_date']}\n")
                f.write(f"URL: {article['url']}\n")
                f.write(f"PERPLEXITY SCORE: {article.get('perplexity_score', 'N/A')}/10\n")
                f.write(f"\nSUMMARY:\n{article.get('perplexity_summary', article['summary'])}\n")
                
                if article.get('full_content'):
                    f.write(f"\nCONTENT PREVIEW:\n{article['full_content'][:800]}{'...' if len(article['full_content']) > 800 else ''}\n")
                
                f.write("\n" + "=" * 100 + "\n\n")
        
        print(f"💾 Articles saved to: {filename}")
        return filename
    
    def run_scraping_cycle(self):
        """Complete hybrid scraping cycle"""
        print(f"🚀 Starting hybrid news scraping at {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
        all_articles = []
        
        print("\n📡 Phase 1: RSS Feed Scraping")
        rss_articles = self.scrape_rss_feeds()
        all_articles.extend(rss_articles)
        print(f"RSS Articles collected: {len(rss_articles)}")
        
        print("\n🔍 Phase 2: API Scraping")
        api_articles = self.scrape_news_apis()
        all_articles.extend(api_articles)
        print(f"API Articles collected: {len(api_articles)}")
        
        print(f"\n🔄 Phase 3: Processing {len(all_articles)} articles")
        final_articles = self.remove_duplicates_and_sort(all_articles)
        
        print(f"\n💾 Phase 4: Saving {len(final_articles)} articles")
        filename = self.save_articles(final_articles)
        
        print("\n" + "=" * 80)
        print(f"✅ SCRAPING COMPLETE!")
        print(f"📊 Total Articles: {len(final_articles)}")
        print(f"📈 Source Diversity: {len(set(a['source'] for a in final_articles))} sources")
        
        if final_articles:
            avg_score = sum(a.get('perplexity_score', 5) for a in final_articles) / len(final_articles)
            print(f"🎯 Average Relevance: {avg_score:.1f}/10")
        
        print(f"💾 Saved to: {filename}")
        print("=" * 80)

def main():
    """Main function with scheduling"""
    scraper = HybridNewsScraper()
    
    print("🎯 Running initial hybrid news scraping...")
    scraper.run_scraping_cycle()
    
    schedule.every(2).hours.do(scraper.run_scraping_cycle)
    
    print("\n⏰ Scheduler started - News will update every 2 hours")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped")

if __name__ == "__main__":
    main()
