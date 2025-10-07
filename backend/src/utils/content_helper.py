# backend/src/utils/content_helper.py
"""
Consolidated Content Helper Service
Handles content formatting, enrichment, and preparation for CMS publication.
Focuses on creating visually attractive blog posts for CMS landing pages.
"""

import re
import logging
import httpx
import unicodedata
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter
from uuid import UUID

from ..clients.supabase_client import supabase_client
from backend.src.core.config import settings
from backend.src.core.exceptions import FormatterError

logger = logging.getLogger(__name__)

# In-memory task log store for inline updates (frontend polls this)
task_logs: Dict[str, List[Dict[str, str]]] = {}


def log_task(task_id: str, message: str):
    """Append a log message for a given task ID."""
    if task_id not in task_logs:
        task_logs[task_id] = []
    task_logs[task_id].append(
        {"timestamp": datetime.utcnow().isoformat(), "message": message}
    )


class ContentHelper:
    """
    Comprehensive content helper service for creating visually attractive
    CMS-ready blog posts with proper formatting, SEO optimization, and engagement features.
    """

    # ================= MAIN CMS FORMATTING METHOD ================= #
    
    async def format_for_cms(self, article_data: Dict[str, Any], user_id: UUID) -> str:
        """
        Main method to transform AI-generated article data into a complete, 
        visually attractive HTML document ready for CMS publication.
        
        This creates a polished blog post with:
        - Professional styling and layout
        - SEO optimization
        - Interactive elements
        - Visual content integration
        - Responsive design
        """
        try:
            # Extract and prepare data
            title = article_data.get("title", "")
            content = article_data.get("content", "")
            website_url = article_data.get("website_url", "")
            featured_image_url = article_data.get("featured_image_url", "")
            meta_description = article_data.get("meta_description", "")
            keywords = article_data.get("keywords", [])
            
            # Generate missing SEO elements if needed
            if not meta_description:
                meta_description = await self.generate_seo_meta_description(content, title)
            
            # Process and enhance content
            enhanced_content = await self._enhance_content_structure(content)
            
            # Generate website screenshot if URL provided
            screenshot_section = ""
            if website_url:
                screenshot_url = await self.capture_screenshot(website_url)
                if screenshot_url:
                    screenshot_section = self._create_screenshot_section(screenshot_url, website_url)
            
            # Create engaging introduction
            intro_section = self._create_intro_section(title, meta_description)
            
            # Create call-to-action section
            cta_section = self._create_cta_section(website_url, title)
            
            # Generate reading time and other metadata
            reading_time = self.calculate_reading_time(content)
            publish_date = datetime.utcnow().strftime("%B %d, %Y")
            
            # Build the complete HTML document
            final_html = self._build_complete_html(
                title=title,
                meta_description=meta_description,
                keywords=keywords,
                featured_image_url=featured_image_url,
                intro_section=intro_section,
                enhanced_content=enhanced_content,
                screenshot_section=screenshot_section,
                cta_section=cta_section,
                reading_time=reading_time,
                publish_date=publish_date
            )
            
            return self.sanitize_html(final_html)
            
        except Exception as e:
            logger.error(f"Error formatting content for CMS: {str(e)}")
            raise FormatterError(detail=str(e), operation="format_for_cms")

    def _build_complete_html(self, **kwargs) -> str:
      """Build a real blog post HTML (not card-style)"""
    
      return f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="{kwargs['meta_description']}">
        <meta name="keywords" content="{', '.join(kwargs['keywords'])}">
        <meta property="og:title" content="{kwargs['title']}">
        <meta property="og:description" content="{kwargs['meta_description']}">
        <meta property="og:image" content="{kwargs['featured_image_url']}">
        <meta property="og:type" content="article">
        <title>{kwargs['title']}</title>
        <style>
            /* REAL BLOG STYLING - No card design */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.8;
                color: #333;
                background: #fff;
                font-size: 18px;
            }}
            
            .blog-container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            
            .blog-header {{
                text-align: center;
                padding: 4rem 0 2rem;
                border-bottom: 1px solid #eaeaea;
                margin-bottom: 3rem;
            }}
            
            .blog-title {{
                font-size: 3.5rem;
                font-weight: 800;
                line-height: 1.2;
                margin-bottom: 1.5rem;
                color: #1a202c;
            }}
            
            .blog-meta {{
                display: flex;
                justify-content: center;
                gap: 2rem;
                font-size: 1rem;
                color: #718096;
                margin-bottom: 2rem;
            }}
            
            .meta-item {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .featured-image {{
                width: 100%;
                height: 500px;
                object-fit: cover;
                margin: 2rem 0;
            }}
            
            .blog-content {{
                max-width: 800px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            
            .intro-section {{
                font-size: 1.3rem;
                color: #4a5568;
                margin-bottom: 3rem;
                line-height: 1.8;
                font-style: italic;
            }}
            
            .content-body {{
                font-size: 1.2rem;
                line-height: 1.9;
            }}
            
            .content-body h1 {{
                font-size: 2.5rem;
                margin: 3rem 0 1.5rem;
                color: #2d3748;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 0.5rem;
            }}
            
            .content-body h2 {{
                font-size: 2rem;
                margin: 2.5rem 0 1.2rem;
                color: #4a5568;
            }}
            
            .content-body h3 {{
                font-size: 1.5rem;
                margin: 2rem 0 1rem;
                color: #718096;
            }}
            
            .content-body p {{
                margin-bottom: 1.8rem;
            }}
            
            .content-body blockquote {{
                border-left: 4px solid #667eea;
                padding: 2rem;
                margin: 2.5rem 0;
                background: #f7fafc;
                font-style: italic;
                font-size: 1.3rem;
            }}
            
            .screenshot-section {{
                margin: 3rem 0;
                text-align: center;
            }}
            
            .screenshot-image {{
                width: 100%;
                max-width: 800px;
                height: auto;
                margin: 0 auto;
                display: block;
            }}
            
            .cta-section {{
                background: #f8f9fa;
                padding: 3rem 2rem;
                margin: 3rem 0;
                text-align: center;
                border-top: 1px solid #eaeaea;
                border-bottom: 1px solid #eaeaea;
            }}
            
            .cta-button {{
                display: inline-block;
                padding: 1rem 2rem;
                background: #667eea;
                color: white;
                text-decoration: none;
                font-weight: 600;
                margin-top: 1.5rem;
            }}
            
            @media (max-width: 768px) {{
                .blog-title {{
                    font-size: 2.5rem;
                }}
                
                .blog-meta {{
                    flex-direction: column;
                    gap: 1rem;
                }}
                
                .featured-image {{
                    height: 300px;
                }}
                
                .content-body {{
                    font-size: 1.1rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="blog-container">
            <header class="blog-header">
                <h1 class="blog-title">{kwargs['title']}</h1>
                <div class="blog-meta">
                    <div class="meta-item">
                        <span>📅</span>
                        <span>{kwargs['publish_date']}</span>
                    </div>
                    <div class="meta-item">
                        <span>⏱️</span>
                        <span>{kwargs['reading_time']} min read</span>
                    </div>
                    <div class="meta-item">
                        <span>👤</span>
                        <span>By Content Team</span>
                    </div>
                </div>
            </header>
            
            {f'<img src="{kwargs["featured_image_url"]}" alt="Featured image for {kwargs["title"]}" class="featured-image">' if kwargs["featured_image_url"] else ""}
            
            <main class="blog-content">
                <div class="intro-section">
                    <p>{kwargs['meta_description']}</p>
                </div>
                
                <article class="content-body">
                    {kwargs['enhanced_content']}
                </article>
                
                {kwargs['screenshot_section']}
                {kwargs['cta_section']}
            </main>
        </div>
    </body>
    </html>"""
    # ================= CONTENT ENHANCEMENT METHODS ================= #
    
    async def _enhance_content_structure(self, content: str) -> str:
        """Enhance content with proper HTML structure and formatting."""
        try:
            # Split content into paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            enhanced_paragraphs = []
            
            for i, paragraph in enumerate(paragraphs):
                # Detect and format headings
                if len(paragraph.split()) <= 10 and not paragraph.endswith('.'):
                    # Likely a heading
                    if i == 0:
                        enhanced_paragraphs.append(f"<h1>{paragraph}</h1>")
                    else:
                        enhanced_paragraphs.append(f"<h2>{paragraph}</h2>")
                else:
                    # Regular paragraph
                    # Check for list indicators
                    if any(paragraph.startswith(marker) for marker in ['•', '-', '*', '1.', '2.', '3.']):
                        # Convert to proper list
                        list_items = paragraph.split('\n')
                        list_html = "<ul>"
                        for item in list_items:
                            clean_item = re.sub(r'^[•\-\*]\s*', '', item.strip())
                            if clean_item:
                                list_html += f"<li>{clean_item}</li>"
                        list_html += "</ul>"
                        enhanced_paragraphs.append(list_html)
                    else:
                        # Regular paragraph with emphasis detection
                        enhanced_paragraph = self._add_emphasis_formatting(paragraph)
                        enhanced_paragraphs.append(f"<p>{enhanced_paragraph}</p>")
            
            return '\n\n'.join(enhanced_paragraphs)
            
        except Exception as e:
            logger.error(f"Error enhancing content structure: {str(e)}")
            return f"<p>{content}</p>"
    
    def _add_emphasis_formatting(self, text: str) -> str:
        """Add emphasis formatting to text."""
        # Bold for words in quotes or after colons
        text = re.sub(r'"([^"]+)"', r'<strong>\1</strong>', text)
        text = re.sub(r':\s*([A-Z][^.!?]*)', r': <strong>\1</strong>', text)
        
        # Italic for emphasis words
        emphasis_words = ['important', 'note', 'remember', 'key', 'crucial']
        for word in emphasis_words:
            text = re.sub(f'\\b{word}\\b', f'<em>{word}</em>', text, flags=re.IGNORECASE)
        
        return text

    def _create_intro_section(self, title: str, description: str) -> str:
        """Create an engaging introduction section."""
        return f"""
        <div class="intro-section">
            <p>{description}</p>
        </div>
        """

    def _create_screenshot_section(self, screenshot_url: str, website_url: str) -> str:
        """Create website screenshot section."""
        return f"""
        <div class="screenshot-section">
            <h2>📸 Website Preview</h2>
            <img src="{screenshot_url}" alt="Screenshot of {website_url}" class="screenshot-image">
            <p style="text-align: center; margin-top: 1rem; color: #718096;">
                <small>Preview of the website we analyzed</small>
            </p>
        </div>
        """

    def _create_cta_section(self, website_url: str, title: str) -> str:
        """Create call-to-action section."""
        if not website_url or website_url == "#":
            return ""
            
        return f"""
        <div class="cta-section">
            <h2 class="cta-title">🚀 Ready to Explore?</h2>
            <p class="cta-text">
                Visit the website we analyzed in this article and see these insights in action!
            </p>
            <a href="{website_url}" target="_blank" rel="noopener noreferrer" class="cta-button">
                Visit Website →
            </a>
        </div>
        """

    

    # ================= UTILITY METHODS ================= #
    
    async def capture_screenshot(self, url: str) -> Optional[str]:
        """Capture website screenshot using external service."""
        try:
            if not url or not url.startswith(('http://', 'https://')):
                return None
                
            async with httpx.AsyncClient(timeout=30) as client:
                # Using a screenshot service (replace with your actual service)
                screenshot_api_url = f"{settings.SCREENSHOT_SERVICE_URL}/screenshot"
                payload = {
                    "url": url,
                    "width": 1200,
                    "height": 800,
                    "format": "png",
                    "full_page": False
                }
                
                response = await client.post(screenshot_api_url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("screenshot_url")
                    
        except Exception as e:
            logger.error(f"Failed to capture screenshot for {url}: {str(e)}")
            
        return None

    @staticmethod
    def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
        """Calculate estimated reading time."""
        word_count = len(content.split())
        return max(1, round(word_count / words_per_minute))

    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL-friendly slug."""
        # Normalize unicode characters
        title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
        # Convert to lowercase and replace non-alphanumeric with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())
        # Clean up hyphens
        slug = re.sub(r'^-+|-+$', '', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug

    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Basic HTML sanitization."""
        # Remove script tags and their content
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove on* event attributes
        html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        html_content = re.sub(r'javascript:', '', html_content, flags=re.IGNORECASE)
        
        return html_content

    @staticmethod
    def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content."""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'will', 'can',
            'should', 'would', 'could', 'have', 'has', 'had', 'been', 'being',
            'they', 'them', 'their', 'there', 'where', 'when', 'what', 'why',
            'how', 'which', 'who', 'whom', 'whose', 'from', 'into', 'onto',
            'upon', 'about', 'above', 'below', 'over', 'under', 'between'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(max_keywords)]

    # ================= LEGACY SUPPORT METHODS ================= #
    
    @staticmethod
    def format_content_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format content plan for compatibility."""
        try:
            return {
                "title": plan_data.get("title", ""),
                "strategy_id": plan_data.get("strategy_id", ""),
                "scheduled_at": plan_data.get("scheduled_at", datetime.utcnow().isoformat()),
                "status": plan_data.get("status", "pending"),
                "headlines": plan_data.get("headlines", []),
                "user_id": plan_data.get("user_id", ""),
            }
        except Exception as e:
            logger.error(f"Error formatting content plan: {str(e)}")
            raise FormatterError(detail=str(e), operation="format_content_plan")

    async def format_article_for_pipeline(self, article_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Format article for pipeline processing."""
        try:
            formatted_article = {
                "title": article_data.get("title", ""),
                "slug": self.generate_slug(article_data.get("title", "")),
                "body": article_data.get("body", ""),
                "meta_title": article_data.get("meta_title", article_data.get("title", "")),
                "meta_description": article_data.get("meta_description", ""),
                "keywords": article_data.get("keywords", []),
                "user_id": user_id,
                "created_at": article_data.get("created_at", datetime.utcnow().isoformat()),
                "status": "formatted"
            }

            # Store in Supabase
            response = await supabase_client.table("articles").insert(formatted_article).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise FormatterError(detail="Failed to store formatted article", operation="format_article_for_pipeline")

        except Exception as e:
            logger.error(f"Error formatting article for pipeline: {str(e)}")
            raise FormatterError(detail=str(e), operation="format_article_for_pipeline")


# Create singleton instance
content_helper = ContentHelper()


