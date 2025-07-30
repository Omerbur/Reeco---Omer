import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ZIP_CODE = os.getenv('ZIP_CODE', '97035')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
HEADLESS = os.getenv('HEADLESS', 'True').lower() == 'true'
THROTTLE_SECONDS = float(os.getenv('THROTTLE_SECONDS', '0.5'))

# Categories to scrape
CATEGORIES_TO_SCRAPE = [
    "Meat & Seafood",
    "Dairy & Eggs", 
    "Canned & Dry"
]

# Output file
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'sysco_products.csv')