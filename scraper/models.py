"""
Data models for the Sysco scraper
"""
from dataclasses import dataclass, field
from typing import List, Optional
import os


@dataclass
class ProductData:
    """Data model for a scraped product"""
    url: str = ""
    brand: str = ""
    product_name: str = ""
    packaging: str = ""
    sku: str = ""
    image_url: str = ""
    description: str = ""
    price: str = ""
    category: str = ""
    
    # Performance optimization flags
    enable_resource_blocking: bool = True
    enable_async_scraping: bool = False
    enable_performance_monitoring: bool = True
    
    def is_valid(self) -> bool:
        """Check if product has minimum required data"""
        # Must have URL and at least one identifying field (product name, brand, or SKU)
        # Price is not mandatory as some products may not have pricing displayed
        has_url = bool(self.url)
        has_identifying_info = bool(self.product_name or self.brand or self.sku)
        return has_url and has_identifying_info
    
    def to_dict(self) -> dict:
        """Convert ProductData to dictionary for CSV export"""
        return {
            'url': self.url,
            'brand': self.brand,
            'product_name': self.product_name,
            'packaging': self.packaging,
            'sku': self.sku,
            'image_url': self.image_url,
            'description': self.description,
            'price': self.price,
            'category': self.category
        }


@dataclass
class ScrapingConfig:
    """Configuration for the scraper"""
    zip_code: str = "97035"
    headless: bool = False
    categories_to_scrape: List[str] = field(default_factory=lambda: [
        "Meat & Seafood",
        "Dairy & Eggs", 
        "Canned & Dry"
    ])
    max_products: int = 10  # Limit for testing, can be increased to 20 for production
    output_dir: str = "output"
    output_file: str = "sysco_products.csv"
    
    # Browser and navigation settings
    page_load_timeout: int = 30000  # 30 seconds
    element_timeout: int = 10000    # 10 seconds
    throttle_seconds: float = 0.5   # Delay between operations
    
    # Performance optimization settings
    enable_resource_blocking: bool = True
    enable_async_scraping: bool = False
    enable_performance_monitoring: bool = True
    async_batch_size: int = 3
    
    @property
    def output_path(self) -> str:
        """Get full output file path"""
        return os.path.join(self.output_dir, self.output_file)
