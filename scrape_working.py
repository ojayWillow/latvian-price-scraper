#!/usr/bin/env python3
"""WORKING Depo Scraper - Based on actual page structure"""
import sqlite3, pandas as pd, time, re, logging
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
        return self.conn.execute('SELECT * FROM products ORDER BY price').fetchall()
    
    def count(self):
        return self.conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]

def scrape_depo():
    """Scrape Depo using the REAL page structure"""
    db = DB()
    
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    
    try:
        logger.info("🔍 Loading Depo category page...")
        driver.get("https://online.depo.lv/products/7481")
        time.sleep(8)  # Wait for JavaScript
        
        # Find ALL links that contain /product/
        all_links = driver.find_elements(By.TAG_NAME, "a")
        product_urls = set()
        
        for link in all_links:
            href = link.get_attribute('href')
            if href and '/product/' in href and 'depo.lv' in href:
                product_urls.add(href)
        
        logger.info(f"📦 Found {len(product_urls)} unique products")
        
        # Scrape each product
        for i, url in enumerate(list(product_urls)[:15], 1):
            try:
                logger.info(f"\n[{i}/15] {url}")
                driver.get(url)
                time.sleep(3)
                
                # Get product ID from URL
                pid = url.split('/product/')[-1].split('?')[0]
                
                # Get name from H1
                try:
                    name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                    logger.info(f"  📝 {name}")
                except:
                    logger.warning("  ⚠️ No name found")
                    continue
                
                # Get price - look for pattern "XX.XX €"
                try:
                    page_html = driver.page_source
                    # Find prices in format "20.59 €"
                    prices = re.findall(r'(\d+\.\d+)\s*€', page_html)
                    if prices:
                        price = float(prices[0])
                        logger.info(f"  💰 €{price}")
                        
                        db.add('Depo', pid, name, price, url)
                        logger.info(f"  ✅ Saved to database")
                    else:
                        logger.warning("  ⚠️ No price found")
                except Exception as e:
                    logger.error(f"  ❌ Error: {e}")
                    
            except Exception as e:
                logger.error(f"  ❌ Failed: {e}")
        
        driver.quit()
        
        # Export to Excel
        products = db.get_all()
        if products:
            data = [{'Store': p[1], 'Product': p[3], 'Price': f"€{p[4]}", 'URL': p[5]} for p in products]
            df = pd.DataFrame(data)
            df.to_excel('depo_prices.xlsx', index=False)
            logger.info(f"\n🎉 SUCCESS! Scraped {len(products)} products")
            logger.info(f"📊 Exported to depo_prices.xlsx")
        else:
            logger.warning("⚠️ No products found")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        driver.quit()

if __name__ == '__main__':
    scrape_depo()
