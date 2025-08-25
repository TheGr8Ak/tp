import asyncio
import aiohttp
import feedparser

async def fetch_source(session, source):
    """Fetches data from a single source."""
    try:
        if source['type'] == 'rss':
            async with session.get(source['url']) as response:
                data = await response.text()
                feed = feedparser.parse(data)
                return feed.entries
        elif source['type'] == 'api':
            async with session.get(source['url']) as response:
                return await response.json()
    except Exception as e:
        print(f"Error fetching {source['url']}: {e}")
        return None

async def fetch_all_sources(sources):
    """Fetches data from all sources in parallel."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_source(session, source) for source_list in sources.values() for source in source_list]
        results = await asyncio.gather(*tasks)
        return results
