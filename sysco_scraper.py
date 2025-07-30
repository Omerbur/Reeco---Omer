import asyncio
import csv
import os
import time
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any

from playwright.async_api import async_playwright, Page, Browser
from config import (
    ZIP_CODE, OUTPUT_DIR, HEADLESS, THROTTLE_SECONDS,
    CATEGORIES_TO_SCRAPE, OUTPUT_FILE
)


class SyscoScraper:
    def __init__(self):
        self.base_url = "https://shop.sysco.com"
        self.login_url = "https://shop.sysco.com/auth/login"
        self.products = []
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        
    async def start_browser(self):
        """Initialize the browser and context"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.firefox.launch(
                headless=HEADLESS
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
            print("Browser started successfully")
        except Exception as e:
            print(f"Error starting browser: {e}")
            await self.close_browser()
            raise
        
    async def close_browser(self):
        """Close the browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Error closing browser: {e}")
            
    async def navigate_and_login_as_guest(self):
        """Navigate to shop.sysco.com and handle guest login flow"""
        print(f"Navigating to {self.base_url}...")
        
        try:
            # Step 1: Navigate to shop.sysco.com (will redirect to login)
            await self.page.goto(self.base_url, wait_until='load', timeout=60000)
            await self.page.wait_for_timeout(3000)
            print("Successfully navigated to shop.sysco.com")
            
            # Step 2: Handle redirect to login page and click "Continue as Guest"
            print("Looking for 'Continue as Guest' button...")
            guest_button_selectors = [
                'button[data-id="btn_login_continue_as_guest"]',
                'button:has-text("Continue as Guest")',
                '.btn-secondary:has-text("Continue as Guest")',
                '[data-id="btn_login_continue_as_guest"]'
            ]
            
            guest_clicked = False
            for selector in guest_button_selectors:
                try:
                    guest_button = await self.page.wait_for_selector(selector, timeout=5000)
                    if guest_button:
                        await guest_button.click()
                        print("Clicked 'Continue as Guest' button")
                        guest_clicked = True
                        break
                except:
                    continue
                    
            if not guest_clicked:
                print("Warning: Could not find 'Continue as Guest' button")
                
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"Error during navigation/login: {e}")
        
    async def handle_zip_code_modal(self):
        """Handle the zip code modal dialog based on user specifications"""
        try:
            print("Looking for zip code modal...")
            await self.page.wait_for_timeout(5000)  # Wait longer for modal to appear
            
            # Look for the specific zip code input in the modal
            zip_input_selectors = [
                'input[data-id="initial_zipcode_modal_input"]',
                '.initial-zipcode-modal-input input',
                '.input-lg input[type="text"]',
                'input[aria-labelledby*="foundation-text-input"]'
            ]
            
            zip_input = None
            for selector in zip_input_selectors:
                try:
                    zip_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if zip_input:
                        print(f"Found zip input with selector: {selector}")
                        break
                except:
                    continue
                    
            if zip_input:
                print(f"Entering zip code: {ZIP_CODE}")
                # Clear the input field properly using correct Playwright methods
                await zip_input.click()
                await zip_input.press('Control+a')  # Select all
                await zip_input.type(ZIP_CODE)
                await self.page.wait_for_timeout(2000)  # Wait for button to become enabled
                
                # Look for the "Start Shopping" button
                start_shopping_selectors = [
                    'button[data-id="initial_zipcode_modal_start_shopping_button"]',
                    'button:has-text("Start Shopping")',
                    '.initial-zipcode-modal-button',
                    '.btn-primary:has-text("Start Shopping")',
                    'button.btn-primary[type="primary"]'
                ]
                
                shopping_clicked = False
                for selector in start_shopping_selectors:
                    try:
                        # Wait for button to exist and become enabled
                        shopping_btn = await self.page.wait_for_selector(selector, timeout=5000)
                        if shopping_btn:
                            # Wait for button to be enabled (not disabled)
                            print(f"Found button with selector: {selector}, checking if enabled...")
                            
                            # Wait up to 10 seconds for button to become enabled
                            for attempt in range(10):
                                is_disabled = await shopping_btn.get_attribute('disabled')
                                if is_disabled is None:  # Button is enabled
                                    break
                                await self.page.wait_for_timeout(1000)
                                print(f"Button still disabled, waiting... (attempt {attempt + 1}/10)")
                            
                            # Try to click the button
                            await shopping_btn.scroll_into_view_if_needed()
                            await shopping_btn.click()
                            print(f"Clicked 'Start Shopping' button with selector: {selector}")
                            shopping_clicked = True
                            break
                    except Exception as e:
                        print(f"Failed to click with selector '{selector}': {e}")
                        continue
                        
                if not shopping_clicked:
                    print("Warning: Could not find 'Start Shopping' button")
                    # Debug: Show what buttons are available
                    all_buttons = await self.page.query_selector_all('button')
                    print(f"Found {len(all_buttons)} buttons on page")
                    for i, btn in enumerate(all_buttons[:5]):
                        try:
                            text = await btn.inner_text()
                            data_id = await btn.get_attribute('data-id')
                            btn_class = await btn.get_attribute('class')
                            print(f"  Button {i}: text='{text}', data-id='{data_id}', class='{btn_class}'")
                        except:
                            pass
                    return False
                    
                await self.page.wait_for_timeout(8000)  # Wait longer for page to load after modal
                print("Successfully handled zip code modal")
                return True
                
            else:
                print("No zip code input found in modal")
                return False
                
        except Exception as e:
            print(f"Error handling zip code modal: {e}")
            return False
            
    async def select_category(self, category_name: str) -> bool:
        """Select a category from the shop.sysco.com dashboard"""
        try:
            print(f"Looking for category: {category_name}")
            await self.page.wait_for_timeout(3000)
            
            # First, debug what categories are available
            print("Debugging available categories...")
            try:
                # Look for all category grid buttons
                category_buttons = await self.page.query_selector_all('div.category-grid-button')
                print(f"Found {len(category_buttons)} category grid buttons")
                
                for i, btn in enumerate(category_buttons[:10]):  # Show first 10
                    try:
                        btn_class = await btn.get_attribute('class')
                        # Get the span text inside
                        title_span = await btn.query_selector('span.category-grid-title')
                        title_text = ""
                        title_data_id = ""
                        if title_span:
                            title_text = await title_span.inner_text()
                            title_data_id = await title_span.get_attribute('data-id')
                        
                        print(f"  Category {i}: class='{btn_class}', title='{title_text}', data-id='{title_data_id}'")
                        
                        # Check if this matches our target category
                        if title_text and category_name.lower() in title_text.lower():
                            print(f"Found matching category: {title_text}")
                    except Exception as debug_e:
                        print(f"  Category {i}: Error getting details - {debug_e}")
            except Exception as debug_e:
                print(f"Error debugging categories: {debug_e}")
            
            # Now try to click the target category using multiple strategies
            category_clicked = False
            
            # Strategy 1: Direct click on category button containing the text
            try:
                print(f"Strategy 1: Looking for category button containing '{category_name}'")
                category_buttons = await self.page.query_selector_all('div.category-grid-button')
                
                for btn in category_buttons:
                    try:
                        title_span = await btn.query_selector('span.category-grid-title')
                        if title_span:
                            title_text = await title_span.inner_text()
                            if title_text and category_name.lower() in title_text.lower():
                                print(f"Found matching category button: {title_text}")
                                # Use JavaScript click to bypass aria-hidden
                                await btn.evaluate('element => element.click()')
                                print(f"Clicked category '{category_name}' using JavaScript click")
                                category_clicked = True
                                break
                    except Exception as e:
                        continue
                        
                if category_clicked:
                    await self.page.wait_for_timeout(5000)
                    return True
                        
            except Exception as e:
                print(f"Strategy 1 failed: {e}")
            
            # Strategy 2: Click on the span directly
            if not category_clicked:
                try:
                    print(f"Strategy 2: Looking for category title span containing '{category_name}'")
                    title_spans = await self.page.query_selector_all('span.category-grid-title')
                    
                    for span in title_spans:
                        try:
                            title_text = await span.inner_text()
                            if title_text and category_name.lower() in title_text.lower():
                                print(f"Found matching category span: {title_text}")
                                # Use JavaScript click
                                await span.evaluate('element => element.click()')
                                print(f"Clicked category span '{category_name}' using JavaScript click")
                                category_clicked = True
                                break
                        except Exception as e:
                            continue
                            
                    if category_clicked:
                        await self.page.wait_for_timeout(5000)
                        return True
                        
                except Exception as e:
                    print(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Use specific data-id selectors
            if not category_clicked:
                try:
                    print(f"Strategy 3: Using data-id selectors for '{category_name}'")
                    # Map category names to their data-id patterns
                    data_id_map = {
                        "meat & seafood": "meatseafood",
                        "dairy & eggs": "dairyeggs",
                        "canned & dry": "canneddry",
                        "frozen foods": "frozenfoods",
                        "bakery & bread": "bakerybread",
                        "equipment & supplies": "equipmentsupplies",
                        "produce": "produce",
                        "beverages": "beverages",
                        "disposables": "disposables",
                        "chemicals": "chemicals"
                    }
                    
                    data_id_key = data_id_map.get(category_name.lower())
                    if data_id_key:
                        selector = f'span[data-id="lbl_category_app.dashboard.{data_id_key}.title"]'
                        print(f"Trying selector: {selector}")
                        
                        span_element = await self.page.wait_for_selector(selector, timeout=5000)
                        if span_element:
                            await span_element.evaluate('element => element.click()')
                            print(f"Clicked category '{category_name}' using data-id selector")
                            category_clicked = True
                            
                    if category_clicked:
                        await self.page.wait_for_timeout(5000)
                        return True
                        
                except Exception as e:
                    print(f"Strategy 3 failed: {e}")
            
            if not category_clicked:
                print(f"Warning: Could not find or click category '{category_name}' with any strategy")
                return False
                
            await self.page.wait_for_timeout(5000)
            return True
            
        except Exception as e:
            print(f"Error selecting category '{category_name}': {e}")
            return False
        
    async def scrape_product_page(self, product_url: str) -> Dict[str, Any]:
        """Scrape individual product details"""
        product_data = {
            'url': product_url,
            'brand': '',
            'product_name': '',
            'packaging': '',
            'sku': '',
            'image_url': '',
            'description': '',
            'price': '',
            'category': ''
        }
        
        try:
            await self.page.goto(product_url, wait_until='networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Extract product name (renamed from 'name' to 'product_name')
            name_selectors = ['h1', '.product-title', '.product-name', '[data-testid="product-name"]']
            for selector in name_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        product_data['product_name'] = await element.inner_text()
                        break
                except:
                    continue
                    
            # Extract brand using specific selector
            try:
                brand_element = await self.page.query_selector('button[data-id="product_brand_link"]')
                if brand_element:
                    product_data['brand'] = await brand_element.inner_text()
            except Exception as e:
                print(f"Could not extract brand: {e}")
                    
            # Extract SKU using specific selector
            try:
                sku_element = await self.page.query_selector('div[data-id="product_id"]')
                if sku_element:
                    product_data['sku'] = await sku_element.inner_text()
            except Exception as e:
                print(f"Could not extract SKU: {e}")
                    
            # Extract packaging using specific selector
            try:
                packaging_element = await self.page.query_selector('div[data-id="pack_size"]')
                if packaging_element:
                    product_data['packaging'] = await packaging_element.inner_text()
            except Exception as e:
                print(f"Could not extract packaging: {e}")
                    
            # Extract main product image using specific selector
            try:
                img_element = await self.page.query_selector('img[data-id="main-product-img-v2"]')
                if img_element:
                    src = await img_element.get_attribute('src')
                    if src:
                        product_data['image_url'] = src
            except Exception as e:
                print(f"Could not extract image URL: {e}")
                    
            # Extract description with "Read More" button handling
            try:
                # First check if "Read More" button exists
                read_more_button = await self.page.query_selector('button[data-id="ellipsis-read-more-button"]')
                if read_more_button:
                    print("Found 'Read More' button, clicking it...")
                    await read_more_button.click()
                    await self.page.wait_for_timeout(1000)  # Wait for content to expand
                
                # Now extract the description
                desc_element = await self.page.query_selector('div[data-id="product_description_text"]')
                if desc_element:
                    description_text = await desc_element.inner_text()
                    # Clean up the description by removing "Read More" artifacts
                    description_text = description_text.replace('...Read More', '').strip()
                    product_data['description'] = description_text
            except Exception as e:
                print(f"Could not extract description: {e}")
                    
            # Extract price (keeping existing logic as fallback)
            price_selectors = ['.price', '.product-price', '[data-testid="price"]', '.cost']
            for selector in price_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        product_data['price'] = await element.inner_text()
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"Error scraping product {product_url}: {e}")
            
        return product_data
        
    async def scrape_category_products(self, category_url: str) -> List[str]:
        """Get all product URLs from a category page"""
        product_urls = []
        
        try:
            await self.page.goto(category_url, wait_until='networkidle')
            print(f"Scraping category: {category_url}")
            
            # Handle pagination and load all products
            page_num = 1
            max_pages = 5  # Limit to prevent infinite loops
            
            while page_num <= max_pages:
                print(f"Processing page {page_num}...")
                
                # Wait for products to load
                await self.page.wait_for_timeout(2000)
                
                # Find product links on current page (enhanced for shop.sysco.com)
                product_selectors = [
                    'a[href*="/product/"]',
                    'a[href*="/item/"]',
                    'a[href*="/detail/"]',
                    'a[href*="/p/"]',
                    '.product-link',
                    '.product-tile a',
                    '.product-card a',
                    '.item-link',
                    '.product-item a',
                    '.catalog-item a',
                    '[data-testid="product-link"]',
                    '[data-testid="product-card"] a',
                    '.product a',
                    '.item a',
                    'article a',
                    '.grid-item a',
                    '.tile a',
                    '[class*="product"] a',
                    '[class*="item"] a'
                ]
                
                page_products = set()
                for selector in product_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            print(f"  Selector '{selector}' found {len(elements)} elements")
                        for element in elements:
                            href = await element.get_attribute('href')
                            if href and ('/product/' in href or '/item/' in href or '/detail/' in href or '/p/' in href or '/app/catalog' in href):
                                full_url = urljoin(self.base_url, href)
                                page_products.add(full_url)
                                if len(page_products) <= 3:  # Debug first few URLs
                                    print(f"    Added product URL: {full_url}")
                    except Exception as e:
                        continue
                        
                print(f"Found {len(page_products)} products on page {page_num}")
                
                # Debug: If no products found, analyze the page
                if len(page_products) == 0:
                    print("DEBUG: No products found, analyzing page content...")
                    
                    # Check if page title suggests we need to log in or enter zip
                    title = await self.page.title()
                    print(f"  Page title: {title}")
                    
                    # Look for any links on the page
                    all_links = await self.page.query_selector_all('a')
                    print(f"  Total links on page: {len(all_links)}")
                    
                    # Check for specific content that might indicate issues
                    content_checks = [
                        ('zip code required', 'text*="zip"'),
                        ('login required', 'text*="login" i'),
                        ('location required', 'text*="location" i'),
                        ('sign in', 'text*="sign in" i'),
                        ('products', 'text*="product" i')
                    ]
                    
                    for check_name, selector in content_checks:
                        try:
                            elements = await self.page.query_selector_all(selector)
                            if elements:
                                print(f"  Found {len(elements)} elements with '{check_name}' text")
                        except:
                            pass
                    
                    # Sample some link hrefs to understand page structure
                    sample_links = all_links[:10]
                    print("  Sample link hrefs:")
                    for i, link in enumerate(sample_links):
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href:
                                print(f"    {i}: {href[:80]} | Text: {text[:30]}")
                        except:
                            pass
                
                product_urls.extend(list(page_products))
                
                # Try to go to next page
                next_found = False
                next_selectors = [
                    'a:has-text("Next")',
                    'a[aria-label="Next"]',
                    '.pagination .next',
                    '.pager .next',
                    'button:has-text("Next")'
                ]
                
                for selector in next_selectors:
                    try:
                        next_button = await self.page.query_selector(selector)
                        if next_button:
                            # Check if button is enabled
                            is_disabled = await next_button.get_attribute('disabled')
                            if not is_disabled:
                                await next_button.click()
                                await self.page.wait_for_timeout(3000)
                                next_found = True
                                break
                    except:
                        continue
                        
                if not next_found:
                    print("No more pages found")
                    break
                    
                page_num += 1
                
        except Exception as e:
            print(f"Error scraping category {category_url}: {e}")
            
        return list(set(product_urls))  # Remove duplicates
        
    async def scrape_all_products(self):
        """Main scraping method using the new shop.sysco.com flow"""
        print("Starting Sysco product scraper with new flow...")
        
        await self.start_browser()
        
        try:
            # Step 1: Navigate to shop.sysco.com and handle guest login
            await self.navigate_and_login_as_guest()
            
            # Step 2: Handle zip code modal
            zip_success = await self.handle_zip_code_modal()
            if not zip_success:
                print("Failed to handle zip code modal, continuing anyway...")
            
            # Step 3: Process each category
            all_product_urls = []
            for i, category in enumerate(CATEGORIES_TO_SCRAPE):
                print(f"\nProcessing category {i+1}/{len(CATEGORIES_TO_SCRAPE)}: {category}")
                
                # Select the category from dashboard
                category_selected = await self.select_category(category)
                if not category_selected:
                    print(f"Skipping category '{category}' - could not select")
                    continue
                
                # Get products from this category
                current_url = self.page.url
                product_urls = await self.scrape_category_products(current_url)
                all_product_urls.extend(product_urls)
                
                # Go back to dashboard for next category (if not last)
                if i < len(CATEGORIES_TO_SCRAPE) - 1:
                    print("Returning to dashboard for next category...")
                    await self.page.goto(self.base_url, wait_until='load')
                    await self.page.wait_for_timeout(3000)
                
                # Throttle between categories
                await self.page.wait_for_timeout(int(THROTTLE_SECONDS * 1000))
                
            print(f"\nFound {len(all_product_urls)} total products to scrape")
            
            # Step 4: Scrape individual products (limited to 10 for testing)
            max_products = min(10, len(all_product_urls))  # Limit to 10 for testing
            for i, product_url in enumerate(all_product_urls[:max_products]):
                print(f"Scraping product {i+1}/{max_products}: {product_url}")
                
                product_data = await self.scrape_product_page(product_url)
                if product_data['product_name']:  # Only add if we got some data (updated field name)
                    self.products.append(product_data)
                    
                # Throttle between products
                await self.page.wait_for_timeout(int(THROTTLE_SECONDS * 1000))
                
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await self.close_browser()
            
    def save_to_csv(self):
        """Save scraped products to CSV file"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        if not self.products:
            print("No products to save")
            return
            
        fieldnames = ['brand', 'product_name', 'packaging', 'sku', 'image_url', 'description', 'price', 'category', 'url']
        
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)
            
        print(f"Saved {len(self.products)} products to {OUTPUT_FILE}")
        

async def main():
    """Main entry point"""
    scraper = SyscoScraper()
    await scraper.scrape_all_products()
    scraper.save_to_csv()
    

if __name__ == "__main__":
    asyncio.run(main())