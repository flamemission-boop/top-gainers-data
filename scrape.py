from playwright.sync_api import sync_playwright
from datetime import date
import csv
import os
URL = "https://www.screener.in/screens/3405656/daily-top-gainers/"
TODAY = date.today().isoformat()
DATA_FILE = "data/industry_data.csv"
STOCKS_FILE = "data/stocks_data.csv"
os.makedirs("data", exist_ok=True)
def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120 Safari/537.36"
            )
        )
        page = context.new_page()
        
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            browser.close()
            raise Exception(f"Failed to load page: {str(e)}")
        
        stocks_rows = []
        try:
            page.wait_for_selector("table", timeout=15000)
            table = page.locator("table").first
            rows = table.locator("tbody tr").all()
            
            for row in rows:
                cells = row.locator("td").all()
                if len(cells) >= 2:
                    name_cell = cells[0]
                    link = name_cell.locator("a").first
                    stock_name = link.inner_text().strip() if link.count() > 0 else name_cell.inner_text().strip()
                    
                    industry = ""
                    if len(cells) >= 7:
                        industry = cells[6].inner_text().strip()
                    
                    change_pct = ""
                    if len(cells) >= 5:
                        change_pct = cells[4].inner_text().strip().replace("%", "")
                    
                    if stock_name:
                        stocks_rows.append([TODAY, stock_name, industry, change_pct])
        except Exception as e:
            page.screenshot(path="debug_stocks_screenshot.png")
            print(f"Warning: Could not scrape stocks table: {str(e)}")
        
        industry_rows = []
        try:
            page.wait_for_selector("button:has-text('Industry')", timeout=15000)
            page.click("button:has-text('Industry')")
            
            page.wait_for_timeout(2000)
            
            try:
                page.wait_for_selector("div[role='menu'] label", timeout=15000)
                items = page.locator("div[role='menu'] label").all()
            except:
                page.wait_for_selector("label input[type='checkbox']", timeout=15000)
                items = page.locator("label:has(input[type='checkbox'])").all()
            
            for item in items:
                text = item.inner_text().strip()
                if "-" in text:
                    industry, count = text.rsplit("-", 1)
                    industry_rows.append([TODAY, industry.strip(), int(count.strip())])
            
        except Exception as e:
            page.screenshot(path="debug_screenshot.png")
            browser.close()
            raise Exception(f"Failed to scrape industry data: {str(e)}")
        
        browser.close()
        
        if not industry_rows:
            raise Exception("No industry data found on the page")
        
        file_exists = os.path.isfile(DATA_FILE)
        with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["date", "industry", "count"])
            writer.writerows(industry_rows)
        
        if stocks_rows:
            stocks_exists = os.path.isfile(STOCKS_FILE)
            with open(STOCKS_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not stocks_exists:
                    writer.writerow(["date", "stock", "industry", "change_pct"])
                writer.writerows(stocks_rows)
            print(f"Saved {len(stocks_rows)} stocks to {STOCKS_FILE}")
        
        print(f"Saved {len(industry_rows)} industries to {DATA_FILE}")

if __name__ == "__main__":
    scrape()
