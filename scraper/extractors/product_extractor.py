"""
Individual product data extraction functionality
Handles extraction of specific product fields from product pages
"""

from typing import Dict, Any
from playwright.async_api import Page
from ..models import ProductData
from ..data_formatter import DataFormatter


class ProductExtractor:
    """Handles extraction of individual product data fields"""
    
    def __init__(self, page: Page):
        self.page = page
        self.formatter = DataFormatter()
    
    async def extract_all_fields(self, product_url: str, category: str) -> ProductData:
        """
        Extract all product fields from a product page
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductData object with extracted information
        """
        try:
            print(f"🔍 Navigating to product: {product_url}")
            # 🚀 PERFORMANCE OPTIMIZATION: Use faster wait strategy
            import time
            start_time = time.time()
            await self.page.goto(product_url, wait_until="domcontentloaded", timeout=15000)
            load_time = time.time() - start_time
            print(f"⚡ Product page loaded in {load_time:.2f}s")
            
            # Wait for content to load (longer wait for dynamic content)
            await self.page.wait_for_timeout(3000)
            
            # Extract all product fields
            product_data = ProductData(url=product_url)
            
            # Extract each field with debugging
            print("  🔍 Extracting product fields...")
            product_data.brand = await self.extract_brand()
            print(f"    🏷️ Brand: '{product_data.brand}'")
            
            product_data.product_name = await self.extract_product_name()
            print(f"    📝 Name: '{product_data.product_name}'")
            
            product_data.packaging = await self.extract_packaging()
            print(f"    📦 Packaging: '{product_data.packaging}'")
            
            product_data.sku = await self.extract_sku()
            print(f"    🔢 SKU: '{product_data.sku}'")
            
            product_data.image_url = await self.extract_image_url()
            print(f"    🖼️ Image: '{product_data.image_url[:50] if product_data.image_url else ""}'")
            
            product_data.description = await self.extract_description()
            print(f"    📝 Description: '{product_data.description[:50] if product_data.description else ""}'")
            
            product_data.price = await self.extract_price()
            print(f"    💰 Price: '{product_data.price}'")
            
            product_data.category = category
            
            # Check if we have minimum required data
            has_required_data = bool(product_data.product_name or product_data.brand or product_data.sku)
            print(f"  📊 Has required data: {has_required_data}")
            
            # Validate extracted fields
            if not product_data.product_name:
                print("  ⚠️ No product name found")
            if not product_data.brand:
                print("  ⚠️ No brand found")
            if not product_data.sku:
                print("  ⚠️ No SKU found")
            if not product_data.image_url:
                print("  ⚠️ No image URL found")
            if not product_data.description:
                print("  ⚠️ No description found")
            if not product_data.price:
                print("  ⚠️ No price found")
            
            return product_data
            
        except Exception as e:
            print(f"❌ Error scraping product {product_url}: {e}")
            return ProductData(url=product_url)
    
    async def extract_brand(self) -> str:
        """Extract brand from product page"""
        try:
            # Updated selectors based on actual HTML structure
            brand_selectors = [
                '.brand',  # Primary selector from the HTML example
                'div.brand',
                'button[data-id="product_brand_link"]',  # Fallback
                '.product-brand',
                '[class*="brand"]'
            ]
            
            for selector in brand_selectors:
                brand_element = await self.page.query_selector(selector)
                if brand_element:
                    brand_text = await brand_element.inner_text()
                    if brand_text and brand_text.strip():
                        return self.formatter.clean_text_field(brand_text)
                        
        except Exception as e:
            print(f"⚠️ Error extracting brand: {e}")
        return ""
    
    async def extract_product_name(self) -> str:
        """Extract product name"""
        try:
            # Updated selectors based on actual HTML structure
            name_selectors = [
                '.product-name',  # Primary selector from HTML example
                'div.product-name',
                'h1[data-id="product-name"]',  # Fallback
                'h1.product-name',
                'h1',
                '.product-title h1',
                '[class*="product-name"]'
            ]
            
            for selector in name_selectors:
                name_element = await self.page.query_selector(selector)
                if name_element:
                    name_text = await name_element.inner_text()
                    if name_text and name_text.strip():
                        return self.formatter.clean_text_field(name_text)
                    
        except Exception as e:
            print(f"⚠️ Error extracting product name: {e}")
        return ""
    
    async def extract_packaging(self) -> str:
        """Extract packaging information"""
        try:
            packaging_element = await self.page.query_selector('div[data-id="pack_size"]')
            if packaging_element:
                packaging_text = await packaging_element.inner_text()
                return self.formatter.clean_text_field(packaging_text)
        except Exception as e:
            print(f"⚠️ Error extracting packaging: {e}")
        return ""
    
    async def extract_sku(self) -> str:
        """Extract SKU/Product ID"""
        try:
            # Updated selectors for SKU extraction
            sku_selectors = [
                '.selectable-supc-label span',  # From HTML example
                'div[data-id*="selectable-supc-label"] span',
                'div[data-id="product_id"]',  # Fallback
                '.product-id',
                '.sku',
                '[class*="supc-label"] span',
                '[data-id*="product"] span'
            ]
            
            for selector in sku_selectors:
                sku_element = await self.page.query_selector(selector)
                if sku_element:
                    sku_text = await sku_element.inner_text()
                    if sku_text and sku_text.strip():
                        return self.formatter.clean_text_field(sku_text)
                        
        except Exception as e:
            print(f"⚠️ Error extracting SKU: {e}")
        return ""
    
    async def extract_image_url(self) -> str:
        """Extract main product image URL"""
        try:
            # Updated selectors for product image
            img_selectors = [
                '.product-card-image-v2 img',  # From HTML example
                'div[data-id*="product_card_image"] img',
                'img[data-id="main-product-img-v2"]',  # Fallback
                '.product-image img',
                '.product-card img',
                'img[alt*="product"]',
                '.row.product-image img'
            ]
            
            for selector in img_selectors:
                img_element = await self.page.query_selector(selector)
                if img_element:
                    img_src = await img_element.get_attribute('src')
                    if img_src and img_src.strip():
                        return img_src.strip()
                        
        except Exception as e:
            print(f"⚠️ Error extracting image URL: {e}")
        return ""
    
    async def extract_description(self) -> str:
        """Extract product description with Read More handling"""
        try:
            # First check if "Read More" button exists
            read_more_button = await self.page.query_selector('button[data-id="ellipsis-read-more-button"]')
            
            if read_more_button:
                print("📖 Found 'Read More' button, clicking to expand...")
                await read_more_button.click()
                await self.page.wait_for_timeout(1000)  # Reduced wait time for expansion
                
                # After clicking "Read More", extract from the expanded content
                desc_element = await self.page.query_selector('.description-detail-wrapper')
                if desc_element:
                    description_text = await desc_element.inner_text()
                    print(f"✅ Extracted expanded description ({len(description_text)} chars)")
                else:
                    print("⚠️ Could not find expanded description content")
                    description_text = ""
            else:
                # No "Read More" button, extract from default description container
                desc_element = await self.page.query_selector('div[data-id="product_description_text"]')
                if desc_element:
                    description_text = await desc_element.inner_text()
                    print(f"✅ Extracted standard description ({len(description_text)} chars)")
                else:
                    description_text = ""
            
            # Format the description using our formatter
            if description_text:
                formatted_description = self.formatter.format_description(description_text)
                print(f"📝 Formatted description ({len(formatted_description)} chars)")
                return formatted_description
            
        except Exception as e:
            print(f"❌ Error extracting description: {e}")
        
        return ""
    
    async def extract_price(self) -> str:
        """Extract price information with improved selectors"""
        try:
            # Updated price selectors based on inspection
            price_selectors = [
                '.price-current',
                '.product-price',
                '.price',
                '[data-id="product-price"]',
                '.cost',
                '.pricing',
                '[class*="price"]',
                '.price-wrapper',
                '.price-display'
            ]
            
            for selector in price_selectors:
                price_element = await self.page.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and price_text.strip():
                        return self.formatter.clean_text_field(price_text)
                    
        except Exception as e:
            print(f"⚠️ Error extracting price: {e}")
        return ""
    
    async def debug_product_page_structure(self):
        """Debug method to inspect the actual HTML structure of the product page"""
        try:
            print("🔍 DEBUG: Inspecting product page structure...")
            
            # Get page title and URL
            title = await self.page.title()
            url = self.page.url
            print(f"  📝 Page title: {title}")
            print(f"  🔗 Page URL: {url}")
            
            # Check if page is actually loaded
            body = await self.page.query_selector('body')
            if not body:
                print("  ❌ No body element found - page may not be loaded")
                return
            
            # Get page content summary
            all_text = await self.page.evaluate('() => document.body.innerText')
            print(f"  📝 Page content length: {len(all_text)} characters")
            
            # Show first 200 characters of page content
            if all_text:
                preview = all_text[:200].replace('\n', ' ').strip()
                print(f"  🔍 Content preview: '{preview}...'")
            
            # Look for ANY elements with common product-related text
            print("  🔍 Looking for elements with product-related content:")
            
            # Check for any elements containing numbers (potential SKUs/prices)
            try:
                elements_with_numbers = await self.page.query_selector_all('div, span, p, h1, h2, h3')
                number_elements = []
                for elem in elements_with_numbers[:50]:  # Check first 50 elements
                    try:
                        text = await elem.inner_text()
                        if text and any(char.isdigit() for char in text) and len(text.strip()) < 50 and len(text.strip()) > 2:
                            tag_name = await elem.evaluate('(el) => el.tagName')
                            class_name = await elem.get_attribute('class') or ''
                            number_elements.append((tag_name, class_name, text.strip()))
                    except:
                        pass
                
                print(f"  🔢 Found {len(number_elements)} elements with numbers:")
                for tag, cls, text in number_elements[:10]:  # Show first 10
                    print(f"    {tag}.{cls}: '{text}'")
            except Exception as e:
                print(f"  ⚠️ Error analyzing number elements: {e}")
            
            # Look for common product page elements
            print("  🔍 Looking for specific product elements:")
            
            # Check for brand elements with more comprehensive search
            brand_candidates = [
                '.brand', 'div.brand', '.product-brand', '[class*="brand"]',
                'button[data-id="product_brand_link"]', '.brand-name',
                '*[class*="Brand"]', '*[data-id*="brand"]'
            ]
            
            brand_found = False
            for selector in brand_candidates:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = await elem.inner_text()
                            if text and text.strip():
                                print(f"    🏷️ Brand candidate '{selector}': '{text.strip()}'")
                                brand_found = True
                except:
                    pass
            
            if not brand_found:
                print("    ⚠️ No brand elements found with standard selectors")
            
            # Check for product name elements with more comprehensive search
            name_candidates = [
                '.product-name', 'div.product-name', 'h1', '.product-title',
                'h1[data-id="product-name"]', '[class*="product-name"]',
                'h2', 'h3', '*[class*="title"]', '*[class*="name"]'
            ]
            
            name_found = False
            for selector in name_candidates:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = await elem.inner_text()
                            if text and text.strip() and len(text.strip()) > 3:
                                print(f"    📝 Name candidate '{selector}': '{text.strip()}'")
                                name_found = True
                except:
                    pass
            
            if not name_found:
                print("    ⚠️ No product name elements found with standard selectors")
            
            # Check for SKU elements
            sku_candidates = [
                '.selectable-supc-label span', 'div[data-id*="selectable-supc-label"] span',
                '.product-id', '.sku', '[class*="supc-label"]', '[data-id*="product"] span'
            ]
            
            for selector in sku_candidates:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = await elem.inner_text()
                            if text.strip():
                                print(f"    🔢 SKU candidate '{selector}': '{text.strip()}'")
                except:
                    pass
            
            # Check for price elements
            price_candidates = [
                '.price', '.product-price', '[class*="price"]', '.cost',
                '[data-id*="price"]', '.pricing'
            ]
            
            for selector in price_candidates:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = await elem.inner_text()
                            if text.strip():
                                print(f"    💰 Price candidate '{selector}': '{text.strip()}'")
                except:
                    pass
            
            # Check for image elements
            img_candidates = [
                '.product-card-image-v2 img', 'div[data-id*="product_card_image"] img',
                'img[data-id="main-product-img-v2"]', '.product-image img'
            ]
            
            for selector in img_candidates:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for i, elem in enumerate(elements[:2]):  # Show first 2
                            src = await elem.get_attribute('src')
                            alt = await elem.get_attribute('alt')
                            if src:
                                print(f"    🖼️ Image candidate '{selector}': src='{src[:50]}...' alt='{alt}'")
                except:
                    pass
            
            # Final check: Look for ANY div or span elements with meaningful text
            print("  🔍 Looking for ANY meaningful text elements:")
            try:
                all_divs = await self.page.query_selector_all('div, span, p, h1, h2, h3')
                meaningful_texts = []
                for elem in all_divs[:100]:  # Check first 100 elements
                    try:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 5 and len(text.strip()) < 100:
                            tag_name = await elem.evaluate('(el) => el.tagName')
                            class_name = await elem.get_attribute('class') or ''
                            meaningful_texts.append((tag_name, class_name, text.strip()))
                    except:
                        pass
                
                print(f"    📝 Found {len(meaningful_texts)} elements with meaningful text:")
                for tag, cls, text in meaningful_texts[:15]:  # Show first 15
                    print(f"    {tag}.{cls}: '{text}'")
                    
            except Exception as e:
                print(f"    ⚠️ Error analyzing text elements: {e}")
            
            print("  ✅ Product page structure inspection complete")
            
        except Exception as e:
            print(f"⚠️ Error inspecting product page structure: {e}")
            # Try to get basic page info even if inspection fails
            try:
                title = await self.page.title()
                url = self.page.url
                print(f"  🔗 Basic info - Title: {title}, URL: {url}")
            except:
                pass
