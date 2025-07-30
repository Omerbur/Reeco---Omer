import csv
import os
from typing import List
from .models import ProductData, ScrapingConfig


class CSVExporter:
    """Handles CSV export of scraped product data"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.fieldnames = [
            'brand', 'product_name', 'packaging', 'sku', 
            'image_url', 'description', 'price', 'category', 'url'
        ]
    
    def export_products(self, products: List[ProductData]) -> bool:
        """Export products to CSV file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.config.output_dir, exist_ok=True)
            
            if not products:
                print("No products to save")
                return False
            
            # Convert products to dictionaries
            product_dicts = [product.to_dict() for product in products if product.is_valid()]
            
            if not product_dicts:
                print("No valid products to save")
                return False
            
            # Write to CSV
            output_path = os.path.join(self.config.output_dir, self.config.output_file)
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(product_dicts)
            
            print(f"Successfully saved {len(product_dicts)} products to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting products to CSV: {e}")
            return False
    
    def get_output_path(self) -> str:
        """Get the full path to the output CSV file"""
        return os.path.join(self.config.output_dir, self.config.output_file)
