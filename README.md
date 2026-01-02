# Latvian Price Scraper

Price comparison scraper for Latvian building material stores: **Depo**, **K-Senukai**, **Kursi**, **Buvserviss**, and **Cenuklubs**.

## Features

✅ **Multi-Store Scraping** - Scrapes all 5 major Latvian building material stores
✅ **Smart Product Matching** - Uses similarity algorithm to find matching products across stores
✅ **Price Comparison** - Automatically identifies the cheapest store for each product
✅ **Excel Export** - Exports results to Excel files for easy analysis
✅ **SQLite Database** - Stores all products in a local database
✅ **Selenium-Based** - Handles JavaScript-heavy websites

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ojayWillow/latvian-price-scraper.git
cd latvian-price-scraper

# Install dependencies
pip install selenium pandas openpyxl webdriver-manager
```

### Usage

#### Option 1: Comprehensive Scraper (Recommended)

Scrape all stores and get price comparisons:

```bash
python scrape_all_stores.py
```

This will:
1. Scrape products from all 5 stores (10 products per store by default)
2. Store them in `all_stores.db` SQLite database
3. Find matching products across stores
4. Generate two Excel files:
   - `all_products.xlsx` - All scraped products
   - `price_comparison.xlsx` - Matching products with price comparison

#### Option 2: Single Store Scraper

Scrape only Depo:

```bash
python scrape_working.py
```

Generates `depo_prices.xlsx`

## Output Files

### all_products.xlsx
Contains all scraped products with:
- Store name
- Product ID
- Product name
- Price
- URL

### price_comparison.xlsx
Contains matching products across stores with:
- Product name
- Price at each store (if available)
- URL for each store
- **Cheapest Store** indicator
- **Best Price**

## Configuration

### Adjust Number of Products

Edit `scrape_all_stores.py` and modify the limit parameter:

```python
def main():
    db = DB()
    
    # Change limit from 10 to your desired number
    scrape_depo(db, limit=50)  # Scrape 50 products from Depo
    scrape_ksenukai(db, limit=50)
    # ... etc
```

### Adjust Similarity Threshold

Change how strict the product matching is (0.0 to 1.0, default 0.6):

```python
matches = find_matching_products(products, threshold=0.7)  # Stricter matching
```

## How It Works

1. **Scraping**: Uses Selenium WebDriver to navigate each store's website
2. **Extraction**: Finds product links, visits each page, and extracts:
   - Product name (from H1 tag)
   - Price (using regex patterns for "XX.XX €")
   - Product ID (from URL)
3. **Storage**: Saves to SQLite database with UNIQUE constraint on (store, product_id)
4. **Matching**: Compares product names using SequenceMatcher to find similar products
5. **Comparison**: Groups matching products and identifies the cheapest option
6. **Export**: Generates Excel reports

## Supported Stores

| Store | URL | Status |
|-------|-----|--------|
| Depo | https://online.depo.lv | ✅ Working |
| K-Senukai | https://www.ksenukai.lv | ✅ Working |
| Kursi | https://www.kursi.lv | ✅ Working |
| Buvserviss | https://www.buvserviss.lv | ✅ Working |
| Cenuklubs | https://cenuklubs.lv | ✅ Working |

## Requirements

- Python 3.10+
- selenium
- pandas
- openpyxl
- webdriver-manager

## Contributing

Feel free to fork the project and create a pull request with new features or refactoring of the code. Also feel free to make issues with problems or suggestions to new features.

## Use Cases

- 🏠 **Home Renovation**: Find the best prices for building materials
- 💰 **Cost Optimization**: Compare prices before making bulk purchases
- 📊 **Market Research**: Track price trends across stores
- 🔍 **Product Discovery**: Find which stores carry specific products

## Example Output

```
=== SCRAPING DEPO ===
Found 156 products
[1/10] https://online.depo.lv/product/12345
  ✅ Cement 50kg - €5.99

=== FOUND 12 MATCHING PRODUCT GROUPS ===

=== PRICE COMPARISON SUMMARY ===
Product: Cement 50kg Portland...
  Best price: €5.99 at Depo

Product: Paint White Interior 10L...
  Best price: €12.49 at K-Senukai

🎉 SCRAPING COMPLETE!
```

## License

MIT License - See LICENSE file for details

## Notes

- Scraping may take some time due to page load times
- The scraper respects robots.txt where applicable
- Use responsibly and don't overload the servers
- Prices and availability are subject to change
