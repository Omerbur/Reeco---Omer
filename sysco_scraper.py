import re
import csv
import time
import logging
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict, Optional
from config import (
    ZIP_CODE, 
    CATEGORIES_TO_SCRAPE, 
    OUTPUT_FILE, 
    OUTPUT_DIR,
    HEADLESS,
    THROTTLE_SECONDS
)

# Additional configuration
MAX_PRODUCTS_PER_CATEGORY = 1000
THROTTLE_DELAY = THROTTLE_SECONDS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SyscoScraper:
    def __init__(self):
        self.products_scraped = 0
        self.csv_writer = None
        self.csv_file = None
        
    def setup_csv(self):
        """Initialize CSV file and writer"""
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        self.csv_file = open(OUTPUT_FILE, 'w', newline='', encoding='utf-8')
        fieldnames = ['Brand Name', 'Product Name', 'Packaging Information', 
                     'SKU', 'Picture URL', 'Description', 'Category']
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        logger.info(f"CSV file created: {OUTPUT_FILE}")

    def accept_cookies(self, page):
        """Accept cookies if banner appears"""
        try:
            cookie_selectors = [
                'button:has-text("Accept")',
                'button:has-text("I Accept")',
                'button:has-text("Accept All")',
                '[data-testid="accept-cookies"]',
                '.cookie-accept',
                '#accept-cookies'
            ]
            
            for selector in cookie_selectors:
                try:
                    page.wait_for_selector(selector, timeout=3000)
                    page.click(selector)
                    logger.info(f"Accepted cookies using selector: {selector}")
                    page.wait_for_timeout(2000)
                    return True
                except PlaywrightTimeoutError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not accept cookies: {e}")
        return False

    def enter_zip_code(self, page):
        """Enter ZIP code for location-based inventory"""
        try:
            # Look for zip code entry elements
            zip_selectors = [
                'input[placeholder*="ZIP"]',
                'input[placeholder*="zip"]',
                'input[name*="zip"]',
                'input[id*="zip"]',
                'input[type="text"]',
                '.zip-input',
                '[data-testid="zip-input"]'
            ]
            
            for selector in zip_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, ZIP_CODE)
                    logger.info(f"Entered ZIP code using selector: {selector}")
                    
                    # Look for submit button
                    submit_selectors = [
                        'button:has-text("Submit")',
                        'button:has-text("Go")',
                        'button:has-text("Search")',
                        'button[type="submit"]',
                        '.submit-btn'
                    ]
                    
                    for submit_selector in submit_selectors:
                        try:
                            page.click(submit_selector)
                            page.wait_for_timeout(3000)
                            logger.info("ZIP code submitted successfully")
                            return True
                        except:
                            continue
                            
                except PlaywrightTimeoutError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not enter ZIP code: {e}")
        return False

    def navigate_to_category(self, page, category_name):
        """Navigate to a specific product category"""
        try:
            # Try different navigation approaches
            nav_selectors = [
                f'a:has-text("{category_name}")',
                f'[data-category="{category_name}"]',
                f'.category-link:has-text("{category_name}")',
                f'nav a:has-text("{category_name}")',
                f'.nav-item:has-text("{category_name}")'
            ]
            
            for selector in nav_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.click(selector)
                    page.wait_for_load_state('networkidle')
                    logger.info(f"Navigated to category: {category_name}")
                    return True
                except PlaywrightTimeoutError:
                    continue
                    
        except Exception as e:
            logger.error(f"Could not navigate to category {category_name}: {e}")
        return False

    def load_all_products(self, page):
        """Load all products by handling pagination or infinite scroll"""
        try:
            previous_count = 0
            max_attempts = 20
            attempts = 0
            
            while attempts < max_attempts:
                # Get current product count
                product_selectors = [
                    '.product-item',
                    '.product-card',
                    '[data-testid="product"]',
                    '.item-card',
                    '.product-tile'
                ]
                
                current_count = 0
                for selector in product_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        if elements:
                            current_count = len(elements)
                            break
                    except:
                        continue
                
                if current_count == previous_count:
                    # Try to load more
                    load_more_selectors = [
                        'button:has-text("Load More")',
                        'button:has-text("Show More")',
                        '.load-more',
                        '.show-more-btn',
                        '[data-testid="load-more"]'
                    ]
                    
                    loaded_more = False
                    for selector in load_more_selectors:
                        try:
                            if page.is_visible(selector):
                                page.click(selector)
                                page.wait_for_timeout(3000)
                                loaded_more = True
                                break
                        except:
                            continue
                    
                    if not loaded_more:
                        # Try scrolling
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(2000)
                        
                    attempts += 1
                else:
                    previous_count = current_count
                    attempts = 0
                
                if current_count >= MAX_PRODUCTS_PER_CATEGORY:
                    break
                    
            logger.info(f"Loaded {current_count} products")
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")

    def extract_product_data(self, product_element, page):
        """Extract data from a single product element"""
        try:
            product_data = {
                'Brand Name': '',
                'Product Name': '',
                'Packaging Information': '',
                'SKU': '',
                'Picture URL': '',
                'Description': '',
                'Category': ''
            }
            
            # Extract product name
            name_selectors = ['.product-name', '.item-name', 'h3', 'h4', '.title']
            for selector in name_selectors:
                try:
                    name_elem = product_element.query_selector(selector)
                    if name_elem:
                        product_data['Product Name'] = name_elem.inner_text().strip()
                        break
                except:
                    continue
            
            # Extract SKU/SUPC
            text_content = product_element.inner_text()
            sku_patterns = [
                r'SUPC[:\s]*([A-Z0-9]+)',
                r'SKU[:\s]*([A-Z0-9]+)',
                r'Item[:\s]*([A-Z0-9]+)',
                r'#([A-Z0-9]{6,})'
            ]
            
            for pattern in sku_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    product_data['SKU'] = match.group(1)
                    break
            
            # Extract brand and packaging from text
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if '|' in line:
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) >= 2:
                        # Assume first part is brand, second is packaging
                        if not product_data['Brand Name']:
                            product_data['Brand Name'] = parts[0]
                        if not product_data['Packaging Information']:
                            product_data['Packaging Information'] = parts[1]
            
            # Extract image URL
            img_selectors = ['img', '.product-image img', '.item-image img']
            for selector in img_selectors:
                try:
                    img_elem = product_element.query_selector(selector)
                    if img_elem:
                        src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = 'https://www.sysco.com' + src
                            product_data['Picture URL'] = src
                            break
                except:
                    continue
            
            # Try to get description from product detail page
            try:
                product_link = product_element.query_selector('a')
                if product_link:
                    href = product_link.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            href = 'https://www.sysco.com' + href
                        
                        # Navigate to product detail page
                        detail_page = page.context.new_page()
                        detail_page.goto(href, timeout=30000)
                        
                        # Extract description
                        desc_selectors = [
                            '.product-description',
                            '.description',
                            '.product-details',
                            '[data-testid="description"]'
                        ]
                        
                        for selector in desc_selectors:
                            try:
                                desc_elem = detail_page.query_selector(selector)
                                if desc_elem:
                                    product_data['Description'] = desc_elem.inner_text().strip()
                                    break
                            except:
                                continue
                        
                        detail_page.close()
                        time.sleep(THROTTLE_DELAY)
                        
            except Exception as e:
                logger.warning(f"Could not get description: {e}")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None

    def scrape_category(self, page, category_name):
        """Scrape all products from a category"""
        logger.info(f"Starting to scrape category: {category_name}")
        
        if not self.navigate_to_category(page, category_name):
            logger.error(f"Could not navigate to category: {category_name}")
            return
        
        self.load_all_products(page)
        
        # Find all product elements
        product_selectors = [
            '.product-item',
            '.product-card',
            '[data-testid="product"]',
            '.item-card',
            '.product-tile'
        ]
        
        products = []
        for selector in product_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    products = elements
                    logger.info(f"Found {len(products)} products using selector: {selector}")
                    break
            except:
                continue
        
        if not products:
            logger.warning(f"No products found for category: {category_name}")
            return
        
        # Extract data from each product
        for i, product in enumerate(products[:MAX_PRODUCTS_PER_CATEGORY]):
            try:
                product_data = self.extract_product_data(product, page)
                if product_data and product_data.get('Product Name'):
                    product_data['Category'] = category_name
                    self.csv_writer.writerow(product_data)
                    self.csv_file.flush()
                    self.products_scraped += 1
                    
                    if i % 10 == 0:
                        logger.info(f"Scraped {i+1}/{len(products)} products from {category_name}")
                    
                    time.sleep(THROTTLE_DELAY)
                    
            except Exception as e:
                logger.error(f"Error processing product {i+1}: {e}")
                continue
        
        logger.info(f"Completed scraping category: {category_name} ({len(products)} products)")

    def run(self):
        """Main scraping function"""
        logger.info("Starting Sysco product scraper")
        self.setup_csv()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                slow_mo=50 if not HEADLESS else 0  # Only slow down in non-headless mode
            )
            
            try:
                page = browser.new_page()
                page.goto("https://www.sysco.com", timeout=30000)
                
                # Handle initial setup
                self.accept_cookies(page)
                self.enter_zip_code(page)
                
                # Scrape each category
                for category in CATEGORIES_TO_SCRAPE:
                    try:
                        self.scrape_category(page, category)
                        
                        if self.products_scraped >= 3000:
                            logger.info("Reached target of 3000 products")
                            break
                            
                    except Exception as e:
                        logger.error(f"Error scraping category {category}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Critical error: {e}")
                
            finally:
                browser.close()
                if self.csv_file:
                    self.csv_file.close()
                
                logger.info(f"Scraping completed. Total products: {self.products_scraped}")
                logger.info(f"Results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    scraper = SyscoScraper()
    scraper.run()