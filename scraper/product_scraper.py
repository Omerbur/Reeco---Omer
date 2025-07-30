"""
Product scraping coordinator for the Sysco scraper
Coordinates individual product extraction and category URL collection
"""

from typing import List
from playwright.async_api import Page
from .models import ProductData
from .extractors import ProductExtractor, CategoryExtractor


class ProductScraper:
    """Coordinates product data extraction using specialized extractors"""
    
    def __init__(self, page: Page):
        self.page = page
        self.product_extractor = ProductExtractor(page)
        self.category_extractor = CategoryExtractor(page)
    
    async def scrape_product(self, product_url: str, category: str) -> ProductData:
        """
        Scrape detailed product data from a product page
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductData object with extracted information
        """
        return await self.product_extractor.extract_all_fields(product_url, category)
    

    
    async def scrape_category_products(self, category_url: str) -> List[str]:
        """
        Scrape product URLs from a category page with pagination support
        
        Args:
            category_url: URL of the category page
            
        Returns:
            List of product URLs found in the category
        """
        return await self.category_extractor.extract_all_product_urls(category_url)
    

