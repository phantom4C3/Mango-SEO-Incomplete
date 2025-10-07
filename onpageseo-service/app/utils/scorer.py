# onpageseo-service/app/utils/scorer.py
from typing import Dict, List, Optional 
import logging
from .validators import SEOValidator
from shared_models.models import SEOIssue, SEOIssueLevel, PageSEOData
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SEOScorer:
    """SEO scoring engine with weighted issue-based scoring"""

    # Weight configurations (adjust based on SEO importance)
    WEIGHTS = {
        "title": {"missing": 10.0, "too_short": 3.0, "too_long": 2.0, "duplicate": 5.0},
        "meta_description": {"missing": 8.0, "too_short": 2.0, "too_long": 1.5},
        "headings": {"missing_h1": 8.0, "multiple_h1": 6.0, "poor_hierarchy": 3.0},
        "images": {"missing_alt": 4.0, "empty_alt": 2.0, "large_image": 1.5},
        "links": {"broken": 5.0, "nofollow_ratio": 2.0},
        "content": {
            "thin_content": 7.0,
            "low_readability": 3.0,
            "keyword_stuffing": 6.0,
        },
        "technical": {"missing_canonical": 4.0, "no_schema": 3.0, "slow_loading": 5.0},
    }

    # Optimal ranges for various SEO elements
    OPTIMAL_RANGES = {
        "title_length": (50, 60),  # Characters
        "meta_description_length": (150, 160),  # Characters
        "content_length": (300, 2500),  # Words
        "images_with_alt": (0.8, 1.0),  # Ratio (80-100%)
        "internal_links": (5, float("inf")),  # Minimum 5
        "heading_h1_count": (1, 1),  # Exactly 1 H1
        "readability_score": (60, 100),  # Flesch reading ease
    }

    @staticmethod
    def calculate_seo_score(issues: List[SEOIssue], max_score: float = 100.0) -> float:
        """
        Calculate overall SEO score based on issues found
        """
        if not issues:
            return max_score

        total_weight = 0.0
        penalty = 0.0

        for issue in issues:
            # Calculate penalty based on issue level and weight
            if issue.level == SEOIssueLevel.CRITICAL:
                penalty += issue.weight * 0.8  # 80% penalty for critical
            elif issue.level == SEOIssueLevel.WARNING:
                penalty += issue.weight * 0.4  # 40% penalty for warning
            elif issue.level == SEOIssueLevel.INFO:
                penalty += issue.weight * 0.1  # 10% penalty for info

            total_weight += issue.weight

        if total_weight == 0:
            return max_score

        # Normalize penalty and calculate score
        normalized_penalty = min(penalty / total_weight, 1.0)
        score = max_score * (1 - normalized_penalty)

        return round(score, 1)

    def analyze_title(self, title: str, page_url: str) -> List[SEOIssue]:
        issues = []

        if not title:
            title = ""
        if not page_url:
            page_url = ""


        # Use validator for basic checks
        validation_issue = SEOValidator.validate_meta_tag_length(title, "title", 50, 60)
        if validation_issue:
            issues.append(validation_issue)

        # Keep scoring-specific logic here
        if self._detect_keyword_stuffing(title):
            issues.append(
                SEOIssue(
                    type="title_keyword_stuffing",
                    level=SEOIssueLevel.WARNING,
                    message="Title appears to have keyword stuffing",
                    element="<title>",
                    recommendation="Use natural language with 1-2 primary keywords",
                    weight=self.WEIGHTS["content"]["keyword_stuffing"] * 0.5,
                )
            )

        return issues

    @staticmethod
    def analyze_headings(headings: Dict[str, List[str]]) -> List[SEOIssue]:
        """Analyze heading structure for SEO issues"""
        issues = []
        
        if not headings:
            headings = {level: [] for level in ["h1","h2","h3","h4","h5","h6"]}


        # Check heading hierarchy
        if not SEOScorer._has_proper_heading_hierarchy(headings):
            issues.append(
                SEOIssue(
                    type="poor_heading_hierarchy",
                    level=SEOIssueLevel.INFO,
                    message="Heading hierarchy could be improved",
                    element="<h1>-<h6>",
                    recommendation="Maintain proper heading order (H1 → H2 → H3, etc.)",
                    weight=SEOScorer.WEIGHTS["headings"]["poor_hierarchy"],
                )
            )

        return issues

    @staticmethod
    def analyze_images(images: List[Dict], total_images: int) -> List[SEOIssue]:
        """Analyze images for SEO issues"""
        issues = []

        images = images or []
        total_images = total_images or 0


        if total_images == 0:
            return issues

        # FIX: Actually use these variables
        images_with_alt = sum(1 for img in images if img.get("alt"))
        alt_ratio = images_with_alt / total_images

        min_ratio, max_ratio = SEOScorer.OPTIMAL_RANGES["images_with_alt"]

        if alt_ratio < min_ratio:
            issues.append(
                SEOIssue(
                    type="low_alt_text_coverage",
                    level=SEOIssueLevel.WARNING,
                    message=f"Only {images_with_alt}/{total_images} images have alt text ({alt_ratio:.0%})",
                    element="<img>",
                    recommendation="Add descriptive alt text to all images",
                    weight=SEOScorer.WEIGHTS["images"]["missing_alt"],
                )
            )

        # FIX: Actually use this variable
        empty_alt_count = sum(1 for img in images if img.get("alt") == "")
        if empty_alt_count > 0:
            issues.append(
                SEOIssue(
                    type="empty_alt_text",
                    level=SEOIssueLevel.INFO,
                    message=f"{empty_alt_count} images have empty alt text",
                    element="<img>",
                    recommendation="Either remove alt attribute or add meaningful text",
                    weight=SEOScorer.WEIGHTS["images"]["empty_alt"],
                )
            )

        return issues

    @staticmethod
    def analyze_content(content_metrics: Dict, text_content: str) -> List[SEOIssue]:
        """Analyze content for SEO issues"""
        issues = []

        content_metrics = content_metrics or {}
        text_content = text_content or ""


        # Check content length
        word_count = content_metrics.get("word_count", 0)
        min_words, max_words = SEOScorer.OPTIMAL_RANGES["content_length"]

        if word_count < min_words:
            issues.append(
                SEOIssue(
                    type="thin_content",
                    level=SEOIssueLevel.WARNING,
                    message=f"Content is too short ({word_count} words, minimum {min_words})",
                    element="body content",
                    recommendation="Add more substantive content to the page",
                    weight=SEOScorer.WEIGHTS["content"]["thin_content"],
                )
            )
        elif word_count > max_words:
            issues.append(
                SEOIssue(
                    type="content_too_long",
                    level=SEOIssueLevel.INFO,
                    message=f"Content is very long ({word_count} words)",
                    element="body content",
                    recommendation="Consider breaking into multiple pages or adding pagination",
                    weight=1.0,
                )
            )

        # Check readability (simplified)
        readability_score = SEOScorer._calculate_readability(text_content)
        min_read, max_read = SEOScorer.OPTIMAL_RANGES["readability_score"]

        if readability_score < min_read:
            issues.append(
                SEOIssue(
                    type="low_readability",
                    level=SEOIssueLevel.INFO,
                    message=f"Content may be difficult to read (score: {readability_score}/100)",
                    element="body content",
                    recommendation="Simplify language and shorten sentences",
                    weight=SEOScorer.WEIGHTS["content"]["low_readability"],
                )
            )

        # Check keyword stuffing
        if SEOScorer._detect_keyword_stuffing(text_content):
            issues.append(
                SEOIssue(
                    type="keyword_stuffing",
                    level=SEOIssueLevel.WARNING,
                    message="Content appears to have keyword stuffing",
                    element="body content",
                    recommendation="Use keywords naturally and focus on user value",
                    weight=SEOScorer.WEIGHTS["content"]["keyword_stuffing"],
                )
            )

        return issues

    @staticmethod
    def _has_proper_heading_hierarchy(headings: Dict[str, List[str]]) -> bool:
        """Check if headings follow proper hierarchy"""
        
        if not headings:
            return True


        levels = ["h1", "h2", "h3", "h4", "h5", "h6"]
        found_levels = [level for level in levels if headings.get(level)]

        # Ensure no gaps in hierarchy (e.g., h1 → h3 without h2)
        if len(found_levels) > 1:
            first_index = levels.index(found_levels[0])
            last_index = levels.index(found_levels[-1])
            expected_levels = levels[first_index : last_index + 1]
            return all(level in found_levels for level in expected_levels)

        return True

    @staticmethod
    def _calculate_readability(text: str) -> float:
        """
        Simplified Flesch reading ease score
        Higher score = easier to read
        """
        if not text:
            return 0.0

        words = text.split()
        sentences = text.count(".") + text.count("!") + text.count("?")

        if len(words) == 0 or sentences == 0:
            return 0.0

        avg_words_per_sentence = len(words) / sentences
        avg_syllables_per_word = SEOScorer._estimate_syllables_per_word(words)

        # Flesch reading ease formula
        score = (
            206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        )

        return max(0, min(100, score))

    @staticmethod
    def _estimate_syllables_per_word(words: List[str]) -> float:
        """Estimate syllables per word (simplified)"""
        if not words:
            return 0.0

        total_syllables = 0
        for word in words:
            # Simple syllable estimation
            word = word.lower()
            if len(word) <= 3:
                total_syllables += 1
            else:
                vowels = "aeiouy"
                prev_char_vowel = False
                syllable_count = 0

                for char in word:
                    if char in vowels and not prev_char_vowel:
                        syllable_count += 1
                    prev_char_vowel = char in vowels

                # Adjust for silent e and other patterns
                if word.endswith("e") and syllable_count > 1:
                    syllable_count -= 1

                total_syllables += max(1, syllable_count)

        return total_syllables / len(words)

    @staticmethod
    def _detect_keyword_stuffing(text: str, threshold: float = 0.05) -> bool:
        """Detect potential keyword stuffing"""
        if not text:
            return False

        words = text.lower().split()
        if len(words) < 10:
            return False

        word_freq = {}
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_freq[word] = word_freq.get(word, 0) + 1

        if not word_freq:
            return False

        max_freq = max(word_freq.values())
        stuffing_ratio = max_freq / len(words)

        return stuffing_ratio > threshold

    @staticmethod
    def analyze_links(links: Dict[str, List[Dict]]) -> List[SEOIssue]:
        """Analyze internal/external link ratios and nofollow/broken links"""
        issues = []

        links = links or {"internal": [], "external": [], "nofollow": [], "broken": []}

        total_links = sum(len(v) for v in links.values())
        if total_links == 0:
            return issues

        internal_count = len(links.get("internal", []))
        external_count = len(links.get("external", []))
        broken_count = len(links.get("broken", []))
        nofollow_count = len(links.get("nofollow", []))

        # Internal link ratio
        if internal_count < 5:
            issues.append(
                SEOIssue(
                    type="few_internal_links",
                    level=SEOIssueLevel.INFO,
                    message=f"Only {internal_count} internal links found",
                    element="<a>",
                    recommendation="Add more internal links to improve site structure",
                    weight=2.0,
                )
            )

        # Broken links
        if broken_count > 0:
            issues.append(
                SEOIssue(
                    type="broken_links",
                    level=SEOIssueLevel.WARNING,
                    message=f"{broken_count} broken links detected",
                    element="<a>",
                    recommendation="Fix or remove broken links",
                    weight=5.0,
                )
            )

        # NoFollow ratio
        nofollow_ratio = nofollow_count / total_links
        if nofollow_ratio > 0.3:
            issues.append(
                SEOIssue(
                    type="high_nofollow_ratio",
                    level=SEOIssueLevel.INFO,
                    message=f"Nofollow links are {nofollow_ratio:.0%} of all links",
                    element="<a>",
                    recommendation="Ensure important links are dofollow where needed",
                    weight=2.0,
                )
            )

        return issues

    @staticmethod
    def analyze_schema(schema_data: List[Dict]) -> List[SEOIssue]:
        """Check structured data richness and missing recommended types"""
        issues = []
        
        schema_data = schema_data or []


        if not schema_data:
            issues.append(
                SEOIssue(
                    type="no_schema",
                    level=SEOIssueLevel.INFO,
                    message="No structured data found",
                    element="<script type='application/ld+json'>",
                    recommendation="Add structured data (Article, Product, FAQ, Breadcrumb)",
                    weight=3.0,
                )
            )
            return issues

        recommended_types = {"Article", "Product", "FAQPage", "BreadcrumbList"}
        found_types = {entry.get("data", {}).get("@type") for entry in schema_data if entry.get("type")=="json-ld"}

        missing_types = recommended_types - found_types
        for t in missing_types:
            issues.append(
                SEOIssue(
                    type="missing_schema_type",
                    level=SEOIssueLevel.INFO,
                    message=f"Recommended schema type '{t}' not found",
                    element="<script type='application/ld+json'>",
                    recommendation=f"Consider adding '{t}' schema for better SEO",
                    weight=2.0,
                )
            )

        return issues

    @staticmethod
    def analyze_canonical_and_hreflang(canonical_url: str, current_url: str, hreflangs: List[Dict[str, str]]) -> List[SEOIssue]:
        """Check canonical URL and hreflang tags"""
        issues = []
        canonical_url = canonical_url or ""
        current_url = current_url or ""
        hreflangs = hreflangs or []

        # Canonical mismatch
        if canonical_url and canonical_url != current_url:
            issues.append(
                SEOIssue(
                    type="canonical_mismatch",
                    level=SEOIssueLevel.INFO,
                    message="Canonical URL does not match current URL",
                    element="<link rel='canonical'>",
                    recommendation="Fix canonical to match page URL",
                    weight=2.0,
                )
            )

        # Missing hreflang
        if not hreflangs:
            issues.append(
                SEOIssue(
                    type="missing_hreflang",
                    level=SEOIssueLevel.INFO,
                    message="No hreflang tags detected",
                    element="<link rel='alternate' hreflang>",
                    recommendation="Add hreflang for multilingual pages",
                    weight=2.0,
                )
            )

        return issues

    @staticmethod
    def analyze_content_richness(content_metrics: Dict, images: List[Dict], tables_count: int = 0) -> List[SEOIssue]:
        """Check for content variety and richness"""
        issues = []

        content_metrics = content_metrics or {}
        images = images or []
        tables_count = tables_count or 0

        if len(images) < 1:
            issues.append(
                SEOIssue(
                    type="low_media",
                    level=SEOIssueLevel.INFO,
                    message="Few or no images in content",
                    element="body content",
                    recommendation="Add images or videos to improve engagement",
                    weight=1.5,
                )
            )

        if tables_count == 0:
            issues.append(
                SEOIssue(
                    type="no_tables",
                    level=SEOIssueLevel.INFO,
                    message="No tables detected in content",
                    element="body content",
                    recommendation="Add tables if it improves content clarity",
                    weight=1.0,
                )
            )

        return issues


    @classmethod
    def analyze_all(
        cls,
        page_data: PageSEOData,
        soup: Optional[BeautifulSoup] = None
    ) -> List[SEOIssue]:
        """
        Orchestrator to run all SEOScorer analysis methods on a page
        Returns a combined list of SEOIssue objects
        """

        issues: List[SEOIssue] = []

        # --- Title ---
        issues.extend(cls().analyze_title(page_data.title, page_data.url))

        # --- Headings ---
        issues.extend(cls.analyze_headings(page_data.headings.__dict__))

        # --- Images ---
        issues.extend(cls.analyze_images([img.__dict__ for img in page_data.images], len(page_data.images)))

        # --- Content ---
        issues.extend(cls.analyze_content(page_data.content_metrics.__dict__ if page_data.content_metrics else {}, page_data.content_text))

        # --- Links ---
        # Separate internal/external/nofollow/broken links
        links_dict = {
            "internal": [l.__dict__ for l in page_data.links if SEOValidator._is_internal_link(l.url, page_data.url)],
            "external": [l.__dict__ for l in page_data.links if not SEOValidator._is_internal_link(l.url, page_data.url)],
            "nofollow": [
                l.__dict__ for l in page_data.links
                if getattr(l, "rel", None) and (
                    (isinstance(l.rel, list) and any(r.lower() == "nofollow" for r in l.rel))
                    or (isinstance(l.rel, str) and l.rel.lower() == "nofollow")
                )
            ],
            "broken": [l.__dict__ for l in page_data.links if getattr(l, "broken", False)]
        }
        issues.extend(cls.analyze_links(links_dict))

        # --- Schema ---
        issues.extend(cls.analyze_schema([s.__dict__ for s in page_data.schema_markup]))

        # --- Canonical & Hreflang ---
        hreflangs = getattr(page_data, "hreflang_tags", [])
        issues.extend(cls.analyze_canonical_and_hreflang(page_data.canonical_url or "", page_data.url, hreflangs))

        # --- Content Richness ---
        tables_count = getattr(page_data, "tables_count", 0)  # optional field
        issues.extend(cls.analyze_content_richness(page_data.content_metrics.__dict__ if page_data.content_metrics else {}, [img.__dict__ for img in page_data.images], tables_count))

        # --- Optional: Indexability (requires soup) ---
        if soup:
            issues.extend(SEOValidator.validate_indexability(soup))

        return issues
