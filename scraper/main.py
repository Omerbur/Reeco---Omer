import asyncio
import time
from typing import List, Dict
from .models import ProductData, ScrapingConfig
from .browser_manager import BrowserManager
from .category_navigator import CategoryNavigator
from .product_scraper import ProductScraper
from .csv_exporter import CSVExporter


class SyscoScraperOrchestrator:
    """Main orchestrator that coordinates all scraping components"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.browser_manager = BrowserManager(config)
        self.products: List[ProductData] = []
        
        # Components initialized after browser starts
        self.category_navigator = None
        self.product_scraper = None
        self.csv_exporter = CSVExporter(config)
    
    async def run_scraper(self) -> bool:
        """Main scraper orchestration method with comprehensive timing"""
        import time
        
        # Start total timer
        total_start_time = time.time()
        
        try:
            print("\n" + "="*60)
            print(" SYSCO PRODUCT SCRAPER - MODULAR ARCHITECTURE")
            print("="*60)
            
            # Print configuration
            print(" Configuration loaded:")
            print(f"   • ZIP Code: {self.config.zip_code}")
            print(f"   • Headless: {self.config.headless}")
            print(f"   • Categories: {', '.join(self.config.categories_to_scrape)}")
            print(f"   • Max Products: {self.config.max_products}")
            print(f"   • Output: {self.config.output_file}")
            print()
            
            print(" Starting scraper timer...")
            print(" Starting Sysco product scraper with modular architecture...")
            
            # Step 1: Initialize browser and components
            browser_start_time = time.time()
            page = await self.browser_manager.start_browser()
            self.category_navigator = CategoryNavigator(page)
            self.product_scraper = ProductScraper(page)
            browser_time = time.time() - browser_start_time
            print(f"⚡ Browser startup: {browser_time:.2f}s")
            
            # Step 2: Navigate to Sysco and handle initial setup
            session_start_time = time.time()
            if not await self._setup_sysco_session():
                print("❌ Failed to setup Sysco session")
                return False
            session_time = time.time() - session_start_time
            print(f"⚡ Session setup: {session_time:.2f}s")
            
            # Step 3: Process each category
            collection_start_time = time.time()
            category_to_urls_map = await self._collect_product_urls()
            collection_time = time.time() - collection_start_time
            print(f"⚡ URL collection: {collection_time:.2f}s")
            
            if not category_to_urls_map:
                print("❌ No product URLs found")
                return False
            
            # Step 4: Scrape individual products
            scraping_start_time = time.time()
            await self._scrape_products(category_to_urls_map)
            scraping_time = time.time() - scraping_start_time
            print(f"⚡ Product scraping: {scraping_time:.2f}s")
            
            # Step 5: Export results
            export_start_time = time.time()
            success = self.csv_exporter.export_products(self.products)
            export_time = time.time() - export_start_time
            print(f"⚡ Data export: {export_time:.2f}s")
            
            # Calculate and display total time
            total_time = time.time() - total_start_time
            
            print("\n" + "="*60)
            print("🏁 SCRAPING PERFORMANCE SUMMARY")
            print("="*60)
            print(f"⏱️ Total scraping time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
            print(f"🚀 Browser startup: {browser_time:.2f}s ({browser_time/total_time*100:.1f}%)")
            print(f"🔑 Session setup: {session_time:.2f}s ({session_time/total_time*100:.1f}%)")
            print(f"🔗 URL collection: {collection_time:.2f}s ({collection_time/total_time*100:.1f}%)")
            print(f"📊 Product scraping: {scraping_time:.2f}s ({scraping_time/total_time*100:.1f}%)")
            print(f"💾 Data export: {export_time:.2f}s ({export_time/total_time*100:.1f}%)")
            
            # Performance metrics
            total_products = len(self.products)
            if total_products > 0:
                avg_time_per_product = scraping_time / total_products
                print(f"📊 Average time per product: {avg_time_per_product:.2f}s")
                print(f"📊 Products per minute: {60/avg_time_per_product:.1f}")
            
            print("="*60)
            print(f"✅ Scraping completed! Found {len(self.products)} valid products")
            return success
            
        except Exception as e:
            total_time = time.time() - total_start_time
            print(f" Error in main scraper after {total_time:.2f}s: {e}")
            return False
        finally:
            await self.browser_manager.close_browser()
    
    async def _setup_sysco_session(self) -> bool:
        """Setup initial Sysco session (navigation, login, zip code)"""
        print("🔧 Setting up Sysco session...")
        
        # Navigate and handle guest login
        if not await self.browser_manager.navigate_to_sysco():
            print("❌ Failed to navigate to Sysco")
            return False
        
        # Handle zip code modal
        if not await self.browser_manager.handle_zip_code_modal():
            print("⚠️ Failed to handle zip code modal, continuing anyway...")
        
        print("✅ Sysco session setup complete")
        return True
    
    async def _collect_product_urls(self) -> Dict[str, List[str]]:
        """Collect product URLs from all configured categories"""
        print("📂 Collecting product URLs from categories...")
        category_to_urls_map: Dict[str, List[str]] = {}
        
        for i, category in enumerate(self.config.categories_to_scrape):
            print(f"\n📁 Processing category {i+1}/{len(self.config.categories_to_scrape)}: {category}")
            
            # Select the category
            if not await self.category_navigator.select_category(category):
                print(f"⚠️ Skipping category '{category}' - could not select")
                continue
            
            # Get products from this category
            category_url = await self.category_navigator.get_current_category_url()
            product_urls = await self.product_scraper.scrape_category_products(category_url)
            
            if product_urls:
                # Use list(set(...)) to remove duplicates within the category
                category_to_urls_map[category] = list(set(product_urls))
            
            print(f"✅ Found {len(product_urls)} products in '{category}'")
            
            # Return to dashboard for next category (if not last)
            if i < len(self.config.categories_to_scrape) - 1:
                await self.category_navigator.return_to_dashboard()
            
            # Throttle between categories
            await self.browser_manager.throttle()
        
        total_urls = sum(len(urls) for urls in category_to_urls_map.values())
        print(f"📊 Total product URLs collected: {total_urls}")
        return category_to_urls_map
    
    async def _scrape_products(self, category_to_urls_map: Dict[str, List[str]]):
        """Scrape individual product data from URLs with performance optimizations"""
        print("🔍 Scraping individual product data...")
        
        # Flatten the dictionary for total count and limiting, while keeping category association
        all_products_to_scrape = []
        for category, urls in category_to_urls_map.items():
            for url in urls:
                all_products_to_scrape.append({'url': url, 'category': category})

        # Apply product limit if configured
        max_products = self.config.max_products or len(all_products_to_scrape)
        products_to_process = all_products_to_scrape[:max_products]
        
        print(f"📝 Scraping {len(products_to_process)} products (limit: {self.config.max_products})")
        
        # 🚀 PERFORMANCE OPTIMIZATION: Use async scraping based on configuration
        if (self.config.enable_async_scraping and 
            len(products_to_process) <= self.config.async_batch_size):
            print(f"⚡ Using asynchronous scraping for {len(products_to_process)} products...")
            await self._scrape_products_async(products_to_process)
        else:
            print(f"🔄 Using sequential scraping for {len(products_to_process)} products...")
            await self._scrape_products_sequential(products_to_process)
        
        print(f"📊 Successfully scraped {len(self.products)} valid products")
    
    async def _scrape_products_sequential(self, products_to_process: List[Dict]):
        """Sequential product scraping (original method)"""
        for i, product_info in enumerate(products_to_process):
            product_url = product_info['url']
            category = product_info['category']
            print(f"🔍 Scraping product {i+1}/{len(products_to_process)} from '{category}': {product_url}")
            
            try:
                import time
                start_time = time.time()
                product_data = await self.product_scraper.scrape_product(product_url, category)
                scrape_time = time.time() - start_time
                
                if product_data.is_valid():
                    self.products.append(product_data)
                    print(f"✅ Successfully scraped in {scrape_time:.2f}s: {product_data.product_name[:50]}...")
                else:
                    print(f"⚠️ Skipped invalid product data (took {scrape_time:.2f}s)")
                
            except Exception as e:
                print(f"❌ Error scraping product {i+1}: {e}")
            
            # Throttle between products
            await self.browser_manager.throttle()
    
    async def _scrape_products_async(self, products_to_process: List[Dict]):
        """Asynchronous product scraping for better performance"""
        import time
        
        async def scrape_single_product(product_info: Dict, index: int):
            """Scrape a single product with error handling"""
            product_url = product_info['url']
            category = product_info['category']
            
            try:
                start_time = time.time()
                print(f"⚡ [{index+1}] Starting async scrape: {product_url}")
                
                product_data = await self.product_scraper.scrape_product(product_url, category)
                scrape_time = time.time() - start_time
                
                if product_data.is_valid():
                    print(f"✅ [{index+1}] Completed in {scrape_time:.2f}s: {product_data.product_name[:50]}...")
                    return product_data
                else:
                    print(f"⚠️ [{index+1}] Invalid data (took {scrape_time:.2f}s)")
                    return None
                    
            except Exception as e:
                print(f"❌ [{index+1}] Error: {e}")
                return None
        
        # Create tasks for concurrent execution
        tasks = [
            scrape_single_product(product_info, i) 
            for i, product_info in enumerate(products_to_process)
        ]
        
        # Execute tasks concurrently with some throttling
        print(f"🚀 Starting {len(tasks)} concurrent scraping tasks...")
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        print(f"⚡ Async scraping completed in {total_time:.2f}s (avg: {total_time/len(tasks):.2f}s per product)")
        
        # Process results
        for result in results:
            if result and not isinstance(result, Exception):
                self.products.append(result)
    
    def get_scraped_products(self) -> List[ProductData]:
        """Get the list of scraped products"""
        return self.products
    
    def get_output_path(self) -> str:
        """Get the path to the output CSV file"""
        return self.csv_exporter.get_output_path()


# Convenience function for backward compatibility
async def run_scraper(config: ScrapingConfig) -> bool:
    """Run the scraper with the given configuration"""
    orchestrator = SyscoScraperOrchestrator(config)
    return await orchestrator.scrape_all_products()
