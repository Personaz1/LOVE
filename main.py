#!/usr/bin/env python3
"""
Family Psychologist Telegram Bot
Main entry point for the application
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bot.family_psychologist_bot import bot
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point"""
    try:
        logger.info("Starting Family Psychologist Bot...")
        logger.info(f"Using OpenAI model: {settings.OPENAI_MODEL}")
        logger.info(f"Memory file: {settings.MEMORY_FILE_PATH}")
        
        if settings.MCP_SERVER_URL:
            logger.info(f"MCP Server configured: {settings.MCP_SERVER_URL}")
        else:
            logger.info("MCP Server not configured - running in local mode")
        
        # Create necessary directories
        Path(settings.MEMORY_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        # Run the bot
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 