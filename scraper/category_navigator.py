"""
Category navigation functionality for the Sysco scraper
Handles category selection and navigation with multiple strategies
"""

import asyncio
from typing import List, Optional
from playwright.async_api import Page


class CategoryNavigator:
    """Handles category selection and navigation"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def select_category(self, category_name: str) -> bool:
        """
        Select a category using the new dropdown menu navigation approach
        
        Args:
            category_name: Name of the category to select
            
        Returns:
            True if category was successfully selected
        """
        try:
            print(f"📁 Selecting category via dropdown menu: {category_name}")
            
            # 🚀 NEW APPROACH: Use sidebar dropdown menu navigation
            return await self._select_via_dropdown_menu(category_name)
            
        except Exception as e:
            print(f"❌ Error selecting category '{category_name}': {e}")
            return False
    
    async def _select_via_dropdown_menu(self, category_name: str) -> bool:
        """
        Select category using the sidebar dropdown menu after zip code entry
        """
        try:
            print(f"🎯 Using dropdown menu navigation for: {category_name}")
            
            # Step 1: Find and hover over the "Products" dropdown button
            print("🔍 Looking for Products dropdown button...")
            
            # Look for the Products dropdown with the specific structure
            products_button_selectors = [
                'div.nav-link.active:has-text("Products")',
                'div.nav-link:has-text("Products")',
                '.nav-link:has-text("Products")',
                'div:has-text("Products"):has(.expand-indicator)'
            ]
            
            products_button = None
            for selector in products_button_selectors:
                try:
                    products_button = await self.page.wait_for_selector(selector, timeout=5000)
                    if products_button:
                        print(f"✅ Found Products button with selector: {selector}")
                        break
                except:
                    continue
            
            if not products_button:
                print("❌ Could not find Products dropdown button")
                return False
            
            # Step 2: Hover over the Products button to reveal the dropdown menu
            print("🖱️ Hovering over Products button to reveal dropdown...")
            await products_button.hover()
            await self.page.wait_for_timeout(1000)  # Wait for dropdown to appear
            
            # Step 3: Look for the category in the dropdown menu
            print(f"🔍 Looking for '{category_name}' in dropdown menu...")
            
            # Wait for dropdown menu items to appear
            await self.page.wait_for_timeout(500)
            
            # Look for category menu items
            category_selectors = [
                f'div.products-menu-item:has-text("{category_name}")',
                f'.products-menu-item:has-text("{category_name}")',
                f'[class*="menu-item"]:has-text("{category_name}")',
                f'div:has-text("{category_name}")'
            ]
            
            category_item = None
            for selector in category_selectors:
                try:
                    # Look for exact or partial matches
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if text and category_name.lower() in text.lower():
                            category_item = element
                            print(f"✅ Found category item: '{text}' with selector: {selector}")
                            break
                    if category_item:
                        break
                except:
                    continue
            
            if not category_item:
                print(f"❌ Could not find '{category_name}' in dropdown menu")
                # Debug: Show what menu items are available
                await self._debug_dropdown_menu()
                return False
            
            # Step 4: Click on the category menu item
            print(f"🎯 Clicking on category menu item: {category_name}")
            await category_item.click()
            await self.page.wait_for_timeout(3000)  # Wait for navigation
            
            print(f"✅ Successfully selected category: {category_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error in dropdown menu navigation: {e}")
            return False
    
    async def _debug_dropdown_menu(self):
        """Debug helper to show available dropdown menu items"""
        try:
            print("🔍 DEBUG: Available dropdown menu items:")
            
            # Look for various menu item selectors
            menu_selectors = [
                'div.products-menu-item',
                '.products-menu-item', 
                '[class*="menu-item"]',
                '.dropdown-menu div',
                '.nav-dropdown div'
            ]
            
            for selector in menu_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"  📋 Found {len(elements)} items with selector '{selector}':")
                        for i, element in enumerate(elements[:10]):  # Show first 10
                            try:
                                text = await element.inner_text()
                                if text.strip():
                                    print(f"    {i+1}: '{text.strip()}'")
                            except:
                                pass
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error debugging dropdown menu: {e}")
    
    async def _select_by_direct_link(self, category_name: str) -> bool:
        """Try to select category by direct link click"""
        try:
            print(f"🔗 Trying direct link for: {category_name}")
            
            # Look for direct category links
            category_selectors = [
                f'a:has-text("{category_name}")',
                f'[data-category="{category_name}"]',
                f'[aria-label*="{category_name}"]'
            ]
            
            for selector in category_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await self.page.wait_for_load_state("networkidle")
                    print(f"✅ Selected category via direct link: {category_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Direct link selection failed: {e}")
            return False
    
    async def _select_by_menu_navigation(self, category_name: str) -> bool:
        """Try to select category through menu navigation"""
        try:
            print(f"📋 Trying menu navigation for: {category_name}")
            
            # Look for menu button or dropdown
            menu_selectors = [
                'button[data-id="categories-menu"]',
                '.categories-menu',
                '.menu-toggle',
                '[aria-label*="menu"]'
            ]
            
            menu_button = None
            for selector in menu_selectors:
                menu_button = await self.page.query_selector(selector)
                if menu_button:
                    break
            
            if menu_button:
                # Click menu to open
                await menu_button.click()
                await self.page.wait_for_timeout(1000)
                
                # Look for category in opened menu
                category_link = await self.page.query_selector(f'a:has-text("{category_name}")')
                if category_link:
                    await category_link.click()
                    await self.page.wait_for_load_state("networkidle")
                    print(f"✅ Selected category via menu: {category_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Menu navigation failed: {e}")
            return False
    
    async def _select_by_search(self, category_name: str) -> bool:
        """Try to select category using search functionality"""
        try:
            print(f"🔍 Trying search-based selection for: {category_name}")
            
            # Look for search input
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search"]',
                '.search-input',
                '[data-id="search-input"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                search_input = await self.page.query_selector(selector)
                if search_input:
                    break
            
            if search_input:
                # Enter category name in search
                await search_input.fill(category_name)
                await self.page.keyboard.press('Enter')
                await self.page.wait_for_load_state("networkidle")
                
                # Look for category in search results
                category_result = await self.page.query_selector(f'a:has-text("{category_name}")')
                if category_result:
                    await category_result.click()
                    await self.page.wait_for_load_state("networkidle")
                    print(f"✅ Selected category via search: {category_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Search-based selection failed: {e}")
            return False
    
    async def get_current_category_url(self) -> str:
        """Get the current category page URL"""
        return self.page.url
    
    async def return_to_dashboard(self) -> bool:
        """Return to the main dashboard - not needed with dropdown navigation"""
        try:
            print("🏠 Returning to dashboard...")
            # With dropdown navigation, we don't need to return to dashboard
            # The dropdown menu should always be available
            await self.page.wait_for_timeout(1000)
            print("✅ Ready for next category selection")
            return True
        except Exception as e:
            print(f"❌ Error in dashboard return: {e}")
            return False
    
    async def get_available_categories(self) -> List[str]:
        """Get list of available categories on the current page"""
        try:
            categories = []
            
            # Look for category links
            category_elements = await self.page.query_selector_all('a[href*="/category/"], .category-link')
            
            for element in category_elements:
                category_text = await element.inner_text()
                if category_text and category_text.strip():
                    categories.append(category_text.strip())
            
            return list(set(categories))  # Remove duplicates
            
        except Exception as e:
            print(f"⚠️ Error getting available categories: {e}")
            return []
    
    async def debug_page_structure(self):
        """Debug helper to understand page structure"""
        try:
            print("🔍 DEBUG: Analyzing page structure...")
            
            # Get page title
            title = await self.page.title()
            print(f"Page Title: {title}")
            
            # Get current URL
            url = self.page.url
            print(f"Current URL: {url}")
            
            # Look for common navigation elements
            nav_elements = await self.page.query_selector_all('nav, .navigation, .menu, [role="navigation"]')
            print(f"Navigation elements found: {len(nav_elements)}")
            
            # Look for category-related elements
            category_elements = await self.page.query_selector_all('[class*="category"], [data-id*="category"], a[href*="category"]')
            print(f"Category-related elements found: {len(category_elements)}")
            
            # Get all links for analysis
            all_links = await self.page.query_selector_all('a[href]')
            print(f"Total links found: {len(all_links)}")
            
            # Sample some link texts
            link_texts = []
            for i, link in enumerate(all_links[:10]):  # First 10 links
                text = await link.inner_text()
                href = await link.get_attribute('href')
                if text and text.strip():
                    link_texts.append(f"{text.strip()} -> {href}")
            
            print("Sample links:")
            for link_text in link_texts:
                print(f"  {link_text}")
                
        except Exception as e:
            print(f"⚠️ Debug analysis failed: {e}")
