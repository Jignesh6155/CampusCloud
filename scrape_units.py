from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import os

# Headless browser setup
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# URL base
base_url = "https://handbook.curtin.edu.au/?study_type=unit&page={}&search_text="
all_data = []

def scrape_page(page):
    try:
        print(f"Scraping page {page}...")
        driver.get(base_url.format(page))

        # Wait max 10 seconds for expected element
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.search-card__title a"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select("h2.search-card__title a")

        count = 0
        for card in cards:
            full_text = card.get_text(strip=True, separator=" ")
            parts = full_text.split(" ", 1)
            if len(parts) == 2:
                code = parts[0].strip()
                title = parts[1].strip()
                all_data.append([code, title])
                count += 1
        print(f"  ➤ {count} units found.")
    except Exception as e:
        print(f"  ⚠️ Page {page} skipped. Reason: {str(e)}")

try:
    for page in range(1, 189):  # Total 188 pages
        scrape_page(page)
        time.sleep(1)  # be polite

finally:
    driver.quit()

# Save to CSV
os.makedirs("app/data", exist_ok=True)
with open("app/data/Units_CURTIN.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Unit Code", "Title"])
    writer.writerows(all_data)

print(f"\n✅ Done. Scraped {len(all_data)} units. Saved to app/data/Units_CURTIN.csv")
