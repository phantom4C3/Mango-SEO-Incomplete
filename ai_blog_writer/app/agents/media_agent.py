# ai_blog_generator/app/agents/media_agent.py
import logging
import asyncio
import base64
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build

from playwright.async_api import async_playwright
import httpx
from typing import List, Dict, Any
from ..clients.ai_clients import nano_banana_client
from ..clients.cloudinary import upload_image
from shared_models.models import UserSettings
from ..core.config import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except:
        return False




class MediaAgent:
    """
    Media Generation Agent - Handles media creation for blog posts:
    - Header images
    - Website screenshots
    - YouTube video integration
    """

    async def generate_media_assets(
        self,
        headings: list[str],
        title: str,
        target_keyword: str,
        website_url: str,
        language: str,
        user_prefs: UserSettings,  # <-- Pass preferences directly
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate all media assets concurrently
        """
        try:

            tasks = []

            # Header image
            if user_prefs.allow_ai_images:
                tasks.append(
                    self._generate_header_image(
                        headings, title, target_keyword, language, user_prefs
                    )
                )
            else:
                tasks.append(asyncio.sleep(0))

            # Website screenshot
            if website_url:
                tasks.append(self._capture_website_screenshot(website_url))
            else:
                tasks.append(asyncio.sleep(0))

            # YouTube videos
            if user_prefs.include_youtube_videos:
                tasks.append(
                    self._find_youtube_videos(
                        title, target_keyword, task_id, user_prefs
                    )
                )
            else:
                tasks.append(asyncio.sleep(0))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            header_image = (
                results[0]
                if not isinstance(results[0], Exception)
                else {"status": "failed"}
            )
            screenshot = (
                results[1]
                if not isinstance(results[1], Exception)
                else {"status": "failed"}
            )
            youtube_videos = results[2] if not isinstance(results[2], Exception) else []

            return {
                "header_image": (
                    header_image
                    if user_prefs.allow_ai_images
                    else {"status": "disabled"}
                ),
                "website_screenshot": (
                    screenshot if website_url else {"status": "no_url"}
                ),
                "youtube_videos": youtube_videos[
                    : user_prefs.max_youtube_videos_per_post
                ],
            }

        except Exception as e:
            logger.error(f"Media generation failed: {str(e)}")
            return self._generate_fallback_media(title, website_url)

    async def _generate_header_image(
        self, headings, title, target_keyword, language, user_prefs
    ):
        try:
            # ---- Build the prompt ----
            prompt_elements = [
                f"Header image for blog post: {title}",
                f"Primary keyword: {target_keyword}",
                f"Preferred style: {user_prefs.image_style}",
                "High quality, professional, visually engaging",
            ]

            if headings:
                prompt_elements.append(
                    f"These are the blog's section headings: {', '.join(headings)}"
                )

            if user_prefs.custom_image_prompt:
                prompt_elements.append(
                    f"User preference: {user_prefs.custom_image_prompt}"
                )

            image_prompt = ". ".join(prompt_elements)

            # ---- Call Nano Banana ----
            image_response = await nano_banana_client.generate_image(
                prompt=image_prompt
            )

            # ✅ Guard #1: no candidates
            if not (image_response and "candidates" in image_response):
                logger.warning("No candidates returned from Nano Banana")
                return {"status": "failed"}

            parts = image_response["candidates"][0]["content"]["parts"]

            # ✅ Guard #2: no parts
            if not parts:
                logger.warning("No parts returned in Nano Banana response")
                return {"status": "failed"}

            # ✅ Guard #3: no inline_data
            if "inline_data" not in parts[0]:
                logger.warning("No inline_data found in Nano Banana response")
                return {"status": "failed"}

            # ---- Safe to decode now ----
            image_data = parts[0]["inline_data"]["data"]
            image_bytes = base64.b64decode(image_data)

            image_url = await upload_image(
                image_bytes,
                f"header_{abs(hash(title))}",
                folder="blog-headers",
            )

            return {
                "url": image_url,
                "alt_text": f"Header image for {title}",
                "prompt": image_prompt,
                "status": "generated",
            }

        except Exception as e:
            logger.error(f"Header image generation failed: {str(e)}")
            return {
                "url": None,
                "alt_text": f"Header image for {title}",
                "status": "failed",
            }

    async def _capture_website_screenshot(self, website_url: str) -> Dict[str, Any]:
        """Capture a screenshot of the website"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed — skipping screenshot")
            return {"status": "unsupported_environment"}

        try:
            async with async_playwright() as p:
                if not is_valid_url(website_url):
                    logger.warning(f"Invalid website URL: {website_url}")
                    return {"status": "invalid_url"}

                try:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                        ],
                    )
                except Exception as e:
                    logger.warning(f"Chromium launch failed: {e}")
                    return {"status": "unsupported_environment"}

                try:
                    context = await browser.new_context(viewport={"width": 1200, "height": 800})
                    page = await context.new_page()
                    await page.goto(website_url, timeout=30000, wait_until="networkidle")
                    await self._clean_page_for_screenshot(page)

                    screenshot = await page.screenshot(full_page=False, quality=80, type="jpeg")
                finally:
                    await browser.close()

                screenshot_url = await upload_image(
                    screenshot,
                    f"screenshot_{abs(hash(website_url))}",
                    folder="website-screenshots",
                )
                return {
                    "url": screenshot_url,
                    "original_url": website_url,
                    "alt_text": f"Screenshot of {website_url}",
                    "status": "captured",
                }

        except Exception as e:
            logger.error(f"Screenshot capture failed: {str(e)}", exc_info=True)
            return {"status": "failed"}


    async def _find_youtube_videos(
        self, title: str, target_keyword: str, task_id: str, user_prefs: UserSettings
    ) -> List[Dict[str, Any]]:
        """Search for the most relevant YouTube video asynchronously."""
        try:
            if not settings.youtube_api_key:
                logger.warning("YouTube API key not configured.")
                return []

            query = f"{title} {target_keyword}"
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 5,
                "order": "relevance",
                "videoEmbeddable": "true",
                "safeSearch": "strict",
                "key": settings.youtube_api_key,
            }

            if user_prefs.preferred_youtube_channels:
                params["channelId"] = ",".join(user_prefs.preferred_youtube_channels)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            if "items" not in data or not data["items"]:
                return []

            best_video = data["items"][0]
            snippet = best_video["snippet"]
            video_id = best_video["id"]["videoId"]

            return [
                {
                    "video_id": video_id,
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet["thumbnails"]["high"]["url"],
                    "embed_url": f"https://www.youtube.com/embed/{video_id}",
                    "status": "selected",
                }
            ]

        except httpx.HTTPStatusError as e:
            logger.error(
                f"YouTube API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"YouTube search failed: {str(e)}")
            return []

    async def _clean_page_for_screenshot(self, page) -> None:
        """Remove popups, modals, ads for screenshot"""
        try:
            selectors_to_remove = [
                ".popup",
                ".modal",
                ".advertisement",
                ".cookie-banner",
            ]
            for selector in selectors_to_remove:
                await page.evaluate(
                    f"document.querySelectorAll('{selector}').forEach(el => el.remove())"
                )
            await asyncio.sleep(1)
        except Exception as e:
            logger.debug(f"Page cleaning failed: {str(e)}")

    def _generate_fallback_media(self, title: str, website_url: str) -> Dict[str, Any]:
        """Fallback media assets if generation fails"""
        return {
            "header_image": {"status": "fallback", "alt_text": f"Header for {title}"},
            "website_screenshot": {"status": "fallback", "original_url": website_url},
            "youtube_videos": [],
        }
