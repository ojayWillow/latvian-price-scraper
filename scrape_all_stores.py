#!/usr/bin/env python3
"""Complete Price Scraper for All Latvian Building Material Stores"""
import sqlite3, pandas as pd, time, re, logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class DB:
    def __init__(self):
        self.conn = sqlite3.connect('all_stores.db')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, store TEXT, product_id TEXT, name TEXT, 
            price REAL, url TEXT, UNIQUE(store, product_id))''')
    
    def add(self, store, pid, name, price, url):
        self.conn.execute('INSERT OR REPLACE INTO products VALUES (NULL,?,?,?,?,?)', 
            (store, pid, name, price, url))
        self.conn.commit()
    
    def get_all(self):
        return self.conn.execute('SELECT * FROM products ORDER BY name, price').fetchall()
    
    def count(self):
        return self.conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]

def get_driver():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--disable-gpu')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

def scrape_depo(db, limit=20):
    """Scrape Depo products"""
    logger.info("\n=== SCRAPING DEPO ===")
    driver = get_driver()
    try:
        driver.get("https://online.depo.lv/products/7481")
        time.sleep(8)
        
        all_links = driver.find_elements(By.TAG_NAME, "a")
        product_urls = set()
        for link in all_links:
            href = link.get_attribute('href')
            if href and '/product/' in href and 'depo.lv' in href:
                product_urls.add(href)
        
        logger.info(f"Found {len(product_urls)} products")
        
        for i, url in enumerate(list(product_urls)[:limit], 1):
            try:
                logger.info(f"[{i}/{limit}] {url}")
                driver.get(url)
                time.sleep(3)
                
                pid = url.split('/product/')[-1].split('?')[0]
                name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                
                page_html = driver.page_source
                prices = re.findall(r'(\d+\.\d+)\s*€', page_html)
                if prices:
                    price = float(prices[0])
                    db.add('Depo', pid, name, price, url)
                    logger.info(f"  ✅ {name} - €{price}")
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
    finally:
        driver.quit()

def scrape_ksenukai(db, limit=20):
    """Scrape K-Senukai products"""
    logger.info("\n=== SCRAPING K-SENUKAI ===")
    driver = get_driver()
    try:
        driver.get("https://www.ksenukai.lv/c/buvmateriali/1g3")
        time.sleep(8)
        
        product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
        product_urls = set([link.get_attribute('href') for link in product_links if link.get_attribute('href')])
        
        logger.info(f"Found {len(product_urls)} products")
        
        for i, url in enumerate(list(product_urls)[:limit], 1):
            try:
                logger.info(f"[{i}/{limit}] {url}")
                driver.get(url)
                time.sleep(3)
                
                pid = url.split('/p/')[-1].split('?')[0]
                name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                
                page_html = driver.page_source
                prices = re.findall(r'(\d+[\.,]\d+)\s*€', page_html)
                if prices:
                    price = float(prices[0].replace(',', '.'))
                    db.add('K-Senukai', pid, name, price, url)
                    logger.info(f"  ✅ {name} - €{price}")
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
    finally:
        driver.quit()

def scrape_kursi(db, limit=20):
    """Scrape Kursi products"""
    logger.info("\n=== SCRAPING KURSI ===")
    driver = get_driver()
    try:
        driver.get("https://www.kursi.lv/lv/buvmateriali")
        time.sleep(8)
        
        product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
        product_urls = set([link.get_attribute('href') for link in product_links if link.get_attribute('href')])
        
        logger.info(f"Found {len(product_urls)} products")
        
        for i, url in enumerate(list(product_urls)[:limit], 1):
            try:
                logger.info(f"[{i}/{limit}] {url}")
                driver.get(url)
                time.sleep(3)
                
                pid = url.split('/product/')[-1].split('?')[0]
                name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                
                page_html = driver.page_source
                prices = re.findall(r'(\d+[\.,]\d+)\s*€', page_html)
                if prices:
                    price = float(prices[0].replace(',', '.'))
                    db.add('Kursi', pid, name, price, url)
                    logger.info(f"  ✅ {name} - €{price}")
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
    finally:
        driver.quit()

def scrape_buvserviss(db, limit=20):
    """Scrape Buvserviss products"""
    logger.info("\n=== SCRAPING BUVSERVISS ===")
    driver = get_driver()
    try:
        driver.get("https://www.buvserviss.lv/buvmateriali")
        time.sleep(8)
        
        product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
        product_urls = set([link.get_attribute('href') for link in product_links if link.get_attribute('href')])
        
        logger.info(f"Found {len(product_urls)} products")
        
        for i, url in enumerate(list(product_urls)[:limit], 1):
            try:
                logger.info(f"[{i}/{limit}] {url}")
                driver.get(url)
                time.sleep(3)
                
                pid = url.split('/product/')[-1].split('?')[0]
                name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                
                page_html = driver.page_source
                prices = re.findall(r'(\d+[\.,]\d+)\s*€', page_html)
                if prices:
                    price = float(prices[0].replace(',', '.'))
                    db.add('Buvserviss', pid, name, price, url)
                    logger.info(f"  ✅ {name} - €{price}")
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
    finally:
        driver.quit()

def scrape_cenuklubs(db, limit=20):
    """Scrape Cenuklubs products"""
    logger.info("\n=== SCRAPING CENUKLUBS ===")
    driver = get_driver()
    try:
        driver.get("https://cenuklubs.lv/buvmateriali-un-apdares-materiali")
        time.sleep(8)
        
        product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/prece/"]')
        product_urls = set([link.get_attribute('href') for link in product_links if link.get_attribute('href')])
        
        logger.info(f"Found {len(product_urls)} products")
        
        for i, url in enumerate(list(product_urls)[:limit], 1):
            try:
                logger.info(f"[{i}/{limit}] {url}")
                driver.get(url)
                time.sleep(3)
                
                pid = url.split('/prece/')[-1].split('?')[0]
                name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                
                page_html = driver.page_source
                prices = re.findall(r'(\d+[\.,]\d+)\s*€', page_html)
                if prices:
                    price = float(prices[0].replace(',', '.'))
                    db.add('Cenuklubs', pid, name, price, url)
                    logger.info(f"  ✅ {name} - €{price}")
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
    finally:
        driver.quit()

def similarity(a, b):
    """Calculate similarity between two product names"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_matching_products(products, threshold=0.6):
    """Find matching products across stores"""
    matches = []
    processed = set()
    
    for i, p1 in enumerate(products):
        if i in processed:
            continue
            
        match_group = [p1]
        for j, p2 in enumerate(products[i+1:], i+1):
            if j in processed:
                continue
            if p1[1] != p2[1]:  # Different stores
                if similarity(p1[3], p2[3]) >= threshold:
                    match_group.append(p2)
                    processed.add(j)
        
        if len(match_group) > 1:
            matches.append(match_group)
    
    return matches

def main():
    db = DB()
    
    # Scrape all stores (10 products each for testing)
    scrape_depo(db, limit=10)
    scrape_ksenukai(db, limit=10)
    scrape_kursi(db, limit=10)
    scrape_buvserviss(db, limit=10)
    scrape_cenuklubs(db, limit=10)
    
    # Get all products
    products = db.get_all()
    logger.info(f"\n=== TOTAL PRODUCTS: {len(products)} ===")
    
    # Export all products to Excel
    df_all = pd.DataFrame(products, columns=['ID', 'Store', 'Product ID', 'Name', 'Price', 'URL'])
    df_all.to_excel('all_products.xlsx', index=False)
    logger.info("✅ Exported all products to all_products.xlsx")
    
    # Find matching products
    matches = find_matching_products(products)
    logger.info(f"\n=== FOUND {len(matches)} MATCHING PRODUCT GROUPS ===")
    
    # Create comparison report
    comparison_data = []
    for match_group in matches:
        base_product = match_group[0]
        comparison_row = {'Product': base_product[3]}
        
        for product in match_group:
            store = product[1]
            price = product[4]
            comparison_row[f"{store} Price"] = f"€{price:.2f}"
            comparison_row[f"{store} URL"] = product[5]
        
        # Find cheapest
        prices = [(p[1], p[4]) for p in match_group]
        cheapest = min(prices, key=lambda x: x[1])
        comparison_row['Cheapest Store'] = cheapest[0]
        comparison_row['Best Price'] = f"€{cheapest[1]:.2f}"
        
        comparison_data.append(comparison_row)
    
    if comparison_data:
        df_comp = pd.DataFrame(comparison_data)
        df_comp.to_excel('price_comparison.xlsx', index=False)
        logger.info("✅ Exported price comparison to price_comparison.xlsx")
        
        # Print summary
        logger.info("\n=== PRICE COMPARISON SUMMARY ===")
        for row in comparison_data[:5]:
            logger.info(f"\nProduct: {row['Product'][:50]}...")
            logger.info(f"  Best price: {row['Best Price']} at {row['Cheapest Store']}")
    
    logger.info("\n🎉 SCRAPING COMPLETE!")

if __name__ == '__main__':
    main()
