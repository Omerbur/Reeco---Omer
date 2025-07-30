#!/usr/bin/env python3
"""
Sysco Product Scraper - Modular Version
Main entry point for the refactored Sysco scraper with clean architecture
"""

import asyncio
import os
from dotenv import load_dotenv
from scraper.models import ScrapingConfig
from scraper.main import SyscoScraperOrchestrator


def load_config() -> ScrapingConfig:
    """Load configuration from environment variables"""
    load_dotenv()
    
    return ScrapingConfig(
        zip_code=os.getenv('ZIP_CODE', '97035'),
        headless=os.getenv('HEADLESS', 'False').lower() == 'true',
        categories_to_scrape=[
            "Meat & Seafood",
            "Dairy & Eggs", 
            "Canned & Dry"
        ],
        max_products=10,  # Set to 10 for testing, remove or increase for full scraping
        output_dir=os.getenv('OUTPUT_DIR', 'output'),
        output_file='sysco_products.csv'
    )


async def main():
    """Main entry point"""
    print("=" * 60)
    print("🏪 SYSCO PRODUCT SCRAPER - MODULAR ARCHITECTURE")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        print(f"📋 Configuration loaded:")
        print(f"   • ZIP Code: {config.zip_code}")
        print(f"   • Headless: {config.headless}")
        print(f"   • Categories: {', '.join(config.categories_to_scrape)}")
        print(f"   • Max Products: {config.max_products}")
        print(f"   • Output: {config.output_dir}/{config.output_file}")
        print()
        
        # Initialize and run scraper
        orchestrator = SyscoScraperOrchestrator(config)
        success = await orchestrator.run_scraper()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 SCRAPING COMPLETED SUCCESSFULLY!")
            print(f"📁 Results saved to: {orchestrator.get_output_path()}")
            print(f"📊 Products scraped: {len(orchestrator.get_scraped_products())}")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ SCRAPING FAILED")
            print("=" * 60)
            
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
