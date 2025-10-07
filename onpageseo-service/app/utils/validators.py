# onpageseo-service/app/utils/validators.py
from typing import Dict, List, Optional, Tuple, Set
import re
from urllib.parse import urlparse
from datetime import datetime
import logging
from shared_models.models import SEOIssue, SEOIssueLevel, PageSEOData
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SEOValidator:
    """SEO validation utilities - focuses on rule-based validation without analysis logic"""

    # Validation patterns and rules
    URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{10,}$")

    @staticmethod
    def validate_url(url: str) -> Optional[SEOIssue]:
        """Validate URL format and return SEOIssue if invalid"""
        if not isinstance(url, str):
            return SEOIssue(
                type="url_invalid_type",
                level=SEOIssueLevel.CRITICAL,
                message="URL must be a string",
                element="<url>",
                recommendation="Provide a valid URL string",
                weight=10.0,
            )

        if not url:
            return SEOIssue(
                type="url_missing",
                level=SEOIssueLevel.CRITICAL,
                message="URL is empty",
                element="<url>",
                recommendation="Provide a valid URL",
                weight=10.0,
            )

        if not SEOValidator.URL_PATTERN.match(url):
            return SEOIssue(
                type="url_invalid_format",
                level=SEOIssueLevel.CRITICAL,
                message="Invalid URL format",
                element="<url>",
                recommendation="Fix URL format (must start with http/https)",
                weight=8.0,
            )

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return SEOIssue(
                    type="url_missing_domain",
                    level=SEOIssueLevel.CRITICAL,
                    message="Missing domain in URL",
                    element="<url>",
                    recommendation="Provide a full domain in the URL",
                    weight=8.0,
                )
            return None  # ✅ valid URL
        except:
            return SEOIssue(
                type="url_malformed",
                level=SEOIssueLevel.CRITICAL,
                message="Malformed URL",
                element="<url>",
                recommendation="Check and fix URL structure",
                weight=8.0,
            )

    @staticmethod
    def validate_meta_tag_length(
        content: str, tag_type: str, min_len: int, max_len: int
    ) -> Optional[SEOIssue]:
        """Validate meta tag length and return issue if invalid"""
        if not isinstance(content, str):
            content = str(content)

        if not content:
            return SEOIssue(
                type=f"{tag_type}_missing",
                level=(
                    SEOIssueLevel.CRITICAL
                    if tag_type == "title"
                    else SEOIssueLevel.WARNING
                ),
                message=f"Missing {tag_type}",
                element=f"<{tag_type}>",
                recommendation=f"Add a {tag_type}",
                weight=10.0 if tag_type == "title" else 8.0,
            )

        length = len(content)
        if length < min_len:
            return SEOIssue(
                type=f"{tag_type}_too_short",
                level=SEOIssueLevel.WARNING,
                message=f"{tag_type.capitalize()} too short ({length} chars, minimum {min_len})",
                element=f"<{tag_type}>",
                recommendation=f"Expand {tag_type} to at least {min_len} characters",
                weight=3.0 if tag_type == "title" else 2.0,
            )
        elif length > max_len:
            return SEOIssue(
                type=f"{tag_type}_too_long",
                level=SEOIssueLevel.WARNING,
                message=f"{tag_type.capitalize()} too long ({length} chars, maximum {max_len})",
                element=f"<{tag_type}>",
                recommendation=f"Shorten {tag_type} to maximum {max_len} characters",
                weight=2.0 if tag_type == "title" else 1.5,
            )

        return None

    @staticmethod
    def validate_heading_structure(headings: Dict[str, List[str]]) -> List[SEOIssue]:
        """Validate heading structure without analysis logic"""
        if not headings or not isinstance(headings, dict):
            return []

        issues = []
        h1_count = len(headings.get("h1", []))

        if h1_count == 0:
            issues.append(
                SEOIssue(
                    type="missing_h1",
                    level=SEOIssueLevel.CRITICAL,
                    message="No H1 heading found",
                    element="<h1>",
                    recommendation="Add a single H1 heading describing the page content",
                    weight=8.0,
                )
            )
        elif h1_count > 1:
            issues.append(
                SEOIssue(
                    type="multiple_h1",
                    level=SEOIssueLevel.WARNING,
                    message=f"Multiple H1 headings found ({h1_count})",
                    element="<h1>",
                    recommendation="Use only one H1 heading per page",
                    weight=6.0,
                )
            )

        return issues

    @staticmethod
    def validate_image_alt_text(images: List[Dict]) -> List[SEOIssue]:
        """Validate image alt text attributes"""
        issues = []

        images = images or []
        if not isinstance(images, list):
            return []

        for i, image in enumerate(images):
            alt_text = image.get("alt", "")
            src = image.get("src", "")

            if not alt_text and src:  # Missing alt text for actual images
                issues.append(
                    SEOIssue(
                        type="missing_alt_text",
                        level=SEOIssueLevel.WARNING,
                        message=f"Image missing alt text: {src[:50]}...",
                        element="<img>",
                        recommendation="Add descriptive alt text for accessibility and SEO",
                        weight=4.0,
                    )
                )
            elif alt_text == "":  # Empty alt text
                issues.append(
                    SEOIssue(
                        type="empty_alt_text",
                        level=SEOIssueLevel.INFO,
                        message=f"Image has empty alt text: {src[:50]}...",
                        element="<img>",
                        recommendation="Either remove alt attribute or add meaningful text",
                        weight=2.0,
                    )
                )

        return issues

    @staticmethod
    def validate_internal_links(links: List[Dict], base_domain: str) -> List[SEOIssue]:
        """Validate internal links structure"""

        links = links or []
        if not isinstance(links, list) or not isinstance(base_domain, str):
            return []

        issues = []
        internal_links = [
            link
            for link in links
            if SEOValidator._is_internal_link(link.get("url", ""), base_domain)
        ]

        if len(internal_links) < 5:  # Minimum internal links recommendation
            issues.append(
                SEOIssue(
                    type="few_internal_links",
                    level=SEOIssueLevel.INFO,
                    message=f"Only {len(internal_links)} internal links found",
                    element="<a>",
                    recommendation="Add more internal links to improve site structure",
                    weight=2.0,
                )
            )

        return issues

    @staticmethod
    def validate_schema_markup(schema_data: List[Dict]) -> List[SEOIssue]:
        """Validate schema.org markup"""
        issues = []

        schema_data = schema_data or []
        if not isinstance(schema_data, list):
            return []

        if not schema_data:
            issues.append(
                SEOIssue(
                    type="no_schema_markup",
                    level=SEOIssueLevel.INFO,
                    message="No schema.org markup found",
                    element="<script type='application/ld+json'>",
                    recommendation="Add structured data to improve search visibility",
                    weight=3.0,
                )
            )

        return issues

    @staticmethod
    def validate_content_length(word_count: int) -> Optional[SEOIssue]:
        """Validate content length"""
        if not isinstance(word_count, (int, float)):
            word_count = 0

        if word_count < 300:
            return SEOIssue(
                type="thin_content",
                level=SEOIssueLevel.WARNING,
                message=f"Content is too short ({word_count} words)",
                element="body content",
                recommendation="Add more substantive content to the page",
                weight=7.0,
            )
        elif word_count > 2500:
            return SEOIssue(
                type="content_too_long",
                level=SEOIssueLevel.INFO,
                message=f"Content is very long ({word_count} words)",
                element="body content",
                recommendation="Consider breaking into multiple pages or adding pagination",
                weight=1.0,
            )

        return None

    @staticmethod
    def validate_canonical_url(
        canonical_url: Optional[str], current_url: str
    ) -> Optional[SEOIssue]:
        """Validate canonical URL"""
        canonical_url = canonical_url or ""
        current_url = current_url or ""

        if not canonical_url:
            return SEOIssue(
                type="missing_canonical",
                level=SEOIssueLevel.WARNING,
                message="Missing canonical URL",
                element="<link rel='canonical'>",
                recommendation="Add canonical URL to avoid duplicate content issues",
                weight=4.0,
            )

        if canonical_url != current_url:
            return SEOIssue(
                type="mismatched_canonical",
                level=SEOIssueLevel.INFO,
                message=f"Canonical URL differs from current URL",
                element="<link rel='canonical'>",
                recommendation="Ensure canonical URL matches the current page URL",
                weight=2.0,
            )

        return None

    @staticmethod
    def validate_language_attributes(
        html_lang: Optional[str], content_language: Optional[str]
    ) -> Optional[SEOIssue]:
        """Validate language attributes"""
        html_lang = html_lang or ""
        content_language = content_language or ""

        if not html_lang and not content_language:
            return SEOIssue(
                type="missing_language",
                level=SEOIssueLevel.INFO,
                message="Missing language declaration",
                element="<html lang> or <meta http-equiv='content-language'>",
                recommendation="Add language attribute to improve accessibility and SEO",
                weight=2.0,
            )

        return None

    @staticmethod
    def _is_internal_link(url: str, base_domain: str) -> bool:
        """Check if link is internal"""
        if not isinstance(url, str) or not isinstance(base_domain, str):
            return False

        if not url or not base_domain:
            return False

        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            return not parsed_url.netloc or parsed_url.netloc == parsed_base.netloc
        except:
            return False

    @staticmethod
    def validate_response_time(response_time_ms: float) -> Optional[SEOIssue]:
        """Validate page response time"""
        response_time_ms = float(response_time_ms or 0)

        if response_time_ms > 3000:  # 3 seconds
            return SEOIssue(
                type="slow_response",
                level=SEOIssueLevel.WARNING,
                message=f"Slow response time ({response_time_ms}ms)",
                element="server",
                recommendation="Optimize server performance and caching",
                weight=5.0,
            )
        elif response_time_ms > 1000:  # 1 second
            return SEOIssue(
                type="moderate_response",
                level=SEOIssueLevel.INFO,
                message=f"Moderate response time ({response_time_ms}ms)",
                element="server",
                recommendation="Consider performance optimizations",
                weight=2.0,
            )

        return None

    @staticmethod
    def validate_mobile_viewport(viewport_meta: Optional[str]) -> Optional[SEOIssue]:
        """Validate mobile viewport meta tag"""
        viewport_meta = viewport_meta or ""

        if not viewport_meta:
            return SEOIssue(
                type="missing_viewport",
                level=SEOIssueLevel.CRITICAL,
                message="Missing viewport meta tag for mobile",
                element="<meta name='viewport'>",
                recommendation="Add viewport meta tag: <meta name='viewport' content='width=device-width, initial-scale=1'>",
                weight=8.0,
            )

        return None

    @staticmethod
    def validate_hreflang_tags(hreflangs: List[Dict[str, str]]) -> List[SEOIssue]:
        """Ensure hreflang tags are present and correctly formatted"""
        hreflangs = hreflangs or []
        if not isinstance(hreflangs, list):
            return []

        issues = []
        if not hreflangs:
            issues.append(
                SEOIssue(
                    type="missing_hreflang",
                    level=SEOIssueLevel.INFO,
                    message="No hreflang tags found",
                    element="<link rel='alternate' hreflang>",
                    recommendation="Add hreflang tags for multilingual content",
                    weight=3.0,
                )
            )
            return issues

        for tag in hreflangs:
            lang = tag.get("hreflang")
            url = tag.get("url")
            if not lang or not re.match(r"^[a-z]{2}(-[A-Z]{2})?$", lang):
                issues.append(
                    SEOIssue(
                        type="invalid_hreflang",
                        level=SEOIssueLevel.WARNING,
                        message=f"Invalid hreflang format: {lang}",
                        element=f"<link hreflang='{lang}'>",
                        recommendation="Use ISO 639-1 codes or ISO 639-1-COUNTRY",
                        weight=2.5,
                    )
                )
            if not url:
                issues.append(
                    SEOIssue(
                        type="hreflang_missing_url",
                        level=SEOIssueLevel.WARNING,
                        message=f"Hreflang tag missing URL for lang {lang}",
                        element="<link hreflang>",
                        recommendation="Provide a valid URL for each hreflang tag",
                        weight=2.0,
                    )
                )
        return issues

    @staticmethod
    def validate_social_media_tags(social_meta: Dict[str, str]) -> List[SEOIssue]:
        """Ensure Open Graph and Twitter Card meta tags are present"""
        social_meta = social_meta or {}
        if not isinstance(social_meta, dict):
            return []

        issues = []
        required_og = ["og:title", "og:description", "og:image", "og:url"]
        required_twitter = ["twitter:card", "twitter:title", "twitter:description"]

        for tag in required_og:
            if tag not in social_meta or not social_meta[tag]:
                issues.append(
                    SEOIssue(
                        type=f"missing_{tag}",
                        level=SEOIssueLevel.INFO,
                        message=f"Missing Open Graph tag: {tag}",
                        element="<meta property='og:...'>",
                        recommendation=f"Add {tag} for social sharing optimization",
                        weight=2.5,
                    )
                )

        for tag in required_twitter:
            if tag not in social_meta or not social_meta[tag]:
                issues.append(
                    SEOIssue(
                        type=f"missing_{tag}",
                        level=SEOIssueLevel.INFO,
                        message=f"Missing Twitter Card tag: {tag}",
                        element="<meta name='twitter:...'>",
                        recommendation=f"Add {tag} for Twitter sharing optimization",
                        weight=2.5,
                    )
                )

        return issues

    @staticmethod
    def validate_external_links(links: List[Dict]) -> List[SEOIssue]:
        """Check for external links (no AI logic)"""
        links = links or []
        if not isinstance(links, list):
            return []

        issues = []
        for link in links:
            if not link.get("url"):
                continue
            if link.get("url").startswith("http"):
                # Could optionally mark if URL seems malformed
                parsed = urlparse(link["url"])
                if not parsed.netloc:
                    issues.append(
                        SEOIssue(
                            type="external_link_invalid",
                            level=SEOIssueLevel.WARNING,
                            message=f"Invalid external link: {link['url']}",
                            element="<a>",
                            recommendation="Fix external link URL",
                            weight=2.0,
                        )
                    )
        return issues

    @staticmethod
    def validate_indexability(soup: BeautifulSoup) -> List[SEOIssue]:
        """Check for robots meta tags and canonical vs noindex conflicts"""
        issues = []
        if not soup or not hasattr(soup, "find"):
            return []

        robots = soup.find("meta", attrs={"name": "robots"})
        if robots and "noindex" in robots.get("content", "").lower():
            issues.append(
                SEOIssue(
                    type="noindex_detected",
                    level=SEOIssueLevel.INFO,
                    message="Page has 'noindex' directive",
                    element="<meta name='robots'>",
                    recommendation="Remove 'noindex' if page should be indexed",
                    weight=3.0,
                )
            )
        return issues

    @staticmethod
    def validate_heading_lengths(
        headings: Dict[str, List[str]], max_length: int = 70
    ) -> List[SEOIssue]:
        """Warn if H1/H2/H3 headings are too long"""
        headings = headings or {}
        if not isinstance(headings, dict):
            return []

        issues = []
        for level in ["h1", "h2", "h3"]:
            for h in headings.get(level, []):
                if len(h) > max_length:
                    issues.append(
                        SEOIssue(
                            type=f"{level}_too_long",
                            level=SEOIssueLevel.WARNING,
                            message=f"{level.upper()} heading too long ({len(h)} chars): {h[:50]}...",
                            element=f"<{level}>",
                            recommendation=f"Keep {level.upper()} headings under {max_length} characters",
                            weight=2.0,
                        )
                    )
        return issues

    @classmethod
    def validate_all(cls, page_data: PageSEOData, soup: Optional[BeautifulSoup] = None) -> List[SEOIssue]:
        """
        Run all validator methods on the page data and return aggregated issues.
        """
        issues: List[SEOIssue] = []

        # --- URL ---
        url_issue = cls.validate_url(page_data.url)
        if url_issue:
            issues.append(url_issue)

        # --- Meta ---
        title_issue = cls.validate_meta_tag_length(page_data.title, "title", 50, 60)
        if title_issue:
            issues.append(title_issue)

        meta_description = next(
            (tag.content for tag in page_data.meta_tags if tag.name == "description"), ""
        )
        if meta_description:
            meta_issue = cls.validate_meta_tag_length(
                meta_description, "meta_description", 150, 160
            )
            if meta_issue:
                issues.append(meta_issue)

        # --- Headings ---
        issues.extend(cls.validate_heading_structure(page_data.headings.__dict__))
        issues.extend(cls.validate_heading_lengths(page_data.headings.__dict__))

        # --- Images ---
        issues.extend(cls.validate_image_alt_text([img.__dict__ for img in page_data.images]))

        # --- Links ---
        issues.extend(cls.validate_internal_links([link.__dict__ for link in page_data.links], page_data.url))
        issues.extend(cls.validate_external_links([link.__dict__ for link in page_data.links]))

        # --- Schema ---
        issues.extend(cls.validate_schema_markup([s.__dict__ for s in page_data.schema_markup]))

        # --- Content ---
        content_issue = cls.validate_content_length(int(page_data.content_metrics.word_count or 0))
        if content_issue:
            issues.append(content_issue)

        # --- Canonical & Language ---
        canonical_issue = cls.validate_canonical_url(page_data.canonical_url, page_data.url)
        if canonical_issue:
            issues.append(canonical_issue)

        language_issue = cls.validate_language_attributes(page_data.language, None)
        if language_issue:
            issues.append(language_issue)

        viewport_issue = cls.validate_mobile_viewport(page_data.viewport)
        if viewport_issue:
            issues.append(viewport_issue)

        # --- Optional fields ---
        hreflang_tags = getattr(page_data, "hreflang_tags", [])
        if hreflang_tags:
            issues.extend(cls.validate_hreflang_tags(hreflang_tags))

        if page_data.social_media_tags:
            issues.extend(cls.validate_social_media_tags(page_data.social_media_tags))

        if page_data.performance and getattr(page_data.performance, "response_time_ms", None):
            response_issue = cls.validate_response_time(page_data.performance.response_time_ms)
            if response_issue:
                issues.append(response_issue)

        # --- Indexability check ---
        if soup:
            issues.extend(cls.validate_indexability(soup))

        return issues
