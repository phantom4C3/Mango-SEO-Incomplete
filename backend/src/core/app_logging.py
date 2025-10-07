# src/core/app_logging.py

import logging
from logging.handlers import RotatingFileHandler
import os
import asyncio
from ..clients.supabase_client import supabase_client

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)

def configure_logging():
    """
    Set up logging for the application:
    - Rotating file handler (logs/app.log, 10MB max, 5 backups)
    - Standard logging format
    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# -------------------------
# Async logging helpers
# -------------------------
async def log_info(message: str):
    """Log an info message to file and optionally Supabase."""
    logger = logging.getLogger("app")
    logger.info(message)
    try:
        await supabase_client.insert_into(
            "logs", [{"level": "INFO", "message": message}]
        )
    except Exception as e:
        logger.error(f"Failed to log to Supabase: {str(e)}")

async def log_error(message: str):
    """Log an error message to file and optionally Supabase."""
    logger = logging.getLogger("app")
    logger.error(message)
    try:
        await supabase_client.insert_into(
            "logs", [{"level": "ERROR", "message": message}]
        )
    except Exception as e:
        logger.error(f"Failed to log to Supabase: {str(e)}")

# -------------------------
# For quick testing
# -------------------------
if __name__ == "__main__":
    asyncio.run(log_info("This is an info test"))
    asyncio.run(log_error("This is an error test"))
