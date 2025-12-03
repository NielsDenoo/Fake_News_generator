import os
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama


class FinalStoryChain:
    def __init__(self, llm=None):
        self.llm = llm or ChatOllama(model="llama3:8b", temperature=0.9)
        self.prompt = PromptTemplate(
            input_variables=["article_title", "article_text", "continuation_choice"],
            template=(
                "You are a satirical fake news writer. Given the real news article below and a chosen continuation idea, "
                "write a sensationalized fake news story in 6-10 paragraphs. Use exaggerated claims, dramatic language, "
                "absurd unnamed sources (like 'sources close to the matter', 'anonymous insiders'), clickbait-style writing, "
                "conspiracy theories, and over-the-top speculation. Make it clearly satirical and ridiculous while building on the article's themes. "
                "Include fake quotes from fictional experts or officials. Do NOT repeat the article verbatim. Output only the fake news story text.\n\n"
                "Article Title: {article_title}\n\nArticle Content:\n{article_text}\n\nChosen Continuation Idea:\n{continuation_choice}"
            ),
        )

    def generate(self, article_title: str, article_text: str, continuation_choice: str) -> str:
        chain = self.prompt | self.llm
        res = chain.invoke({"article_title": article_title, "article_text": article_text, "continuation_choice": continuation_choice}).content
        return res.strip()


__all__ = ["FinalStoryChain"]