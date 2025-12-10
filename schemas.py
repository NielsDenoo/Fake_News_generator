from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class Article(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    url: Optional[HttpUrl] = None


class TitlesOutput(BaseModel):
    titles: List[str]
    article_indices: List[int] = []


class ContinuationOptions(BaseModel):
    options: List[str]


class SessionState(BaseModel):
    articles: List[Article] = []
    title_to_article_map: List[int] = []
    selected_article_index: Optional[int] = None
    continuation_options: List[str] = []
    selected_continuation_index: Optional[int] = None
    final_story: Optional[str] = None
    image_base64: Optional[str] = None