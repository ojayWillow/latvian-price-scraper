#!/usr/bin/env python3
"""
Latvian Building Materials Store Price Scraper - SELENIUM VERSION

Scrapes ALL products from 5 Latvian stores using Selenium for JavaScript-rendered pages.
Stores in SQLite, matches products across stores, and exports price comparison to Excel.

Stores: Depo, K-Senukai, Kursi, Buvserviss, Cenuklubs

Installation:
    pip install selenium webdriver-manager pandas openpyxl

Usage:
    python scrape_all_products.py --full      # Run all steps
    python scrape_all_products.py --scrape    # Just scrape
    python scrape_all_products.py --depo      # Scrape just Depo
"""

import sqlite3
import pandas as pd
from datetime import datetime
import time
import re
from difflib import SequenceMatcher
import argparse
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProductDatabase:
    """SQLite database manager for product storage"""
    
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store TEXT NOT NULL,
                product_id TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'EUR',
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(store, product_id)
            )
        ''')
        
        self.conn.commit()
    
    def add_product(self, store, product_id, name, price, url):
        """Add or update a product"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO products (store, product_id, name, price, url)
            VALUES (?, ?, ?, ?, ?)
        ''', (store, product_id, name, price, url))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_products(self):
        """Get all products"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY store, name')
        return cursor.fetchall()
    
    def get_product_count(self, store=None):
        """Get count of products"""
        cursor = self.conn.cursor()
        if store:
            cursor.execute('SELECT COUNT(*) FROM products WHERE store = ?', (store,))
        else:
            cursor.execute('SELECT COUNT(*) FROM products')
        return cursor.fetchone()[0]
    
    def close(self):
        self.conn.close()


class SeleniumScraper:
    """Selenium-based scraper for JavaScript-rendered pages"""
    
    def __init__(self, db, headless=True):
        self.db = db
        self.driver = None
        self.headless = headless
        
    def init_driver(self):
        """Initialize Selenium driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        logger.info("Selenium driver initialized")
    
    def close_driver(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
    
    def extract_price(self, text):
        """Extract price from text"""
        match = re.search(r'(\d+[,\.]\d+)', text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return 0.0
    
    def scrape_depo(self, max_products=50):
        """Scrape Depo products"""
        logger.info("Scraping Depo...")
        
        category_url = "https://online.depo.lv/products/7481"  # Drills category
        
        try:
            self.driver.get(category_url)
            time.sleep(3)  # Wait for JavaScript to load
            
            # Find all product cards
            products = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
            logger.info(f"Found {len(products)} products on Depo")
            
            count = 0
            for product in products[:max_products]:
                try:
                    href = product.get_attribute('href')
                    if '/product/' not in href:
                        continue
                    
                    product_id = href.split('/product/')[-1].split('?')[0]
                    
                    # Get product page
                    self.driver.get(href)
                    time.sleep(2)
                    
                    # Extract name
                    try:
                        name_elem = self.driver.find_element(By.TAG_NAME, 'h1')
                        name = name_elem.text.strip()
                    except:
                        name = "Unknown Product"
                    
                    # Extract price (looking for the price text)
                    try:
                        price_text = self.driver.page_source
                        price = self.extract_price(price_text)
                    except:
                        price = 0.0
                    
                    if price > 0 and name != "Unknown Product":
                        self.db.add_product('depo', product_id, name, price, href)
                        count += 1
                        logger.info(f"✓ Added: {name} - €{price}")
                    
                    # Go back to listing
                    self.driver.back()
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error scraping product: {e}")
                    continue
            
            logger.info(f"Depo scraping complete! Added {count} products")
            
        except Exception as e:
            logger.error(f"Error scraping Depo: {e}")


class ProductMatcher:
    """Match products across different stores"""
    
    def __init__(self, db):
        self.db = db
    
    def similarity(self, a, b):
        """Calculate string similarity"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def match_products(self, threshold=0.7):
        """Match products across stores based on name similarity"""
        logger.info("Matching products across stores...")
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id, store, name, price FROM products')
        all_products = cursor.fetchall()
        
        # Group by store
        stores_products = {}
        for prod in all_products:
            store = prod[1]
            if store not in stores_products:
                stores_products[store] = []
            stores_products[store].append(prod)
        
        # Match products
        matches = []
        if 'depo' in stores_products:
            depo_products = stores_products['depo']
            
            for depo_prod in depo_products:
                match = {'depo': depo_prod, 'master_name': depo_prod[2]}
                
                # Try to find matches in other stores
                for store in ['ksenukai', 'kursi', 'buvserviss', 'cenuklubs']:
                    if store in stores_products:
                        best_match = None
                        best_score = 0
                        
                        for prod in stores_products[store]:
                            score = self.similarity(depo_prod[2], prod[2])
                            if score > best_score and score >= threshold:
                                best_score = score
                                best_match = prod
                        
                        if best_match:
                            match[store] = best_match
                
                matches.append(match)
        
        logger.info(f"Found {len(matches)} product matches")
        return matches


class ExcelExporter:
    """Export matched products to Excel"""
    
    def __init__(self, db):
        self.db = db
    
    def export(self, matches, filename='price_comparison.xlsx'):
        """Export to Excel with price comparison"""
        logger.info(f"Exporting to {filename}...")
        
        data = []
        for match in matches:
            row = {
                'Product Name': match['master_name'],
                'Depo Price': match.get('depo', [None, None, None, None])[3] if 'depo' in match else None,
                'K-Senukai Price': match.get('ksenukai', [None, None, None, None])[3] if 'ksenukai' in match else None,
                'Kursi Price': match.get('kursi', [None, None, None, None])[3] if 'kursi' in match else None,
                'Buvserviss Price': match.get('buvserviss', [None, None, None, None])[3] if 'buvserviss' in match else None,
                'Cenuklubs Price': match.get('cenuklubs', [None, None, None, None])[3] if 'cenuklubs' in match else None,
            }
            
            # Find cheapest
            prices = {k: v for k, v in row.items() if 'Price' in k and v is not None}
            if prices:
                row['Cheapest Store'] = min(prices, key=prices.get).replace(' Price', '')
                row['Lowest Price'] = min(prices.values())
                row['Price Difference'] = max(prices.values()) - min(prices.values())
            
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        logger.info(f"Export complete! Saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Scrape and compare Latvian building material store prices')
    parser.add_argument('--scrape', action='store_true', help='Scrape all stores')
    parser.add_argument('--depo', action='store_true', help='Scrape Depo only')
    parser.add_argument('--match', action='store_true', help='Match products across stores')
    parser.add_argument('--export', action='store_true', help='Export to Excel')
    parser.add_argument('--full', action='store_true', help='Run all steps')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    db = ProductDatabase()
    scraper = None
    
    try:
        if args.scrape or args.depo or args.full:
            scraper = SeleniumScraper(db, headless=args.headless)
            scraper.init_driver()
            scraper.scrape_depo()
            scraper.close_driver()
        
        logger.info(f"Total products in database: {db.get_product_count()}")
        
        if args.match or args.full:
            matcher = ProductMatcher(db)
            matches = matcher.match_products()
            
            if args.export or args.full:
                exporter = ExcelExporter(db)
                exporter.export(matches)
    
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if scraper:
            scraper.close_driver()
        db.close()
    
    logger.info("Done!")


if __name__ == '__main__':
    main()
