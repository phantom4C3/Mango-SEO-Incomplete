# backend/src/services/realtime_listener_service.py
import logging
import asyncio
from supabase import Client 
from ..clients.supabase_client import supabase_client
from datetime import datetime 
class RealtimeListenerService:
    
    def __init__(self):
        self.supabase= supabase_client
        self.subscriptions = []
        self._running = False

    async def start_listening(self):
        """Start only necessary Supabase realtime subscriptions."""
        self._running = True
        try:
            await self._subscribe_to_blog_tasks()
            await self._subscribe_to_seo_tasks()
 
            # Keep alive until stopped
            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
             await self.stop_listening()

    async def stop_listening(self):
        """Unsubscribe from all subscriptions."""
        self._running = False
        for sub in self.subscriptions:
            try:
                await sub.unsubscribe()
            except Exception as e:
                print(f"Failed to unsubscribe: {e}")
        self.subscriptions.clear()

        # --- Subscriptions ---

# --- Realtime subscription helpers ---
async def _subscribe_to_blog_tasks(self):
    try:
        channel_name = "blog_tasks_changes"
        channel = self.supabase.channel(channel_name)

        channel.on_postgres_changes(
            schema="public",
            table="blog_tasks",
            event="UPDATE",
            filter="status=in.(completed,failed)",
            callback=self._handle_blog_task_update
        )

        await channel.subscribe()
        self.subscriptions.append(channel)
        print(f"✅ Subscribed to {channel_name}")
    except Exception as e:
        print(f"Failed to subscribe to blog_tasks: {e}")


async def _subscribe_to_seo_tasks(self):
    try:
        channel_name = "seo_tasks_changes"
        channel = self.supabase.channel(channel_name)

        channel.on_postgres_changes(
            schema="public",
            table="seo_tasks",
            event="UPDATE",
            filter="status=in.(completed,failed)",
            callback=self._handle_seo_task_update
        )

        await channel.subscribe()
        self.subscriptions.append(channel)
        print(f"✅ Subscribed to {channel_name}")
    except Exception as e:
        print(f"Failed to subscribe to seo_tasks: {e}")

        # --- Handlers ---

    async def _handle_blog_task_update(self, payload):
        task = payload["new"]
        status = task.get("status")

        # Only necessary notifications
        if status in ("completed", "failed"):
            message = f"Your blog task is {status}."
            await supabase_client.insert_into(
                "notifications",
                {
                    "user_id": task.get("user_id"),
                    "type": f"blog_{status}",
                    "message": message,
                    "task_id": task.get("id"),
                    "created_at": datetime.utcnow().isoformat(),
                    "read": False,
                },
            )



    async def _handle_seo_task_update(self, payload):
        task = payload["new"]
        status = task.get("status")

        # Only necessary notifications
        if status in ("completed", "failed"):
            message = f"Your SEO analysis task is {status}."
            await supabase_client.insert_into(
                "notifications",
                {
                    "user_id": task.get("user_id"),
                    "type": f"seo_{status}",
                    "message": message,
                    "task_id": task.get("id"),
                    "created_at": datetime.utcnow().isoformat(),
                    "read": False,
                },
            )


    async def stop_listening(self):
        """Unsubscribe from all realtime channels."""
        self._running = False
        try:
            for subscription in self.subscriptions:
                subscription.unsubscribe() 
        except Exception as e:
                print(f"Failed to subscribe to blog_tasks: {e}")  # or keep print

# --- Singleton instance ---
realtime_listener_service = RealtimeListenerService()









# Potential issues / caveats

# Polling vs push:

# If you rely on DB triggers, realtime_listener_service must poll tables or use Postgres LISTEN/NOTIFY.

# With high frequency, polling can overload the DB.

# Multiple services writing same tables:

# Ensure atomic updates to avoid duplicate triggers (e.g., two services trying to schedule the same blog publishing). 

# If multiple microservices can update the same task, consider a task queue / distributed lock to avoid conflicts.



# Supabase is built on Postgres. Realtime functionality is essentially “listen to Postgres table changes via websockets”, which is why you see "postgres_changes" as the event type.