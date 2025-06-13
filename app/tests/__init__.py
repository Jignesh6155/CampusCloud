from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def test_homepage_loads():
    driver = webdriver.Chrome()  # Assumes ChromeDriver is installed and in PATH
    driver.get("http://localhost:5000")  # Make sure Flask app is running

    assert "CampusCloud" in driver.page_source
    driver.quit()