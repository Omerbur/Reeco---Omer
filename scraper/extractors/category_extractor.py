"""
Category product URL extraction functionality
Handles pagination and URL collection from category pages
"""

import asyncio
from typing import List
from playwright.async_api import Page


class CategoryExtractor:
    """Handles extraction of product URLs from category pages"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def extract_all_product_urls(self, category_url: str) -> List[str]:
        """
        Extract product URLs from a category page with pagination support
        
        Args:
            category_url: URL of the category page
            
        Returns:
            List of product URLs found in the category
        """
        product_urls = []
        
        try:
            print(f"📂 Scraping products from category: {category_url}")
            # 🚀 PERFORMANCE OPTIMIZATION: Use faster wait strategy
            import time
            start_time = time.time()
            await self.page.goto(category_url, wait_until="domcontentloaded", timeout=15000)
            load_time = time.time() - start_time
            print(f"⚡ Category page loaded in {load_time:.2f}s")
            
            page_num = 1
            max_pages = 10  # Limit to prevent infinite loops
            
            while page_num <= max_pages:
                print(f"📄 Processing page {page_num}...")
                
                # 🚀 PERFORMANCE OPTIMIZATION: Reduced wait time
                await self.page.wait_for_timeout(1000)
                
                # Scroll to load any lazy-loaded content
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(1000)
                
                # Extract product links from current page
                page_products = await self.extract_product_links_from_current_page()
                product_urls.extend(page_products)
                
                print(f"✅ Found {len(page_products)} products on page {page_num}")
                
                # Try to go to next page
                if not await self.navigate_to_next_page():
                    print("📄 No more pages found")
                    break
                
                page_num += 1
                await self.page.wait_for_timeout(1000)  # Reduced wait between pages
            
            print(f"📊 Total products found in category: {len(product_urls)}")
            return list(set(product_urls))  # Remove duplicates
            
        except Exception as e:
            print(f"❌ Error scraping category products: {e}")
            return product_urls
    
    async def extract_product_links_from_current_page(self) -> List[str]:
        """Extract product links using the same extensive selector list as original scraper"""
        try:
            # Look for product links using the actual product structure
            product_selectors = [
                'a.product-card-link',  # Primary selector based on actual HTML
                'a[href*="/app/product-details/"]',  # Href pattern match
                'a[class*="product-card"]',  # Class pattern match
                'a[href*="/product/"]',  # Legacy fallback
                'a[href*="/item/"]', 
                'a[href*="/detail/"]',
                '.product-link',
                '[class*="product"] a',
                '[class*="item"] a',
                '.product-card a',
                'a[data-product-id]',
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
                        print(f"  🔍 Selector '{selector}' found {len(elements)} elements")
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href and ('/product/' in href or '/item/' in href or '/detail/' in href or '/p/' in href or '/app/catalog' in href):
                            # Convert relative URLs to absolute (from original scraper)
                            if href.startswith('/'):
                                full_url = f"https://shop.sysco.com{href}"
                            else:
                                full_url = href
                            page_products.add(full_url)
                            if len(page_products) <= 3:  # Debug first few URLs
                                print(f"    ✅ Added product URL: {full_url}")
                except Exception as e:
                    continue
            
            # Debug: If no products found, analyze the page (from original scraper)
            if len(page_products) == 0:
                print("🔍 DEBUG: No products found, analyzing page content...")
                
                # Check if page title suggests we need to log in or enter zip
                title = await self.page.title()
                print(f"  📄 Page title: {title}")
                
                # Look for any links on the page
                all_links = await self.page.query_selector_all('a')
                print(f"  🔗 Total links on page: {len(all_links)}")
                
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
                            print(f"  ⚠️ Found {len(elements)} elements with '{check_name}' text")
                    except:
                        pass
                
                # Sample some link hrefs to understand page structure
                sample_links = all_links[:10]
                print("  🔗 Sample link hrefs:")
                for i, link in enumerate(sample_links):
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        if href:
                            print(f"    {i}: {href[:80]} | Text: {text[:30]}")
                    except:
                        pass
            
            return list(page_products)
            
        except Exception as e:
            print(f"❌ Error extracting product links: {e}")
            return []
    
    async def navigate_to_next_page(self) -> bool:
        """Try to navigate to next page using original scraper's selectors"""
        try:
            # Use the exact same next page selectors from original scraper
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
                            await self.page.wait_for_timeout(3000)  # Same timeout as original
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error navigating to next page: {e}")
            return False
