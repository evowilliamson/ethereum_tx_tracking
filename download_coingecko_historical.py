#!/usr/bin/env python3
"""
Download historical price data from CoinGecko as CSV.
Uses undetected-chromedriver to avoid Cloudflare detection.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import sys


def wait_for_page_load(driver):
    """
    Wait for page to load and check for Cloudflare challenge.
    Waits indefinitely until the page loads (allows manual captcha solving).
    Returns True when page loaded successfully.
    """
    print("Waiting for page to load...")
    
    # Wait a moment for page to start loading
    time.sleep(2)
    
    # Check for Cloudflare challenge indicators
    challenge_detected = False
    
    try:
        # Check page title
        page_title = driver.title.lower()
        if "just a moment" in page_title or "checking your browser" in page_title:
            challenge_detected = True
            print("  ⚠ Cloudflare challenge detected in page title")
        
        # Check for challenge iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            iframe_id = iframe.get_attribute("id") or ""
            if ("challenges.cloudflare.com" in src or 
                "turnstile" in src or
                (iframe_id and iframe_id.startswith("cf-chl-widget-"))):
                challenge_detected = True
                print(f"  ⚠ Cloudflare Turnstile iframe detected: id='{iframe_id}'")
                break
    except:
        pass
    
    # If challenge detected, wait indefinitely for it to be solved
    if challenge_detected:
        print("  Please solve the captcha manually in the browser window.")
        print("  The script will wait until the page loads...")
        
        while True:
            # Check if export button is present (means page loaded successfully)
            try:
                export_button = driver.find_element(By.ID, "export")
                if export_button:
                    print("  ✓ Page loaded successfully!")
                    return True
            except:
                pass
            
            # Check if we're on CoinGecko page (not challenge page)
            try:
                current_url = driver.current_url
                if "coingecko.com" in current_url and "challenge" not in current_url.lower():
                    # Give it a moment and check for export button
                    time.sleep(1)
                    try:
                        export_button = driver.find_element(By.ID, "export")
                        if export_button:
                            print("  ✓ Challenge solved, page loaded!")
                            return True
                    except:
                        pass
            except:
                pass
            
            time.sleep(2)  # Check every 2 seconds
    
    # No challenge detected, check if page loaded
    try:
        export_button = driver.find_element(By.ID, "export")
        if export_button:
            print("  ✓ Page loaded successfully (no challenge detected)")
            return True
    except:
        pass
    
    # Wait a bit more and check again
    time.sleep(2)
    try:
        export_button = driver.find_element(By.ID, "export")
        if export_button:
            print("  ✓ Page loaded successfully")
            return True
    except:
        pass
    
    print("  ⚠ Could not find export button - page may not have loaded")
    return True  # Continue anyway, let it fail later if needed


def download_historical_data(coin_id="bitcoin", download_dir=None):
    """
    Download historical data CSV from CoinGecko for a given coin.
    
    Args:
        coin_id: CoinGecko coin ID (e.g., "bitcoin", "zcash", "ethereum")
        download_dir: Directory to save the CSV file (defaults to current directory)
    """
    if download_dir is None:
        download_dir = os.getcwd()
    
    # Ensure download directory exists
    os.makedirs(download_dir, exist_ok=True)
    
    # Set up undetected Chrome options
    options = uc.ChromeOptions()
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    print(f"Starting browser with undetected-chromedriver...")
    print(f"  This should avoid Cloudflare detection compared to regular Selenium.")
    print(f"  Download directory: {download_dir}")
    
    # Use undetected-chromedriver (specify Chrome version 142)
    # This ensures ChromeDriver matches the installed Chrome version
    driver = uc.Chrome(options=options, version_main=142)
    
    try:
        # Set window size
        driver.set_window_size(1920, 1080)
        
        url = f"https://www.coingecko.com/en/coins/{coin_id}/historical_data"
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load (with Cloudflare check)
        # Will wait indefinitely until page loads (allows manual captcha solving)
        wait_for_page_load(driver)
        
        time.sleep(2)  # Additional wait for page to fully load
        
        # Wait for export button to be clickable
        print("Looking for export button...")
        wait = WebDriverWait(driver, 30)
        
        # Find export button
        export_button = None
        try:
            export_button = wait.until(
                EC.presence_of_element_located((By.ID, "export"))
            )
            print("Found export button by ID")
        except:
            try:
                export_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-coin-historical-data-target='exportButton']"))
                )
                print("Found export button by data attribute")
            except:
                export_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[@id='export' or contains(@data-coin-historical-data-target, 'exportButton')]"))
                )
                print("Found export button by XPath")
        
        # Scroll to button
        driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        time.sleep(1)
        
        # Make sure it's clickable
        export_button = wait.until(EC.element_to_be_clickable(export_button))
        
        print("Clicking export button...")
        export_button.click()
        
        # Wait for dropdown to appear
        print("Waiting for dropdown menu to appear...")
        time.sleep(3)
        
        # Find and click the CSV option in the dropdown
        print("Looking for CSV option in dropdown...")
        
        # Try multiple possible selectors for the CSV link
        csv_selectors = [
            (By.XPATH, "//a[contains(text(), '.csv')]"),
            (By.XPATH, "//button[contains(text(), '.csv')]"),
            (By.XPATH, "//*[contains(text(), '.csv')]"),
            (By.XPATH, "//a[contains(text(), 'CSV')]"),
            (By.XPATH, "//button[contains(text(), 'CSV')]"),
            (By.XPATH, "//*[contains(text(), 'CSV')]"),
        ]
        
        csv_option = None
        for by, selector in csv_selectors:
            try:
                csv_option = driver.find_element(by, selector)
                if csv_option.is_displayed():
                    print(f"Found CSV option with selector: {selector}")
                    break
            except:
                continue
        
        if csv_option is None:
            # Try alternative approach
            print("Trying alternative approach to find CSV option...")
            all_links = driver.find_elements(By.TAG_NAME, "a")
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            
            for element in all_links + all_buttons:
                try:
                    text = element.text.lower()
                    if ('.csv' in text or 'csv' in text) and element.is_displayed():
                        csv_option = element
                        print(f"Found CSV option by text: {element.text}")
                        break
                except:
                    continue
        
        if csv_option is None:
            print("Could not find CSV option. Taking screenshot for debugging...")
            driver.save_screenshot("debug_dropdown.png")
            print("Screenshot saved as debug_dropdown.png")
            raise Exception("Could not find CSV option in dropdown.")
        
        print("Clicking CSV option...")
        csv_option.click()
        
        # Wait for download to complete
        print("Waiting for download to complete (this may take a while for large datasets)...")
        time.sleep(10)
        
        print(f"Download should be complete. Check {download_dir} for the CSV file.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing browser...")
        driver.quit()


if __name__ == "__main__":
    coin_id = sys.argv[1] if len(sys.argv) > 1 else "bitcoin"
    download_dir = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    
    print(f"Downloading historical data for {coin_id}...")
    print(f"Download directory: {download_dir}")
    download_historical_data(coin_id, download_dir)
