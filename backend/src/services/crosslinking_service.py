# backend/src/services/crosslinking_service.py

import logging
import re
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from bs4 import BeautifulSoup

from ..clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)


@dataclass
class ArticleLink:
    id: str
    source_article_id: str
    target_article_id: str
    anchor_text: str
    target_url: str
    cms_type: str
    link_type: str
    enabled: bool
    priority_score: int
    created_date: datetime
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    position_index: Optional[int] = None


class CrossLinkingService:
    """
    Comprehensive cross-linking service with no AI dependency.
    Handles initial and comprehensive cross-linking between articles.
    """

    MAX_LINKS_PER_ARTICLE = 4
    LINK_PRIORITY_DAYS = 30
    MIN_RELEVANCE_SCORE = 0.3

    def __init__(self):
        self.supabase = supabase_client

    async def perform_initial_linking(
        self, blog_id: str, content: str, target_keyword: str, title: str
    ) -> str:
        """
        Perform initial cross-linking for a new article
        """
        try:
            # Get relevant existing posts
            relevant_posts = await self._find_relevant_articles(
                blog_id, target_keyword, title, mode="new"
            )


            if not relevant_posts:
                return content

            # Inject links using internal logic
            enhanced_content = await self._inject_links_internal(
                content, relevant_posts, blog_id, target_keyword, title
            )


            return enhanced_content

        except Exception as e:
            logger.error(f"Initial linking failed: {str(e)}")
            return content

            
            
            # Instead, call scheduler_service.schedule_task("crosslink_blogs", args=[blog_id], countdown=<optional>)
            
    async def initial_link_and_update(self, article_id: str):
        """
        Perform initial linking for a new article and update both articles and blog_results tables.
        """
        article = await self._get_article(article_id)
        if not article:
            logger.error(f"Article {article_id} not found for initial linking.")
            return

        # Fetch target_keyword from topics if available
        topic = None
        if article.get("topic_id"):
            topic = await self.supabase.fetch_one("topics", {"id": article["topic_id"]})
        target_keyword = topic.get("target_keyword", "") if topic else article.get("target_keyword", "")

        # Perform initial linking
        enhanced_content = await self.perform_initial_linking(
            article_id,
            article.get("final_content") or article.get("content", ""),
            target_keyword,
            article.get("title", "")
        )

        # Update articles table
        await self.supabase.update_table(
            "articles",
            {"id": article_id},
            {"final_content": enhanced_content, "updated_at": datetime.utcnow().isoformat()}
        )

        # Update blog_results table
        await self.supabase.update_table(
            "blog_results",
            {"id": article_id},
            {"final_content": enhanced_content, "updated_at": datetime.utcnow().isoformat()}
        )

        logger.info(f"Initial linking completed for article {article_id}")

    async def _perform_comprehensive_relinking(self, blog_id: str):
        """
        Perform comprehensive two-way relinking
        """
        try:
            # Get the article
            article = await self._get_article(blog_id)
            if not article:
                return

            # 1. Forward linking: Update links in this article
            await self._update_article_links(article)

            # 2. Backward linking: Update links in related articles pointing here
            await self._update_backward_links(article)



        except Exception as e:
            logger.error(f"Comprehensive relinking failed for {blog_id}: {str(e)}")

    async def _update_article_links(self, article: Dict):
        """
        Update links within a specific article
        """
        content = article.get("content", "")
        target_keyword = article.get("target_keyword", "")
        title = article.get("title", "")

        # Find newly relevant articles
        relevant_posts = await self._find_relevant_articles(
            article["id"], target_keyword, title, mode="general"
        )

        for relevant_article in relevant_posts:
            await self._add_article_link(
                article["id"],
                relevant_article["id"],
                relevant_article["title"],
                relevant_article.get("cms_type", "unknown"),
                content,
            )

        await self._disable_obsolete_links(article["id"], relevant_posts)


    async def _update_backward_links(self, article: Dict):
        """
        Update links in other articles pointing to this one
        """
        # Find articles that should link to this new article
        new_relevant = await self._find_relevant_articles(
            article["id"], article.get("target_keyword", ""), article.get("title", ""), mode="new"
        )

        for source_article in new_relevant:
            # Check if link already exists
            existing_link = await self._get_existing_link(
                source_article["id"], article["id"]
            )

            if not existing_link:
                await self._add_article_link(
                    source_article["id"],
                    article["id"],
                    article["title"],
                    article.get("cms_type", "unknown"),
                    source_article.get("content", ""),
                )

   
    def _calculate_relevance_score(
        self, post: Dict, target_keyword: str, title: str
    ) -> float:
        """
        Calculate relevance score using internal logic (no AI)
        """
        score = 0.0

        # Convert to lowercase for case-insensitive matching
        target_keyword_lower = target_keyword.lower()
        title_lower = title.lower()
        post_title_lower = post.get("title", "").lower()
        post_content_lower = post.get("content", "").lower()

        # Keyword in title (strong signal)
        if target_keyword_lower in post_title_lower:
            score += 0.4

        # Title similarity
        title_similarity = self._calculate_text_similarity(
            title_lower, post_title_lower
        )
        score += title_similarity * 0.3

        # Keyword in content
        if target_keyword_lower in post_content_lower:
            score += 0.2

        # Tag/category matching
        post_keywords = [str(k).lower() for k in (post.get("keywords") or [])]

        if target_keyword_lower in post_keywords: 
            score += 0.5 
        
        # Ensure the final score never exceeds 1.0
        score = min(score, 1.0)
        return score

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using word overlap
        """
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    async def _inject_links_internal(
        self,
        content: str,
        relevant_posts: List[Dict],
        source_article_id: str,
        target_keyword: str,
        title: str
    ) -> str:

        """
        Inject links using internal text matching logic
        """
        if not relevant_posts:
            return content

        # Remove existing links to avoid conflicts
        clean_content = self._remove_existing_links(content)

        injected_content = clean_content
        used_positions = set()

        for post in relevant_posts:
            anchor_text = post.get("title", "")
            # Prefer 'cms_url', fallback to 'website_url' from blog_results
            target_url = post.get("cms_url") or post.get("website_url") or ""


            if not anchor_text or not target_url:
                continue

            # Find best position to inject link
            best_position = self._find_best_injection_position(
                injected_content, anchor_text, used_positions
            )

            if best_position is not None:
                # Inject the link
                # Use BeautifulSoup to safely inject link 
                soup = BeautifulSoup(injected_content, "html.parser")
                for text_node in soup.find_all(text=True):
                    if anchor_text.lower() in text_node.lower():
                        new_text = str(text_node).replace(
                            anchor_text,
                            f'<a href="{target_url}" target="_blank" rel="noopener" class="internal-link">{anchor_text}</a>',
                            1
                        )
                        text_node.replace_with(BeautifulSoup(new_text, "html.parser"))
                        break  # Only inject once per post
                injected_content = str(soup)


                # Store the link in database
                relevance_score = self._calculate_relevance_score(post, target_keyword, title)
                await self._store_article_link(
                    source_article_id,
                    post["id"],
                    anchor_text,
                    target_url,
                    post.get("cms_type", "unknown"),
                    "initial",
                    best_position,
                    self._get_context(injected_content, best_position, anchor_text),
                    relevance_score=relevance_score,  # Pass it explicitly
                )

        return injected_content

    async def _remove_existing_links(self, content: str) -> str:
        soup = BeautifulSoup(content, "html.parser")
        for a in soup.find_all("a"):
            a.unwrap()
        return str(soup)


    def _find_best_injection_position(
        self, content: str, anchor_text: str, used_positions: set
    ) -> Optional[int]:
        """
        Find the best position to inject a link
        """
        occurrences = []

        for match in re.finditer(re.escape(anchor_text), content, re.IGNORECASE):
            pos = match.start()

            # Skip if position is already used or inside HTML tag
            if pos not in used_positions and not self._is_inside_html_tag(content, pos):
                # Score this occurrence based on context
                score = self._score_position_quality(content, pos, anchor_text)
                occurrences.append((score, pos))

        if not occurrences:
            return None

        # Return the highest scoring position
        return max(occurrences, key=lambda x: x[0])[1]

    def _is_inside_html_tag(self, content: str, position: int) -> bool:
        """
        Check if position is inside HTML tag using cumulative offsets
        """
        soup = BeautifulSoup(content, "html.parser")
        current_pos = 0
        for text_node in soup.find_all(text=True):
            start = current_pos
            end = start + len(text_node)
            if start <= position < end:
                return False  # inside a text node => safe
            current_pos = end
        return True  # not in a text node => inside HTML tag




    def _score_position_quality(
        self, content: str, position: int, anchor_text: str
    ) -> float:
        """
        Score the quality of a link position
        """
        score = 0.0
        context = self._get_text_context(content, position, 50)

        # Higher score for positions in paragraphs (not in headers, code, etc.)
        if not any(tag in context for tag in ["<h1", "<h2", "<h3", "<code", "<pre"]):
            score += 0.5

        # Higher score for positions not at very beginning/end
        if 100 < position < len(content) - 100:
            score += 0.3

        # Higher score for positions near relevant context
        if self._has_relevant_context(context, anchor_text):
            score += 0.2

        return score

    def _get_text_context(self, content: str, position: int, window: int) -> str:
        """Get text around the position"""
        start = max(0, position - window)
        end = min(len(content), position + window)
        return content[start:end]

    def _has_relevant_context(self, context: str, anchor_text: str) -> bool:
        """Check if context seems relevant for the anchor text"""
        # Simple heuristic: context should contain words related to the anchor
        anchor_words = set(anchor_text.lower().split())
        context_words = set(context.lower().split())
        return len(anchor_words.intersection(context_words)) > 0

    def _inject_link_at_position(
        self, content: str, position: int, anchor_text: str, target_url: str
    ) -> str:
        """
        Inject a link at a specific position
        """
        actual_text = content[position : position + len(anchor_text)]
        link_html = f'<a href="{target_url}" target="_blank" rel="noopener" class="internal-link">{actual_text}</a>'

        return content[:position] + link_html + content[position + len(anchor_text) :]

    def _get_context(
        self, content: str, position: int, anchor_text: str
    ) -> Dict[str, str]:
        """Get context before and after the link position"""
        context_before = content[max(0, position - 50) : position].strip()
        context_after = content[
            position + len(anchor_text) : position + len(anchor_text) + 50
        ].strip()

        return {"before": context_before, "after": context_after}

    async def _store_article_link(
        self,
        source_id: str,
        target_id: str,
        anchor_text: str,
        target_url: str,
        cms_type: str,
        link_type: str,
        position: int,
        context: Dict,
        relevance_score: float = 0.5,  # Added
    ):
        """
        Store a link in the database
        """
        # Check current link count and enforce limit
        active_count = await self._get_active_links_count(source_id)

        # New
        if active_count >= self.MAX_LINKS_PER_ARTICLE:
            # Only disable links of type 'initial' to preserve backward/forward links
            await self._disable_lowest_priority_link(source_id, allowed_types=['initial'])
             


        await self.supabase.insert_into("article_links", {
            "source_article_id": source_id,
            "target_article_id": target_id,
            "anchor_text": anchor_text,
            "target_url": target_url,
            "cms_type": cms_type,
            "link_type": link_type,
            "enabled": True,
            "priority_score": await self._calculate_priority_score({
                "relevance_score": relevance_score,
                "created_at": datetime.utcnow().isoformat()
            }),
            "position_index": position,
            "context_before": context.get("before"),
            "context_after": context.get("after"),
            "created_date": datetime.utcnow(),
        })


    async def _add_article_link(
        self,
        source_id: str,
        target_id: str,
        anchor_text: str,
        cms_type: str,
        content: str,
    ):
        """
        Add a new article link with proper context analysis
        """
        # Get target URL
        target_url = await self._get_article_url(target_id)
        if not target_url:
            return False

        # Find best position for the link
        best_position = self._find_best_injection_position(content, anchor_text, set())
        if best_position is None:
            return False

        # Store the link
        context = self._get_context(content, best_position, anchor_text)
        await self._store_article_link(
            source_id,
            target_id,
            anchor_text,
            target_url,
            cms_type,
            "initial",  # link_type
            best_position,
            context,
        )


        return True

    async def _get_active_links_count(self, blog_id: str) -> int:
        """Get count of active links for an article"""
        links = await self.supabase.fetch_all(
            "article_links",
            filters={"source_article_id": blog_id, "enabled": True},
            select="id"
        )
        return len(links)


    async def _disable_lowest_priority_link(self, blog_id: str, allowed_types: List[str] = None):
        """Disable the lowest priority link"""
        filters = {"source_article_id": blog_id, "enabled": True}
        if allowed_types:
            filters["link_type"] = {"in": allowed_types}
        links = await self.supabase.fetch_all(
            "article_links",
            filters=filters,
            select="id, priority_score, created_date"
        )
        if links:
            lowest = sorted(links, key=lambda x: (x.get("priority_score", 0), x.get("created_date", "")))[0]
            await self.supabase.update_table(
                "article_links",
                {"id": lowest["id"]},
                {"enabled": False, "updated_at": datetime.utcnow()}
            )


    async def _find_relevant_articles(
        self,
        exclude_blog_id: str,
        target_keyword: str,
        title: str,
        mode: str = "general"
    ) -> List[Dict]:
        """
        Find relevant articles using internal scoring.
        mode = general | new | source
        """
        try:
            # Get base article for user_id or publish date checks
            base_article = None
            if exclude_blog_id:
                base_article = await self._get_article(exclude_blog_id)

            # Always need user_id
            if not base_article or not base_article.get("user_id"):
                return []

            query_filters = {"user_id": base_article["user_id"], "status": "published"}
            posts = await self.supabase.fetch_all(
                "blog_results",
                filters=query_filters,
                select="id, title, content, keywords, cms_url, cms_type, published_at, target_keyword"
            )


            # Filter out the current article
            posts = [p for p in posts if p["id"] != exclude_blog_id]
            if not posts:
                return []

                        # Mode-specific filtering
            if mode == "new" and base_article.get("published_at"):
                posts = [
                    p for p in posts
                    if p.get("published_at") and p["published_at"] > base_article["published_at"]
                ]


            if mode == "source":
                # Target keyword/title from the base article
                target_keyword = base_article.get("target_keyword", target_keyword)
                title = base_article.get("title", title)

            scored_posts = []
            for post in posts:
                score = self._calculate_relevance_score(post, target_keyword, title)
                if score >= self.MIN_RELEVANCE_SCORE:
                    scored_posts.append((score, post))

            scored_posts.sort(key=lambda x: x[0], reverse=True)

            # Return top 5 by default
            return [post for score, post in scored_posts[:5]]

        except Exception as e:
            logger.error(f"Error finding relevant articles (mode={mode}): {str(e)}")
            return []

    async def _calculate_priority_score(self, link_data: dict) -> float:
        # simplified: just use recency if no relevance given
        recency_score = 1.0
        if "published_at" in link_data:
            created = datetime.fromisoformat(link_data["published_at"])
        elif "created_at" in link_data:
            created = datetime.fromisoformat(link_data["created_at"])
            days_old = max(0, (datetime.utcnow() - created).days)
            recency_score = 1.0 / (1 + days_old)

        relevance_score = link_data.get("relevance_score", 0.5)
        return 0.6 * relevance_score + 0.4 * recency_score


    async def _get_article_url(self, blog_id: str) -> Optional[str]:
        """Get URL for an article"""
        article = await self.supabase.fetch_one(
            "blog_results",
            {"id": blog_id},
            select="post_url"
        )
        return article.get("post_url") if article else None


    async def _get_article(self, blog_id: str) -> Optional[Dict]:
        """Get article by ID"""
        article = await self.supabase.fetch_one("blog_results", {"id": blog_id})
        return article


    async def _get_existing_link(
        self, source_id: str, target_id: str
    ) -> Optional[Dict]:
        """Check if link already exists"""
        link = await self.supabase.fetch_one(
            "article_links",
            {"source_article_id": source_id, "target_article_id": target_id}
        )
        return link


    async def _disable_obsolete_links(self, blog_id: str, new_relevant: List[Dict]):
        """Disable links that are no longer relevant"""
        # Get current active links
        
        # Problem: _disable_obsolete_links updates one row at a time.
        # Fix: Collect IDs and run one update.
        current_links = await self.supabase.fetch_all(
            "article_links",
            filters={"source_article_id": blog_id, "enabled": True},
            select="*"
        )

        if not current_links:
            return
 
            
        current_target_ids = {link["target_article_id"] for link in current_links}
    
        new_target_ids = {article["id"] for article in new_relevant}

        # Disable links that are not in the new relevant set
        obsolete_ids = current_target_ids - new_target_ids


        await self.supabase.update_table(
            "article_links",
            {
                "source_article_id": blog_id,
                "target_article_id": {"in": list(obsolete_ids)}
            },
            {"enabled": False, "updated_at": datetime.utcnow()}
        )

    async def relink_article(self, blog_id: str):
        """
        Public wrapper: perform full comprehensive relinking for a single article.
        """
        return await self._perform_comprehensive_relinking(blog_id)

    async def relink_all_articles(self, user_id: str = None):
        """
        Public wrapper: perform relinking for all published articles.
        If user_id is provided, scope only to that user.
        """
        filters = {"status": "published"}
        if user_id:
            filters["user_id"] = user_id

        blogs = await self.supabase.fetch_all("blog_results", filters=filters)
        results = []
        for blog in blogs:
            try:
                await self._perform_comprehensive_relinking(blog["id"])
                results.append({"id": blog["id"], "status": "success"})
            except Exception as e:
                logger.error(f"Relinking failed for {blog['id']}: {str(e)}")
                results.append({"id": blog["id"], "status": "failed", "error": str(e)})

        return results

cross_linking_service = CrossLinkingService()