"""
AI Usage Tracker - Track AI API usage and costs across multiple providers
"""

__version__ = "0.1.0"
__author__ = "Autonomous Initiatives"
__description__ = "Track AI API usage and costs across multiple providers"

from .database import Database
from .cli import main

__all__ = ["Database", "main"]