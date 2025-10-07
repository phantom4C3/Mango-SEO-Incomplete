# onpageseo-service/app/utils/parsers.py
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional, Tuple, Any
import re
from urllib.parse import urljoin, urlparse
import logging
from shared_models.models import SEOIssue, SEOIssueLevel

logger = logging.getLogger(__name__)


class HTMLParser:
    """Core HTML parsing utilities for SEO analysis - used by all services"""

    @staticmethod
    def parse_html(html_content: str, base_url: Optional[str] = None) -> BeautifulSoup:
        """
        Parse HTML content with error handling
        """
        if not html_content:
            return BeautifulSoup("", "lxml")

        try:
            soup = BeautifulSoup(html_content, "lxml")
            if base_url:
                # Set base URL for relative link resolution
                soup = HTMLParser._set_base_url(soup, base_url)
                return soup 

        except Exception as e:
            logger.error(f"HTML parsing failed: {str(e)}")
            # Fallback to html5lib if lxml fails
            return BeautifulSoup(html_content, "html5lib")

    @staticmethod
    def _set_base_url(soup: BeautifulSoup, base_url: str) -> BeautifulSoup:
        """Ensure base URL is set for relative link resolution"""
        if not base_url:
          return soup

        base_tag = soup.find("base")
        if not base_tag or not base_tag.get("href"):
            base_tag = soup.new_tag("base")
            base_tag["href"] = base_url
            if soup.head:
                soup.head.insert(0, base_tag)
        return soup

    @staticmethod
    def extract_meta_tags(soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all meta tags with comprehensive coverage"""
        if not soup:
            return {}

        meta_tags = {}

        for tag in soup.find_all("meta"):
            # Standard meta tags
            if tag.get("name"):
                meta_tags[tag["name"].lower()] = tag.get("content", "")
            # Open Graph tags
            elif tag.get("property"):
                meta_tags[tag["property"]] = tag.get("content", "")
            # Twitter cards
            elif tag.get("name", "").startswith("twitter:"):
                meta_tags[tag["name"]] = tag.get("content", "")
            # HTTP Equiv
            elif tag.get("http-equiv"):
                meta_tags[tag["http-equiv"].lower()] = tag.get("content", "")
            # Charset
            elif tag.get("charset"):
                meta_tags["charset"] = tag["charset"]

        return meta_tags

    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        """Extract page title with fallbacks"""
        if not soup:
            return ""


        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        # Fallback to Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        # Fallback to H1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)[:255]  # Truncate to title length

        return ""

    @staticmethod
    def extract_headings(soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all headings with hierarchy"""
        if not soup:
            return {"h1":[],"h2":[],"h3":[],"h4":[],"h5":[],"h6":[]}

        headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}

        for level in headings.keys():
            elements = soup.find_all(level)
            headings[level] = [
                elem.get_text(strip=True)
                for elem in elements
                if elem.get_text(strip=True)
            ]

        return headings

    @staticmethod
    def extract_links(soup: BeautifulSoup, base_url: str) -> Dict[str, List[Dict]]:
        """Extract and categorize all links"""
        if not soup or not base_url:
          return {"internal": [], "external": [], "nofollow": [], "broken": []}

        links = {
            "internal": [],
            "external": [],
            "nofollow": [],
            "broken": [],  # Will be populated during validation
        }

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = a_tag.get_text(strip=True)
            rel = a_tag.get("rel", [])

            link_info = {
                "url": HTMLParser._resolve_url(href, base_url),
                "text": text,
                "anchor_text": text,
                "rel": rel,
                "nofollow": "nofollow" in rel,
                "title": a_tag.get("title", ""),
            }

            # Categorize links
            if HTMLParser._is_internal_link(link_info["url"], base_url):
                links["internal"].append(link_info)
            else:
                links["external"].append(link_info)

            if link_info["nofollow"]:
                links["nofollow"].append(link_info)

        return links

    @staticmethod
    def extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract all images with SEO attributes"""
        if not soup or not base_url:
             return []

        images = []

        for img in soup.find_all("img"):
            src = img.get("src", "")
            images.append(
                {
                    "src": HTMLParser._resolve_url(src, base_url),
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "loading": img.get("loading", ""),
                    "srcset": img.get("srcset", ""),
                }
            )

        return images

    @staticmethod
    def extract_schema_markup(soup: BeautifulSoup) -> List[Dict]:
        """Extract all schema.org markup"""
        if not soup:
            return []

        schema_data = []

        # JSON-LD scripts
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json

                data = json.loads(script.string)
                schema_data.append({"type": "json-ld", "data": data})
            except:
                continue

        # Microdata
        for elem in soup.find_all(attrs={"itemtype": True}):
            schema_data.append(
                {
                    "type": "microdata",
                    "itemtype": elem.get("itemtype"),
                    "properties": {
                        prop: elem.get(prop)
                        for prop in elem.attrs
                        if prop.startswith("item")
                    },
                }
            )

        return schema_data

    @staticmethod
    def extract_content_text(
        soup: BeautifulSoup, exclude_selectors: List[str] = None
    ) -> str:
        """Extract clean text content for analysis"""
        if not soup:
            return {}
        exclude_selectors = exclude_selectors or []

        # Remove unwanted elements
        if exclude_selectors:
            for selector in exclude_selectors:
                for elem in soup.select(selector):
                    elem.decompose()

        # Remove script and style elements
        for elem in soup(["script", "style", "nav", "footer", "header"]):
            elem.decompose()

        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    @staticmethod
    def _resolve_url(url: str, base_url: str) -> str:
        """Resolve relative URLs to absolute"""
        if not url:
            return ""
        if not base_url:
            return url

        if not url or url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            return url

        try:
            return urljoin(base_url, url)
        except:
            return url

    @staticmethod
    def _is_internal_link(url: str, base_url: str) -> bool:
        """Check if link is internal"""
        if not url or not base_url:
            return False

        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)

            # Same domain or relative path
            return not parsed_url.netloc or parsed_url.netloc == parsed_base.netloc
        except:
            return False
 
    @staticmethod
    def calculate_content_metrics(content_text: str, image_count:int = 0) -> Dict[str, Any]:
        """Calculate comprehensive content metrics with proper types"""
        words = content_text.split()
        word_count = len(words)
        
        # Avoid division by zero for empty content
        if not content_text.strip():
            return {
                "word_count": 0,
                "sentence_count": 0,
                "avg_words_per_sentence": 0.0,
                "unique_words": 0,
                "char_count": 0,
                "readability_score": 0.0,
                "keyword_density": {},
                "content_quality_score": 0.0,
                "semantic_relevance": {},
                "image_count": image_count  # ✅ ADD THIS

            }
        
        sentence_count = max(content_text.count("."), 1)  # At least 1 to avoid division by zero
        char_count = len(content_text)
        
        # Calculate required metrics
        avg_words_per_sentence = word_count / sentence_count
        unique_words = len(set(words))
        
        # Placeholder values (implement proper calculations later)
        readability_score = max(0, min(100, 100 - (avg_words_per_sentence * 0.5)))  # Simple heuristic
        keyword_density = {"primary": 2.5} if word_count > 0 else {}
        content_quality_score = max(0, min(100, (unique_words / max(word_count, 1)) * 100))
        semantic_relevance = {"score": 0.75}  # Placeholder

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "unique_words": unique_words,
            "char_count": char_count,
            "readability_score": round(readability_score, 2),
            "keyword_density": keyword_density,
            "content_quality_score": round(content_quality_score, 2),
            "semantic_relevance": semantic_relevance
        }

    @staticmethod
    def find_canonical_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract canonical URL"""
        if not soup or not base_url:
            return {}

        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            return HTMLParser._resolve_url(canonical["href"], base_url)
        return None

    @staticmethod
    def extract_language_info(soup: BeautifulSoup) -> Dict:
        """Extract language information"""
        if not soup:
            return {"lang": None, "xml:lang": None, "content_language": None}

        html_tag = soup.find("html")
        content_language_tag = soup.find("meta", attrs={"http-equiv": "content-language"})
        
        return {
            "lang": html_tag.get("lang") if html_tag else None,
            "xml:lang": html_tag.get("xml:lang") if html_tag else None,
            "content_language": content_language_tag.get("content") if content_language_tag else None,
        }


    @staticmethod
    def extract_keywords(soup: BeautifulSoup, html_content: str) -> List[str]:
        """
        Extract page keywords from meta tags and optionally from content heuristics.
        Returns a list of keywords.
        """
        if not soup:
            return {}

        keywords = []

        # 1. Meta keywords
        meta = soup.find("meta", attrs={"name": "keywords"})
        if meta and meta.get("content"):
            keywords.extend([kw.strip() for kw in meta["content"].split(",") if kw.strip()])

        # 2. Optional: top words from content
        # words = re.findall(r'\w+', html_content.lower())
        # common_words = ["the", "and", "of", "in", "to", "a"]  # stopwords
        # word_freq = defaultdict(int)
        # for w in words:
        #     if w not in common_words:
        #         word_freq[w] += 1
        # top_keywords = sorted(word_freq, key=word_freq.get, reverse=True)[:10]
        # keywords.extend(top_keywords)

        return list(set(keywords))  # remove duplicates
     

    @staticmethod
    def extract_hreflang_tags(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract <link rel='alternate' hreflang='x' href='y'>"""
        if not soup:
            return []

        hreflangs = []
        for link in soup.find_all("link", rel="alternate", hreflang=True, href=True):
            hreflangs.append({
                "hreflang": link["hreflang"],
                "url": HTMLParser._resolve_url(link["href"], base_url)
            })
        return hreflangs

    @staticmethod
    def extract_social_meta(soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Open Graph and Twitter card info"""
        if not soup:
            return {}

        social_meta = {}
        for tag in soup.find_all("meta"):
            if tag.get("property", "").startswith("og:") or tag.get("name", "").startswith("twitter:"):
                social_meta[tag.get("property") or tag.get("name")] = tag.get("content", "")
        return social_meta

    @staticmethod
    def extract_heading_stats(soup: BeautifulSoup) -> Dict[str, List[int]]:
        """Return number of words per heading"""
        if not soup:
            return {level: [] for level in ["h1","h2","h3","h4","h5","h6"]}

        heading_stats = {}
        for level in ["h1","h2","h3","h4","h5","h6"]:
            heading_stats[level] = [len(h.get_text(strip=True).split()) for h in soup.find_all(level)]
        return heading_stats

    @staticmethod
    def extract_media_counts(soup: BeautifulSoup) -> Dict[str, int]:
        """Count images, videos, tables, and interactive elements"""
        if not soup:
            return {"images":0,"videos":0,"tables":0,"iframes":0,"buttons":0}

        return {
            "images": len(soup.find_all("img")),
            "videos": len(soup.find_all("video")),
            "tables": len(soup.find_all("table")),
            "iframes": len(soup.find_all("iframe")),
            "buttons": len(soup.find_all("button")),
        }

    @staticmethod
    def extract_inline_assets_count(soup: BeautifulSoup) -> Dict[str, int]:
        """Count inline scripts and styles for performance heuristics"""
        if not soup:
            return {"inline_scripts":0,"inline_styles":0}

        return {
            "inline_scripts": len([s for s in soup.find_all("script") if not s.get("src")]),
            "inline_styles": len([s for s in soup.find_all("style")]),
        }

    @staticmethod
    def detect_social_share_buttons(soup: BeautifulSoup) -> int:
        """Count external social share buttons by common classes or iframes"""
        if not soup:
            return 0

        selectors = [
            ".share-button", ".social-share", "iframe[src*='share']", "a[href*='facebook.com/share']",
            "a[href*='twitter.com/intent']", "a[href*='linkedin.com/shareArticle']"
        ]
        count = 0
        for sel in selectors:
            count += len(soup.select(sel))
        return count
 

    @staticmethod
    def extract_all(html_content: str, base_url: str, exclude_selectors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Orchestrator to extract all SEO-relevant data from HTML.
        Returns a structured dictionary with all extracted elements.
        """
        soup = HTMLParser.parse_html(html_content, base_url)

        # --- Basic metadata ---
        title = HTMLParser.extract_title(soup)
        meta_tags = HTMLParser.extract_meta_tags(soup)
        lang_info = HTMLParser.extract_language_info(soup)
        canonical_url = HTMLParser.find_canonical_url(soup, base_url)
        hreflangs = HTMLParser.extract_hreflang_tags(soup, base_url)
        social_meta = HTMLParser.extract_social_meta(soup)

        # --- Content ---
        content_text = HTMLParser.extract_content_text(soup, exclude_selectors)
        content_metrics = HTMLParser.calculate_content_metrics(content_text, image_count=len(soup.find_all("img")))

        # --- Structural elements ---
        headings = HTMLParser.extract_headings(soup)
        heading_stats = HTMLParser.extract_heading_stats(soup)
        links = HTMLParser.extract_links(soup, base_url)
        images = HTMLParser.extract_images(soup, base_url)
        schema_markup = HTMLParser.extract_schema_markup(soup)
        media_counts = HTMLParser.extract_media_counts(soup)
        inline_assets = HTMLParser.extract_inline_assets_count(soup)
        social_buttons_count = HTMLParser.detect_social_share_buttons(soup)
        keywords = HTMLParser.extract_keywords(soup, html_content)

        # --- Return all extracted data in one structured dict ---
        return {
            "title": title,
            "meta_tags": meta_tags,
            "lang_info": lang_info,
            "canonical_url": canonical_url,
            "hreflangs": hreflangs,
            "social_meta": social_meta,
            "content_text": content_text,
            "content_metrics": content_metrics,
            "headings": headings,
            "heading_stats": heading_stats,
            "links": links,
            "images": images,
            "schema_markup": schema_markup,
            "media_counts": media_counts,
            "inline_assets": inline_assets,
            "social_buttons_count": social_buttons_count,
            "keywords": keywords,
        }
