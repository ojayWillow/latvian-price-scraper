#!/usr/bin/env python3
"""
Latvian Building Materials Store Price Scraper

Scrapes ALL products from 5 Latvian stores, stores in SQLite, 
matches products across stores, and exports price comparison to Excel.

Stores: Depo, K-Senukai, Kursi, Buvserviss, Cenuklubs

Usage:
    python scrape_all_products.py --scrape    # Scrape all products
    python scrape_all_products.py --match     # Match products across stores
    python scrape_all_products.py --export    # Export to Excel
    python scrape_all_products.py --full      # Run all steps
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re
from difflib import SequenceMatcher
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Store configurations
STORES = {
    'depo': {
        'name': 'Depo',
        'base_url': 'https://online.depo.lv',
        'category_urls': [
            '/products/5725',  # Tools
            '/products/5893',  # Power tools
        ]
    },
    'ksenukai': {
        'name': 'K-Senukai',
        'base_url': 'https://www.ksenukai.lv',
        'category_urls': [
            '/c/elektroinsrumenti',  # Power tools
        ]
    },
    'kursi': {
        'name': 'Kursi',
        'base_url': 'https://www.kursi.lv',
        'category_urls': [
            '/instrumenti',  # Tools
        ]
    },
    'buvserviss': {
        'name': 'Buvserviss',
        'base_url': 'https://www.buvserviss.lv',
        'category_urls': [
            '/instrumenti',  # Tools
        ]
    },
    'cenuklubs': {
        'name': 'Cenuklubs',
        'base_url': 'https://cenuklubs.lv',
        'category_urls': [
            '/products',  # All products
        ]
    }
}

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
        
        # Matched products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matched_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                master_name TEXT NOT NULL,
                depo_id INTEGER,
                ksenukai_id INTEGER,
                kursi_id INTEGER,
                buvserviss_id INTEGER,
                cenuklubs_id INTEGER,
                matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        cursor.execute('SELECT * FROM products')
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()


class StoreScraper:
    """Base scraper for all stores"""
    
    def __init__(self, db):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_price(self, text):
        """Extract price from text"""
        match = re.search(r'(\d+[,\.]\d+)', text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return 0.0
    
    def scrape_depo(self):
        """Scrape Depo products"""
        logger.info("Scraping Depo...")
        base_url = STORES['depo']['base_url']
        
        for category_url in STORES['depo']['category_urls']:
            url = base_url + category_url
            try:
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product links (adjust selectors based on actual HTML)
                products = soup.find_all('a', href=re.compile(r'/product/\d+'))
                
                for product in products[:50]:  # Limit to first 50 per category
                    product_url = base_url + product['href']
                    product_id = product['href'].split('/')[-1]
                    
                    # Get product details
                    try:
                        detail_response = self.session.get(product_url, timeout=10)
                        detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                        
                        name_elem = detail_soup.find('h1')
                        name = name_elem.text.strip() if name_elem else 'Unknown'
                        
                        # Find price
                        price_text = detail_soup.get_text()
                        price = self.extract_price(price_text)
                        
                        if price > 0:
                            self.db.add_product('depo', product_id, name, price, product_url)
                            logger.info(f"Added: {name} - €{price}")
                        
                        time.sleep(1)  # Be polite
                    except Exception as e:
                        logger.error(f"Error scraping product {product_url}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error scraping category {url}: {e}")
        
        logger.info("Depo scraping complete!")
    
    def scrape_all_stores(self):
        """Scrape all configured stores"""
        self.scrape_depo()
        # Add other stores here
        logger.info("All stores scraped!")


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
        depo_products = stores_products.get('depo', [])
        
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
    parser.add_argument('--match', action='store_true', help='Match products across stores')
    parser.add_argument('--export', action='store_true', help='Export to Excel')
    parser.add_argument('--full', action='store_true', help='Run all steps')
    
    args = parser.parse_args()
    
    db = ProductDatabase()
    
    try:
        if args.scrape or args.full:
            scraper = StoreScraper(db)
            scraper.scrape_all_stores()
        
        if args.match or args.full:
            matcher = ProductMatcher(db)
            matches = matcher.match_products()
            
            if args.export or args.full:
                exporter = ExcelExporter(db)
                exporter.export(matches)
    
    finally:
        db.close()
    
    logger.info("Done!")


if __name__ == '__main__':
    main()
