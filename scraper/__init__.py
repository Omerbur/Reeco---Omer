"""
Sysco Product Scraper - Modular Architecture
A professional web scraper for shop.sysco.com with clean, maintainable code structure.
"""

__version__ = "2.0.0"
__author__ = "Sysco Scraper Team"

# Main exports
from .main import SyscoScraperOrchestrator, run_scraper
from .models import ProductData, ScrapingConfig
