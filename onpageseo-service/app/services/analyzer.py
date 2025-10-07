# onpageseo-service/app/services/analyzer.py
from typing import Dict, List, Optional
import logging
from datetime import datetime
from shared_models.models import (
    PageSEOData,
    SEOAuditResult,
    SEOIssue,
    SEOIssueLevel,
    ContentMetrics,
    HeadingStructure,
    TaskStatus,
    MetaTag,
    LinkTag,
    ImageTag,
    SchemaMarkup,
)
from uuid import uuid4
import time  # For request timing
import httpx
from ..utils.parsers import HTMLParser
from ..utils.validators import SEOValidator
from ..utils.scorer import SEOScorer
from ..clients.supabase_client import supabase_client
from collections import defaultdict
import asyncio
from httpx import AsyncClient, URL, HTTPStatusError, HTTPError
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

TABLE_NAME = "seo_versions"


logger = logging.getLogger(__name__)

_url_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class SEOAnalyzer:
    """Main SEO analysis service - parses, validates, and scores pages"""

    def __init__(self):
        self.parser = HTMLParser()
        self.validator = SEOValidator()
        self.scorer = SEOScorer()

    async def analyze(
        self,
        url: Optional[str] = None,
        html_content: Optional[str] = None,
        task_id: Optional[str] = None,  # ✅ Add task_id parameter
    ) -> SEOAuditResult:
        """
        Analyze page with optional URL fetching
        """
        if url and not html_content:
            html_content = await self._fetch_url_content(url)

        if not html_content:
            raise ValueError("Either url or html_content must be provided")

        # Continue with existing analysis logic
        return await self.analyze_page(url, html_content, task_id=task_id)



    async def _fetch_url_content(self, url: str, max_redirects: int = 10) -> str:
        """
        Fetch URL content with full logging and robust redirect handling.
        Returns HTML content as a string.
        Raises HTTPError if request fails or too many redirects.
        Heavy logging includes: request/response headers, status, timing, content length, and redirect chain.
        """
        redirect_chain = []
        current_url = url
        redirect_count = 0

        headers = {
            "User-Agent": "MangoSEO-Bot/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }

        async with AsyncClient(timeout=15, follow_redirects=False) as client:
            while redirect_count <= max_redirects:
                start_time = time.time()
                logger.info(f"[Fetch Attempt] URL: {current_url} (Redirect count: {redirect_count})")
                logger.info(f"[Request Headers] {headers}")
                try:
                    response = await client.get(current_url, headers=headers)
                    elapsed = time.time() - start_time
                    logger.info(
                        f"[Response] Status code: {response.status_code} URL: {current_url} "
                        f"| Content-Length: {len(response.content)} | Time: {elapsed:.2f}s"
                    )

                    redirect_chain.append((response.status_code, current_url))

                    # Check if response is a redirect
                    if response.status_code in [301, 302, 303, 307, 308] or response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise HTTPError(f"Redirect without Location header at {current_url}")

                        try:
                            current_url = urljoin(str(response.url), location)
                            logger.info(f"[Redirect] {redirect_count + 1}: {redirect_chain[-1][1]} -> {current_url}")
                        except Exception as e:
                            logger.exception(f"[Redirect URL Parsing Failed] location={location} base={response.url}: {e}")
                            raise

                        redirect_count += 1

                        if any(url == current_url for _, url in redirect_chain[:-1]):
                            raise HTTPError(f"Redirect loop detected at {current_url}")

                        continue

                    # Success - non-redirect response
                    response.raise_for_status()
                    logger.info(f"[Success] Final URL reached after {len(redirect_chain)} redirects: {response.url}")
                    logger.debug(f"[Response Headers] {response.headers}")
                    return response.text

                except HTTPStatusError as e:
                    logger.warning(f"[HTTPStatusError] URL: {current_url} Status: {e.response.status_code}")
                    if e.response.status_code in [301, 302, 303, 307, 308]:
                        location = e.response.headers.get("location")
                        if location:
                            try:
                                current_url = urljoin(str(e.response.url), location)
                                redirect_count += 1
                                logger.info(f"[Redirect from exception] {redirect_count}: → {current_url}")
                                continue
                            except Exception as join_error:
                                logger.error(f"[URL join error] {join_error}")
                    raise
                except HTTPError as e:
                    logger.exception(f"[HTTPError] Failed fetching URL {current_url}: {e}")
                    raise
                except Exception as e:
                    logger.exception(f"[Unexpected Error] Fetching URL {current_url}: {e}")
                    raise

        raise HTTPError(f"Too many redirects ({redirect_count}) for URL: {url}. Redirect chain: {redirect_chain}")

    
    # Updated:
    async def analyze_page(
        self,
        url: str,
        html_content: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> SEOAuditResult:
        """
        Comprehensive SEO analysis of a web page
        Does NOT call AI agents - only rule-based analysis
        """
        try:
            if task_id:
                await self._update_task_status(
                    task_id, TaskStatus.PROCESSING, "Starting SEO analysis"
                )

            # Parse HTML content

            # Extract all page data
            page_data = await self._extract_page_data(url, html_content)

            # Run validations and find issues
            issues = await self._validate_page(page_data)

            # Calculate scores
            overall_score = self.scorer.calculate_seo_score(issues)

            if task_id:
                await self._update_task_status(
                    task_id, TaskStatus.COMPLETED, "SEO analysis completed successfully"
                )

            # --- Decide AI triggers based on analysis ---
            ai_triggers = []

            # Content quality trigger
            if page_data.content_metrics and page_data.content_metrics.content_quality_score < 0.6:
                ai_triggers.append("content_quality")

            # Schema missing or invalid trigger
            if not page_data.schema_markup or any(s.validation_errors for s in page_data.schema_markup):
                ai_triggers.append("schema_missing")

            # Thin content trigger
            if any(issue.type == "thin_content" for issue in issues):
                ai_triggers.append("thin_content")

            # Missing keyword trigger
            if not page_data.extracted_keywords:
                ai_triggers.append("keyword_research")

            # Performance / mobile / security triggers
            if not page_data.performance:
                ai_triggers.append("performance_audit")
            if not page_data.mobile:
                ai_triggers.append("mobile_readiness")
            if not page_data.security:
                ai_triggers.append("security_audit")


            return SEOAuditResult(
                url=url or "unknown",
                url_id=self._generate_url_id(url),  # Add this!
                timestamp=datetime.now(),
                overall_score=overall_score,
                category_scores=self._calculate_category_scores(issues),
                issues=[
                    issue
                    for issue in issues
                    if issue.level in [SEOIssueLevel.CRITICAL, SEOIssueLevel.WARNING]
                ],
                warnings=[
                    issue for issue in issues if issue.level == SEOIssueLevel.INFO
                ],
                recommendations=[],
                passed_checks=self._get_passed_checks(issues),
                audit_version="1.0",
                # ✅ Now populate new fields
                metrics=page_data.content_metrics,
                analyzer_context={
                    "headings": page_data.headings.__dict__,
                    "schema": page_data.schema_markup,
                    "extracted_keywords": page_data.extracted_keywords,
                },
                    page_data=page_data,  # <-- Add this line here
                    ai_triggers=ai_triggers,  # ✅ NEW FIELD
                    extracted_keywords=page_data.extracted_keywords,  # ✅ propagate here too
                    industry=None  # (later we can enrich with classifier)

            )

        except Exception as e:
            if task_id:
                await self._update_task_status(
                    task_id, TaskStatus.FAILED, f"SEO analysis failed: {str(e)}"
                )
            logger.error(f"Page analysis failed for {url}: {str(e)}")
            raise

    async def _extract_page_data(self, url: str, html_content: str) -> PageSEOData:
        """Extract all SEO-relevant data from page using orchestrator"""

        extracted = self.parser.extract_all(html_content, url)

        # Convert dict → models
        meta_tags = [
            MetaTag(name=k, content=v) for k, v in extracted["meta_tags"].items()
        ]
        images = [ImageTag(**img) for img in extracted["images"]]
        links = []
        for category, link_list in extracted["links"].items():
            for link_data in link_list:
                try:
                    if isinstance(link_data, dict):
                        links.append(LinkTag(**link_data))
                    else:
                        link_dict = {
                            "url": link_data[0] if len(link_data) > 0 else "",
                            "anchor_text": link_data[1] if len(link_data) > 1 else "",
                            "nofollow": False,
                            "title": "",
                            "is_internal": False,
                            "is_broken": False,
                            "suggested_anchor": None,
                            "link_equity": 1.0,
                            "rel": [],
                        }
                        links.append(LinkTag(**link_dict))
                except Exception as e:
                    logger.warning(f"Skipping bad link: {link_data} ({e})")

        schema_markup = []
        for schema in extracted["schema_markup"]:
            try:
                schema_markup.append(SchemaMarkup(**schema))
            except Exception as e:
                logger.warning(f"Skipping bad schema: {schema} ({e})")

        return PageSEOData(
            id=self._generate_url_id(url),  # use url_id string, not uuid4()
            url=url,
            title=extracted["title"],
            meta_tags=meta_tags,
            headings=HeadingStructure(**extracted["headings"]),
            images=images,
            links=links,
            schema_markup=schema_markup,
            content_metrics=ContentMetrics(**extracted["content_metrics"]),
            content_text=extracted["content_text"],
            extracted_keywords=extracted["keywords"],
            canonical_url=extracted["canonical_url"],
            language=extracted["lang_info"].get("lang"),
            charset=extracted["lang_info"].get("charset"),
            viewport=extracted.get("viewport"),  # add if included in extract_all
        )

    async def _validate_page(self, page_data: PageSEOData) -> List[SEOIssue]:
        """Run all validations on page data"""
        issues = []

        # --- Existing validator calls ---
        issues.extend(self.validator.validate_all(page_data))

        # Run all scorer checks (orchestrator handles title, headings, images, content)
        issues.extend(self.scorer.analyze_all(page_data))
        return issues

    def _calculate_category_scores(self, issues: List[SEOIssue]) -> Dict[str, float]:
        """Calculate scores for each SEO category"""
        categories = {
            "technical": [
                issue
                for issue in issues
                if "meta" in issue.type or "canonical" in issue.type
            ],
            "content": [issue for issue in issues if "content" in issue.type],
            "images": [issue for issue in issues if "alt" in issue.type],
            "headings": [
                issue
                for issue in issues
                if "h1" in issue.type or "heading" in issue.type
            ],
            "links": [issue for issue in issues if "link" in issue.type],
        }

        return {
            category: self.scorer.calculate_seo_score(category_issues, 100)
            for category, category_issues in categories.items()
        }

    def _get_passed_checks(self, issues: List[SEOIssue]) -> List[str]:
        """Get list of checks that passed, properly mapped to validator issue types"""
        failed_types = {issue.type for issue in issues}
        passed_checks = []

        # Title check
        if not any(
            t in failed_types
            for t in ["title_missing", "title_too_short", "title_too_long"]
        ):
            passed_checks.append("title_present")

        # Meta description check
        if not any(
            t in failed_types
            for t in [
                "meta_description_missing",
                "meta_description_too_short",
                "meta_description_too_long",
            ]
        ):
            passed_checks.append("meta_description_present")

        # H1 heading check
        if not any(t in failed_types for t in ["missing_h1", "multiple_h1"]):
            passed_checks.append("h1_present")

        # Image alt text check
        if not any(t in failed_types for t in ["missing_alt_text", "empty_alt_text"]):
            passed_checks.append("images_have_alt")

        # Content length check
        if not any(t in failed_types for t in ["thin_content", "content_too_long"]):
            passed_checks.append("content_sufficient")

        # Schema markup check
        if not any(t in failed_types for t in ["no_schema_markup"]):
            passed_checks.append("schema_present")

        # Canonical URL check
        if not any(
            t in failed_types for t in ["missing_canonical", "mismatched_canonical"]
        ):
            passed_checks.append("canonical_present")

        # Language declaration check
        if not any(t in failed_types for t in ["missing_language"]):
            passed_checks.append("language_declared")

        return passed_checks

    def _extract_viewport(self, soup) -> Optional[str]:
        """Extract viewport meta tag"""
        viewport = soup.find("meta", attrs={"name": "viewport"})
        return viewport.get("content") if viewport else None

    async def discover_sitemaps(self, base_url: str) -> List[str]:
        """Find all sitemaps for a website"""
        sitemap_urls = []

        # Check common sitemap locations
        common_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap.php",
            "/sitemap.txt",
            "/sitemap.xml.gz",
            "/robots.txt",
        ]

        for path in common_paths:
            try:
                full_url = f"{base_url.rstrip('/')}{path}"
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(full_url)
                    if response.status_code == 200:
                        if path == "/robots.txt":
                            # Extract sitemap from robots.txt
                            sitemap_urls.extend(
                                self._parse_robots_txt(response.text, base_url)
                            )
                        else:
                            sitemap_urls.extend(full_url)
            except:
                continue

        return list(set(sitemap_urls))

    def _parse_robots_txt(self, content: str, base_url: str) -> List[str]:
        """Extract sitemap URLs from robots.txt"""
        sitemaps = []
        for line in content.split("\n"):
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                sitemap_url = line[8:].strip()
                if sitemap_url.startswith("/"):
                    sitemap_url = f"{base_url.rstrip('/')}{sitemap_url}"
                sitemaps.extend(sitemap_url)
        return sitemaps

    def _generate_url_id(self, url: str) -> str:
        """Generate consistent URL ID for database"""
        import hashlib

        return hashlib.md5(url.encode()).hexdigest()

    async def _update_task_status(
        self, task_id: str, status: TaskStatus, message: str = ""
    ):
        """Update task status in Supabase"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now().isoformat(),
            }
            if message:
                update_data["progress_message"] = message
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                update_data["completed_at"] = datetime.now().isoformat()

            # ✅ Corrected Supabase usage
            qb = await supabase_client.from_table("tasks")
            qb = qb.update(update_data).eq("id", task_id)
            await qb.execute()

            logger.info(f"[Task {task_id}] Status updated to {status.value}")
        except Exception as e:
            logger.error(f"[Task {task_id}] Failed to update task status: {str(e)}")
