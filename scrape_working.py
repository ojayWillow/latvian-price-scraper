#!/usr/bin/env python3
import sqlite3, pandas as pd, time, re, logging, argparse
from difflib import SequenceMatcher
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class DB:
    def __init__(self):
        self.conn = sqlite3.connect('products.db')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, store TEXT, product_id TEXT, name TEXT, 
            price REAL, url TEXT, UNIQUE(store, product_id))''')
    
    def add(self, store, pid, name, price, url):
        self.conn.execute('INSERT OR REPLACE INTO products VALUES (NULL,?,?,?,?,?)', 
                         (store, pid, name, price, url))
        self.conn.commit()
    
    def get_all(self):
        return self.conn.execute('SELECT * FROM products').fetchall()

class Scraper:
    def __init__(self):
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    
    def scrape_depo(self, db):
        logger.info("🔍 Scraping Depo...")
        self.driver.get("https://online.depo.lv/products/7481")
        time.sleep(5)
        
        links = [l.get_attribute('href') for l in self.driver.find_elements(By.TAG_NAME, "a") 
                 if l.get_attribute('href') and '/product/' in l.get_attribute('href')]
        
        logger.info(f"Found {len(links)} products")
        
        for i, url in enumerate(links[:20]):
            try:
                self.driver.get(url)
                time.sleep(2)
                
                name = self.driver.find_element(By.TAG_NAME, 'h1').text.strip()
                price_match = re.search(r'(\d+\.\d+)', self.driver.page_source)
                price = float(price_match.group(1)) if price_match else 0
                
                if price > 0:
                    pid = url.split('/product/')[-1]
                    db.add('depo', pid, name, price, url)
                    logger.info(f"✓ {i+1}. {name} - €{price}")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        self.driver.quit()

def export_excel(products):
    data = []
    for p in products:
        data.append({'Store': p[1], 'Name': p[3], 'Price': f"€{p[4]}", 'URL': p[5]})
    pd.DataFrame(data).to_excel('prices.xlsx', index=False)
    logger.info("✅ Exported to prices.xlsx")

def main():
    db = DB()
    scraper = Scraper()
    scraper.scrape_depo(db)
    export_excel(db.get_all())
    logger.info("🎉 Done!")

if __name__ == '__main__':
    main()
