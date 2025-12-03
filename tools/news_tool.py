import os
import requests
import random
from typing import List
from schemas import Article

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")


class NewsTool:
    BASE_URL = "https://newsapi.org/v2/top-headlines"
    CATEGORIES = ["business", "entertainment", "technology", "science", "sports", "health", "general"]

    def __init__(self, api_key: str = None, country: str = "us"):
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
            article = Article(
                title=a.get("title") or "",
                description=a.get("description"),
                content=a.get("content") or a.get("description"),
                image_url=a.get("urlToImage"),
                url=a.get("url"),
            )
            articles.append(article)

        # Shuffle to add more randomness
        random.shuffle(articles)
        return articles


__all__ = ["NewsTool"]