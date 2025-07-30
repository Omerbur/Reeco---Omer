"""
Browser management for the Sysco scraper
Handles browser lifecycle, navigation, and Sysco-specific interactions
"""

import asyncio
import time
from playwright.async_api import async_playwright, Browser, Page, Playwright
from .models import ScrapingConfig


class BrowserManager:
    """Manages browser lifecycle and Sysco navigation"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None
    
    async def start_browser(self) -> Page:
        """Initialize browser with performance optimizations"""
        try:
            print("🌐 Starting Firefox browser with performance optimizations...")
            self.playwright = await async_playwright().start()
            
            # Launch browser with optimized settings
            self.browser = await self.playwright.firefox.launch(
                headless=self.config.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # 🚀 PERFORMANCE OPTIMIZATION: Block unnecessary resources (if enabled)
            if self.config.enable_resource_blocking:
                await self.page.route("**/*", self._handle_route)
                print("🚫 Resource blocking enabled")
            else:
                print("📥 Resource blocking disabled")
            
            print("✅ Browser started with resource blocking enabled")
            return self.page
            
        except Exception as e:
            print(f"❌ Error starting browser: {e}")
            await self.close_browser()
            raise
    
    async def close_browser(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("🔒 Browser closed successfully")
        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")
    
    async def navigate_to_sysco(self) -> bool:
        """Navigate to Sysco and handle guest login"""
        try:
            print("🏪 Navigating to shop.sysco.com...")
            # 🚀 PERFORMANCE OPTIMIZATION: Use faster wait strategy
            start_time = time.time()
            await self.page.goto("https://shop.sysco.com", wait_until="domcontentloaded", timeout=self.config.page_load_timeout)
            await self.page.wait_for_timeout(2000)  # Reduced wait time
            load_time = time.time() - start_time
            if self.config.enable_performance_monitoring:
                print(f"⚡ Page loaded in {load_time:.2f}s")
            print("✅ Successfully navigated to shop.sysco.com")
            
            # Handle guest login
            if await self._handle_guest_login():
                print("✅ Successfully handled guest login")
                return True
            else:
                print("❌ Failed to handle guest login")
                return False
                
        except Exception as e:
            print(f"❌ Error navigating to Sysco: {e}")
            return False
    
    async def _handle_guest_login(self) -> bool:
        """Handle the guest login process with multiple fallback selectors"""
        try:
            print("👤 Looking for 'Continue as Guest' button...")
            
            # Use same selectors as original scraper
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
                        print(f"✅ Clicked 'Continue as Guest' button with selector: {selector}")
                        guest_clicked = True
                        break
                except:
                    continue
                    
            if not guest_clicked:
                print("⚠️ Could not find 'Continue as Guest' button with any selector")
                return False
                
            await self.page.wait_for_timeout(3000)  # Wait for navigation
            return True
                
        except Exception as e:
            print(f"❌ Error during guest login: {e}")
            return False
    
    async def handle_zip_code_modal(self) -> bool:
        """Handle zip code modal with robust fallback strategies from original scraper"""
        try:
            print("📍 Looking for zip code modal...")
            await self.page.wait_for_timeout(5000)  # Wait longer for modal to appear
            
            # Look for the specific zip code input in the modal (from original scraper)
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
                        print(f"📍 Found zip input with selector: {selector}")
                        break
                except:
                    continue
                    
            if zip_input:
                print(f"📍 Entering zip code: {self.config.zip_code}")
                # Clear the input field properly using correct Playwright methods
                await zip_input.click()
                await zip_input.press('Control+a')  # Select all
                await zip_input.type(self.config.zip_code)
                await self.page.wait_for_timeout(2000)  # Wait for button to become enabled
                
                # Look for the "Start Shopping" button (from original scraper)
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
                            print(f"📍 Found button with selector: {selector}, checking if enabled...")
                            
                            # Wait up to 10 seconds for button to become enabled
                            for attempt in range(10):
                                is_disabled = await shopping_btn.get_attribute('disabled')
                                if is_disabled is None:  # Button is enabled
                                    break
                                await self.page.wait_for_timeout(1000)
                                print(f"📍 Button still disabled, waiting... (attempt {attempt + 1}/10)")
                            
                            # Try to click the button
                            await shopping_btn.scroll_into_view_if_needed()
                            await shopping_btn.click()
                            print(f"✅ Clicked 'Start Shopping' button with selector: {selector}")
                            shopping_clicked = True
                            break
                    except Exception as e:
                        print(f"⚠️ Failed to click with selector '{selector}': {e}")
                        continue
                        
                if not shopping_clicked:
                    print("⚠️ Could not find 'Start Shopping' button")
                    return False
                    
                await self.page.wait_for_timeout(8000)  # Wait longer for page to load after modal
                print("✅ Successfully handled zip code modal")
                return True
                
            else:
                print("ℹ️ No zip code input found in modal")
                return False
                
        except Exception as e:
            print(f"❌ Error handling zip code modal: {e}")
            return False
    
    async def _handle_route(self, route):
        """Handle resource routing to block unnecessary resources for performance"""
        resource_type = route.request.resource_type
        url = route.request.url
        
        # Block images, stylesheets, fonts, and other non-essential resources
        blocked_types = {'image', 'stylesheet', 'font', 'media'}
        
        # Also block specific domains that are not essential
        blocked_domains = {
            'googletagmanager.com', 'google-analytics.com', 'facebook.com',
            'twitter.com', 'linkedin.com', 'pinterest.com', 'instagram.com',
            'doubleclick.net', 'googlesyndication.com', 'amazon-adsystem.com'
        }
        
        # Check if we should block this resource
        should_block = (
            resource_type in blocked_types or
            any(domain in url for domain in blocked_domains)
        )
        
        if should_block:
            await route.abort()
        else:
            await route.continue_()
    
    async def throttle(self):
        """Apply throttling between requests"""
        if self.config.throttle_seconds > 0:
            await asyncio.sleep(self.config.throttle_seconds)
    
    async def wait_for_page_load(self, timeout: int = 30000):
        """Wait for page to fully load"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            print(f"⚠️ Page load timeout: {e}")
    
    async def scroll_to_bottom(self):
        """Scroll to bottom of page to trigger lazy loading"""
        try:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)  # Wait for content to load
        except Exception as e:
            print(f"⚠️ Error scrolling: {e}")
    
    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url if self.page else ""
    
    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to a specific URL"""
        try:
            await self.page.goto(url, wait_until="networkidle")
            return True
        except Exception as e:
            print(f"❌ Error navigating to {url}: {e}")
            return False
