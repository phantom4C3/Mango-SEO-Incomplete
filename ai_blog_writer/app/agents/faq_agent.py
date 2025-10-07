# ai_blog_writer\app\agents\faq_agent.py 
import logging
import json
from typing import List, Dict, Any, Optional
from ..clients.ai_clients import gemini_client

logger = logging.getLogger(__name__)

class FAQAgent:
    """
    Generates FAQs based on completed blog content.
    Designed to produce structured JSON suitable for rich snippets.
    """

    def __init__(self):
        self.clients = {
            "gemini": gemini_client
        }

    async def generate_faqs(
        self,
        blog_content: str,
        target_keywords: Optional[List[str]] = None,
        max_faqs: int = 7,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Generate FAQs for a blog.
        
        Parameters:
        - blog_content: full content of the blog
        - target_keywords: optional keywords to focus on
        - max_faqs: maximum number of FAQs to generate
        - language: language for the questions and answers
        
        Returns:
        - List of dictionaries, each with 'question', 'answer', and optional metadata
        """
        try:
            keywords_text = ", ".join(target_keywords) if target_keywords else "general"

            prompt = f"""
            You are a professional content writer. Based on the following blog content, generate up to {max_faqs} FAQs.
            Each FAQ should include a clear question and a concise answer suitable for a reader.
            Make sure FAQs incorporate the following keywords where relevant: {keywords_text}.
            Output as JSON in this format:
            [
                {{
                    "question": "FAQ question here",
                    "answer": "Concise answer here",
                    "tags": ["optional keyword tags"],
                    "language": "{language}"
                }}
            ]

            Blog Content:
            {blog_content}
            """

            response = await gemini_client.generate_structured(prompt=prompt)

            if not response:
                logger.warning("FAQ generation returned empty. Using fallback FAQs.")
                return self._generate_fallback_faqs(blog_content, target_keywords, max_faqs, language)

            if isinstance(response, str):
                faqs = json.loads(response)
            else:
                faqs = response

            # Ensure language field
            for faq in faqs:
                faq["language"] = faq.get("language", language)

            return faqs

        except Exception as e:
            logger.error(f"FAQ generation failed: {str(e)}")
            return self._generate_fallback_faqs(blog_content, target_keywords, max_faqs, language)

    def _generate_fallback_faqs(
        self,
        blog_content: str,
        target_keywords: Optional[List[str]],
        max_faqs: int,
        language: str
    ) -> List[Dict[str, Any]]:
        """
        Generate simple fallback FAQs using rule-based method.
        Splits content into sentences and creates generic questions.
        """
        faqs = []
        sentences = blog_content.split(". ")
        for i, sentence in enumerate(sentences[:max_faqs]):
            question = f"What is about {target_keywords[0]}?" if target_keywords else f"FAQ {i+1}"
            answer = sentence.strip()
            faqs.append({
                "question": question,
                "answer": answer,
                "tags": target_keywords[:3] if target_keywords else [],
                "language": language
            })
        return faqs

# Singleton instance
faq_agent = FAQAgent()
