import os
import requests
import random
import re
from typing import List, Optional
from schemas import Article

def _get_news_api_key():
    # Accept several possible env names and sanitize the value
    candidates = ["NEWS_API_KEY", "NEWSAPI_KEY", "NEWS_APIKEY"]
    for name in candidates:
        v = os.environ.get(name)
        if not v:
            continue
        # strip surrounding whitespace and quotes
        v = v.strip().strip('"').strip("'")
        if v:
            return v
    return None


NEWS_API_KEY = _get_news_api_key()


class NewsTool:
    BASE_URL = "https://newsapi.org/v2/top-headlines"
    CATEGORIES = ["business", "entertainment", "technology", "science", "sports", "health", "general"]

    def __init__(self, api_key: Optional[str] = None, country: str = "us"):
        self.api_key = api_key or NEWS_API_KEY
        self.country = country

    def fetch_top_headlines(self, category: str = "general", page_size: int = 10) -> List[Article]:
        if not self.api_key:
            raise RuntimeError("NEWS_API_KEY not configured in environment")

        # Use provided category, randomly select page to get varied results
        page = random.randint(1, 3)  # NewsAPI free tier supports up to page 3

        params = {
            "apiKey": self.api_key,
            "country": self.country,
            "category": category,
            "page": page,
            "pageSize": page_size,
        }

        resp = requests.get(self.BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for a in data.get("articles", []):
            raw_content = a.get("content") or a.get("description") or ""
            raw_description = a.get("description") or ""
            
            clean_content = re.sub(r'<[^>]+>', '', raw_content)
            clean_description = re.sub(r'<[^>]+>', '', raw_description)
            
            article = Article(
                title=a.get("title") or "",
                description=clean_description if clean_description else None,
                content=clean_content if clean_content else None,
                image_url=a.get("urlToImage"),
                url=a.get("url"),
            )
            articles.append(article)

        # Shuffle to add more randomness
        random.shuffle(articles)
        return articles


__all__ = ["NewsTool"]