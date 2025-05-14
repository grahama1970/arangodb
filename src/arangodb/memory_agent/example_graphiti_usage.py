#!/usr/bin/env python3
"""
Example of using the enhanced Memory Agent with Graphiti-inspired features.

This example demonstrates:
1. Storing conversations with temporal metadata
2. Creating entities and relationships
3. Detecting and resolving contradictions
4. Performing temporal search

Run with:
    python example_graphiti_usage.py
"""

import asyncio
from datetime import datetime, timezone, timedelta
from loguru import logger
import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

from complexity.arangodb.arango_setup import connect_arango, ensure_database
from complexity.arangodb.memory_agent.memory_agent import MemoryAgent

# Custom log formatter with nicer colors
class ColoredFormatter:
    def __init__(self):
        self.colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Fore.RED + Style.BRIGHT,
            "DEBUG": Fore.BLUE
        }
        self.styles = {
            "header": Style.BRIGHT,
            "normal": Style.NORMAL,
            "reset": Style.RESET_ALL
        }
    
    def format(self, record):
        level_name = record["level"].name
        level_color = self.colors.get(level_name, "")
        
        # Format the message with appropriate colors
        if level_name == "INFO":
            # For regular info messages, use cyan
            return f"{Fore.CYAN}{record['message']}{Style.RESET_ALL}"
        elif level_name == "SUCCESS":
            # For success messages, use green
            return f"{Fore.GREEN}{record['message']}{Style.RESET_ALL}"
        elif level_name == "WARNING":
            # For warnings, use yellow
            return f"{Fore.YELLOW}{record['message']}{Style.RESET_ALL}"
        elif level_name == "ERROR" or level_name == "CRITICAL":
            # For errors, use red
            return f"{Fore.RED}{record['message']}{Style.RESET_ALL}"
        else:
            # Default formatting
            return record["message"]


async def main():
    # Print welcome message with custom formatting
    print(f"{Fore.CYAN}{Style.BRIGHT}
