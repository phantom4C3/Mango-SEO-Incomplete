# allow usrs to change settigs reated to site similar to soebot # backend/src/services/user_service.py

from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging
from uuid import UUID, uuid4


from ..clients.supabase_client import supabase_client
from ..clients.redis_client import redis_client 
from ..core.exceptions import IntegrationError
from shared_models.models import User, UserCreate, UserUpdate, UserSettings, SiteSettings


logger = logging.getLogger(__name__)


class UserService:
    """
    Service for managing user settings, preferences, and site-specific configurations.
    Similar to Soebot's user settings management.
    """

    def __init__(self):
        self.supabase = supabase_client
        self.redis = redis_client

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID with complete profile."""
        try:
            data = await self.supabase.fetch_one("users", {"id": str(user_id)})
            return User(**data) if data else None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="get_user")

    async def update_user_profile(self, user_id: UUID, user_update: UserUpdate) -> User:
        """Update user profile information."""
        try:
            update_data = user_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()

            updated = await self.supabase.update_table("users", {"id": str(user_id)}, update_data)
            if not updated: 
                raise IntegrationError(
                    detail="User not found", operation="update_user_profile"
                )

            return User(**updated[0])  # ✅ Use 'updated' instead of 'response'
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="update_user_profile")
  
    async def get_user_preferences(self, user_id: UUID) -> UserSettings:
        """Get user preferences and settings."""
        try:
            data = await self.supabase.fetch_one("user_preferences", {"user_id": str(user_id)})
            return UserSettings(**data) if data else UserSettings(user_id=user_id)

        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="get_user_preferences")
    # -------------------------------
    # Optional helper: login
    # -------------------------------
    async def update_user_preferences(
        self, user_id: UUID, preferences: UserSettings
    ) -> UserSettings:
        """Update user preferences."""
        try:
            pref_data = preferences.dict()
            pref_data["updated_at"] = datetime.utcnow().isoformat()

            # Check if preferences exist first, then update/insert
            existing = await self.supabase.fetch_one("user_preferences", {"user_id": str(user_id)})
            if existing:
                updated = await self.supabase.update_table("user_preferences", {"user_id": str(user_id)}, pref_data)
            else:
                updated = await self.supabase.insert_into("user_preferences", pref_data)
                return UserSettings(**updated[0])  # ✅ ADD THIS RETURN

        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="update_user_preferences")

    async def _cache_preferences(self, user_id: UUID, preferences: Dict) -> None:
        """Cache user preferences in Redis."""
        try:
            cache_key = f"user:{user_id}:preferences"
            await redis_client.set(cache_key, preferences, ex=3600)  # 1 hour cache
        except Exception as e:
            logger.warning(f"Error caching preferences for user {user_id}: {e}")

    async def get_site_settings(self, user_id: UUID, site_id: Optional[UUID] = None) -> List[SiteSettings]:
        """Get site settings for a user."""
        try:
            filters = {"user_id": str(user_id)}
            if site_id:
                filters["id"] = str(site_id)
                
            data = await self.supabase.fetch_all("website_configs", filters)
            return [SiteSettings(**site) for site in data]
            
        except Exception as e:
            logger.error(f"Error getting site settings for user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="get_site_settings")

    async def update_site_settings(
        self, user_id: UUID, site_settings: SiteSettings
    ) -> SiteSettings:
        """Update site-specific settings."""
        try:
            site_data = site_settings.dict()
            site_data["updated_at"] = datetime.utcnow().isoformat()

            # Use existing methods - check if site exists first
            existing = await self.supabase.fetch_one("website_configs", {"id": str(site_settings.id)})
            if existing:
                updated = await self.supabase.update_table("website_configs", {"id": str(site_settings.id)}, site_data)
            else:
                updated = await self.supabase.insert_into("website_configs", site_data)
            return SiteSettings(**updated[0])
        except Exception as e:
            logger.error(f"Error updating site settings for user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="update_site_settings")

    async def get_notification_settings(self, user_id: UUID) -> Dict[str, Any]:
        """Get user notification preferences."""
        try:
            data = await self.supabase.fetch_one("user_notifications", {"user_id": str(user_id)})
            return data if data else {
                "email_notifications": True,
                "browser_notifications": False,
                "task_completion_alerts": True,
                "error_alerts": True,
                "weekly_reports": True,
            }

        except Exception as e:
            logger.error(f"Error getting notification settings for user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="get_notification_settings")

    async def update_notification_settings(
        self, user_id: UUID, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update notification settings."""
        try:
            settings_data = {
                "user_id": str(user_id),
                **settings,
                "updated_at": datetime.utcnow().isoformat(),
            }

            existing = await self.supabase.fetch_one("user_notifications", {"user_id": str(user_id)})
            if existing:
                updated = await self.supabase.update_table("user_notifications", {"user_id": str(user_id)}, settings_data)
            else:
                updated = await self.supabase.insert_into("user_notifications", settings_data)
            return updated[0]

        except Exception as e:
            logger.error(
                f"Error updating notification settings for user {user_id}: {e}"
            )
            raise IntegrationError(
                detail=str(e), operation="update_notification_settings"
            )
 
    async def get_usage_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user usage statistics."""
        try:
            # Get article count
            articles_response = (
                await self.supabase.table("articles")
                .select("id")
                .eq("user_id", str(user_id))
                .execute()
            )
            article_count = len(articles_response.data) if articles_response.data else 0

            # Get task count
            tasks_response = (
                await self.supabase.table("tasks")
                .select("id")
                .eq("user_id", str(user_id))
                .execute()
            )
            task_count = len(tasks_response.data) if tasks_response.data else 0

            # Get CMS integration count
            cms_response = (
                await self.supabase.table("cms_integrations")
                .select("id")
                .eq("user_id", str(user_id))
                .execute()
            )
            cms_count = len(cms_response.data) if cms_response.data else 0

            return {
                "article_count": article_count,
                "task_count": task_count,
                "cms_integrations_count": cms_count,
                "last_30_days_activity": await self._get_recent_activity(user_id),
            }
        except Exception as e:
            logger.error(f"Error getting usage stats for user {user_id}: {e}")
            raise IntegrationError(detail=str(e), operation="get_usage_stats")

    async def _get_recent_activity(self, user_id: UUID) -> Dict[str, int]:
        """Get user activity from the last 30 days."""
        try:
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

            data = await self.supabase.fetch_all("tasks", {
                "user_id": str(user_id),
                "created_at": {"gte": thirty_days_ago}
            })

            # Manual counting by status
            activity = {}
            for task in data:
                status = task.get("status", "unknown")
                activity[status] = activity.get(status, 0) + 1
            return activity
        except Exception as e:
            logger.warning(f"Error getting recent activity for user {user_id}: {e}")
            return {}
  
    async def get_or_create_oauth_user(self, email: str, name: str = None, picture: str = None) -> User:
        """Get existing user or create new one from OAuth data."""
        try:
            # Try to get existing user
            user_data = await self.supabase.fetch_one("users", {"email": email})
            
            if user_data:
                return User(**user_data)
            
            # Create new user from OAuth
            new_user_data = {
                "id": str(uuid4()),
                "email": email,
                "name": name or "",
                "profile_picture": picture or "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "role": "free"  # Default role
            }
            
            created = await self.supabase.insert_into("users", new_user_data)
            return User(**created[0])
            
        except Exception as e:
            logger.error(f"Error in get_or_create_oauth_user for {email}: {e}")
            raise IntegrationError(detail=str(e), operation="get_or_create_oauth_user")
    
# Singleton instance
user_service = UserService()


