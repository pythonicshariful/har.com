from selenium.webdriver.common.by import By
import random
import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    InvalidArgumentException,
)
import json
import os
import undetected_chromedriver as uc
#===filters===
COUNTY = "Montgomery"
MAX_PRICE = 40000
MAX_PAGES = 20
ACREAGE = True
RESIDENTIAL = True
IP = None  # e.g., "123.45.67.89"
PORT = None  # e.g., "8080"


# === Setup ===
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
profile_path = r"C:\Users\pytho\AppData\Local\BraveSoftware\Brave-Browser\User Data"
chromedriver_path = "chromedriver.exe"

def human_like_delay(min_seconds=1, max_seconds=3):
    """Add random delay to simulate human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_like_scroll(driver):
    """Simulate human-like scrolling"""
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    scroll_positions = [100, 300, 500, 700]
    
    for pos in scroll_positions[:random.randint(1, 3)]:
        if pos < scroll_height:
            driver.execute_script(f"window.scrollTo(0, {pos});")
            human_like_delay(0.5, 1.5)

def calculate_acres(square_feet_str):
    """Convert square feet to acres (1 acre = 43,560 sq ft)"""
    try:
        if square_feet_str and square_feet_str != "N/A":
            # Remove commas and convert to float
            sq_ft = float(square_feet_str.replace(',', ''))
            acres = sq_ft / 43560
            return round(acres, 4)  # Round to 4 decimal places
        return "N/A"
    except (ValueError, TypeError):
        return "N/A"

def extract_property_data(box):
    """Extract property data in the required format"""
    property_data = {
        "address": "N/A",
        "price": "N/A", 
        "acres": "N/A",
        "listing_url": "N/A",
        "additional_info": {}
    }
    
    try:
        # Basic property information
        property_data["listing_url"] = box.find_element(By.CSS_SELECTOR, 'a.photolink').get_attribute("href")
        property_data["address"] = box.find_element(By.CSS_SELECTOR, 'div.cardv2--landscape__content__body__details_address_left_add').text
        property_data["price"] = box.find_element(By.CSS_SELECTOR, 'div.cardv2--landscape__content__body__details_price').text
        
        # Extract features for acres calculation and additional info
        features = {}
        feature_elements = box.find_elements(By.CSS_SELECTOR, '.cardv2--landscape__content__body__details_features_item')
        for feature in feature_elements:
            text = feature.text
            if 'bedrooms' in text.lower():
                features['bedrooms'] = text.split()[0]
            elif 'baths' in text.lower():
                features['bathrooms'] = text.split()[0]
            elif 'sqft' in text.lower() and 'lot' not in text.lower():
                sqft_data = text.split()
                features['square_feet'] = sqft_data[0].replace(',', '')
                if len(sqft_data) > 1 and '/Sqft' in text:
                    features['price_per_sqft'] = sqft_data[1].replace('($', '').replace('/Sqft.)', '')
            elif 'lot' in text.lower() and 'sqft' in text.lower():
                features['lot_sqft'] = text.split()[0].replace(',', '')
            elif 'story' in text.lower():
                features['stories'] = text.split()[0]
            elif 'year built' in text.lower():
                features['year_built'] = text.split()[0]
        
        # Calculate acres from square feet
        if 'square_feet' in features:
            property_data["acres"] = calculate_acres(features['square_feet'])
        elif 'lot_sqft' in features:
            property_data["acres"] = calculate_acres(features['lot_sqft'])
        
        # Property status
        try:
            property_data["additional_info"]["status"] = box.find_element(By.CSS_SELECTOR, '.label--forsale').text
        except:
            property_data["additional_info"]["status"] = "N/A"
        
        # Property description
        try:
            property_data["additional_info"]["description"] = box.find_element(By.CSS_SELECTOR, '.cardv2--landscape__content__body__details_address_left_info').text
        except:
            property_data["additional_info"]["description"] = "N/A"
        
        # Add features to additional_info
        property_data["additional_info"]["features"] = features
        
        # Property badges/tags
        badges = []
        badge_elements = box.find_elements(By.CSS_SELECTOR, '.listingbadges')
        for badge in badge_elements:
            badges.append(badge.text)
        property_data["additional_info"]["badges"] = badges
        
        # Agent information
        try:
            agent_info = {}
            agent_info['agent_name'] = box.find_element(By.CSS_SELECTOR, '.agent_signaturev2__info__agent_name').text
            agent_info['broker_name'] = box.find_element(By.CSS_SELECTOR, '.agent_signaturev2__info__broker_name').text
            property_data["additional_info"]["agent_info"] = agent_info
        except:
            property_data["additional_info"]["agent_info"] = "N/A"
        
        # Property images
        try:
            property_data["additional_info"]["photo_count"] = box.find_element(By.CSS_SELECTOR, '.cardv2--landscape__content__footer_ph').text
        except:
            property_data["additional_info"]["photo_count"] = "N/A"
        
        # Days on market
        try:
            property_data["additional_info"]["days_on_market"] = box.find_element(By.CSS_SELECTOR, '.circle_nimber').text
        except:
            property_data["additional_info"]["days_on_market"] = "N/A"
        
    except Exception as e:
        print(f"Error extracting property data: {e}")
        property_data["additional_info"]["error"] = str(e)
    
    return property_data

def save_progress(properties, filename='har_properties_all_pages.json'):
    """Save progress in real-time"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(properties, f, indent=2, ensure_ascii=False)
        print(f"💾 Progress saved: {len(properties)} properties")
    except Exception as e:
        print(f"Error saving progress: {e}")

def go_to_next_page(driver):
    """Navigate to the next page by clicking the next button"""
    try:
        # Find the next page button using the specific CSS selector from your HTML
        next_button = driver.find_element(By.CSS_SELECTOR, 'li.page-item a.page-link[rel="next"]')
        
        print(f"🔄 Scrolling to next page button...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        human_like_delay(0.5, 1.5)
        
        print(f"🔄 Clicking next page button...")
        driver.execute_script("arguments[0].click();", next_button)
        
        # Wait for page to load
        human_like_delay(3, 5)
        
        # Wait for property cards to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[id^='card_']"))
        )
        
        return True
        
    except NoSuchElementException:
        print("❌ Next page button not found")
        return False
    except Exception as e:
        print(f"Error navigating to next page: {e}")
        return False

def has_next_page(driver):
    """Check if there's a next page available by looking for the next button"""
    try:
        # Look for the next page button that is not disabled
        next_buttons = driver.find_elements(By.CSS_SELECTOR, 'li.page-item a.page-link[rel="next"]')
        
        if next_buttons:
            # Check if the parent li doesn't have disabled class
            parent_li = next_buttons[0].find_element(By.XPATH, "./..")
            if 'disabled' not in parent_li.get_attribute('class'):
                return True
        
        return False
        
    except Exception as e:
        print(f"Error checking for next page: {e}")
        return False

def get_current_page_number(driver):
    """Get current page number from pagination"""
    try:
        # Find the active page in pagination
        active_page = driver.find_element(By.CSS_SELECTOR, 'li.page-item.active .page-link')
        return int(active_page.text)
    except:
        try:
            # Alternative method: check URL
            current_url = driver.current_url
            if 'page=' in current_url:
                return int(current_url.split('page=')[1].split('&')[0])
            return 1
        except:
            return 1



def build_browser_options(enable_exclude_switches=True):
    options = uc.ChromeOptions()
    options.binary_location = brave_path
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    if IP and PORT:
        options.add_argument(f"--proxy-server={IP}:{PORT}")

    # Advanced stealth options
    stealth_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-blink-features",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-popup-blocking",
        "--disable-translate",
        "--disable-default-apps",
        "--disable-component-extensions-with-background-pages",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--enable-features=NetworkService,NetworkServiceInProcess",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
    ]

    for arg in stealth_args:
        options.add_argument(arg)

    if enable_exclude_switches:
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )
        options.add_experimental_option("useAutomationExtension", False)
    else:
        print("ℹ️ Running without excludeSwitches for driver compatibility.")

    return options


def start_driver(enable_exclude_switches=True):
    options = build_browser_options(enable_exclude_switches)
    return uc.Chrome(
        driver_executable_path=chromedriver_path,
        options=options,
        browser_executable_path=brave_path,
    )


try:
    driver = start_driver()
except InvalidArgumentException as e:
    if "excludeSwitches" in str(e):
        print("⚠️ Driver rejected excludeSwitches. Retrying without them...")
        driver = start_driver(enable_exclude_switches=False)
    else:
        raise

# Remove webdriver property
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Override permissions
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# === Load configuration ===
print(f"📋 Configuration loaded:")
print(f"   County: {COUNTY}")
print(f"   Max pages: {MAX_PAGES}")

# === Navigate with human-like behavior ===
url = 'https://www.har.com/'

try:
    # print("Loading HAR.com with enhanced stealth...")
    # driver.get(url)
    
    # human_like_delay(2, 4)
    # try: 
    #     confirm_button = driver.find_element(By.CSS_SELECTOR,'button[aria-label="Confirm"]')
    #     confirm_button.click()
    #     human_like_delay(1, 2)
    #     print("Clicked 'Confirm' button successfully.")
    # except Exception as e:
    #     pass
    # human_like_scroll(driver)
    # human_like_delay(1, 2)
    
    print("Page should be loaded. Check for CAPTCHA...")

    # Click More Filters    
    # more_filters = driver.find_element(By.XPATH, "//a[text()='More Filters']")
    # more_filters.click()
    # human_like_delay(2, 4)
    # print("Clicked 'More Filters' successfully.")
    driver.get('https://www.har.com/search/dosearch?for_sale=1&view=map&showform=1')
    human_like_delay(2, 4)
    print("Navigated to 'https://www.har.com/search/dosearch?for_sale=1&view=map&showform=1' successfully.")
    human_like_scroll(driver)
    human_like_delay(1, 2)
    try: 
        confirm_button = driver.find_element(By.CSS_SELECTOR,'button[aria-label="Confirm"]')
        confirm_button.click()
        human_like_delay(1, 2)
        print("Clicked 'Confirm' button successfully.")
    except Exception as e:
        pass
    
    # Select county from config
    wait = WebDriverWait(driver, 10)
    dropdown = wait.until(EC.presence_of_element_located((By.ID, "fips_code_id")))
    select = Select(dropdown)
    select.select_by_visible_text(COUNTY)
    human_like_delay(2, 4)
    print(f"Selected '{COUNTY}' from the dropdown.")
    
    human_like_scroll(driver)

    if MAX_PRICE:
        try:
            price_max_dropdown = wait.until(EC.presence_of_element_located((By.ID, "listing_price_max_id")))
            price_select = Select(price_max_dropdown)
            price_select.select_by_value(str(MAX_PRICE))
            human_like_delay(2, 4)
            print(f"Selected '${MAX_PRICE}' as maximum price.")
        except Exception as e:
            print(f"Error selecting maximum price: {e}")
    if ACREAGE:
        try:
            acreage = driver.find_element(By.XPATH,"//label[@for='customCheckDisabled3']")
            acreage.click()
            human_like_delay(1, 2)
            print(f"Selected 'Acreage' checkbox.")
        except Exception as e:
            print(f"Error selecting acreage checkbox: {e}")
    if RESIDENTIAL:
        try:
            residential = driver.find_element(By.XPATH,"//label[@for='customCheckDisabled5']")
            residential.click()
            human_like_delay(1, 2)
            print(f"Selected 'Residential' checkbox.")
        except Exception as e:
            print(f"Error selecting residential checkbox: {e}")



    
    # Click Search
    search_btn = driver.find_element(By.XPATH, "//button[text()='Search']")
    search_btn.click()
    human_like_delay(3, 5)
    print("Clicked 'Search' button successfully.")
    
    # Wait for search results to load
    human_like_delay(3, 5)
    human_like_scroll(driver)
    
    # Initialize data collection
    all_properties = []
    output_filename = 'har_properties_all_pages.json'
    
    # Load existing progress if any
    if os.path.exists(output_filename):
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                all_properties = json.load(f)
            print(f"📁 Loaded existing progress: {len(all_properties)} properties")
        except:
            print("🆕 Starting fresh data collection")
    
    current_page = get_current_page_number(driver)
    
    while current_page <= MAX_PAGES:
        print(f"\n{'='*60}")
        print(f"📄 PROCESSING PAGE {current_page}")
        print(f"{'='*60}")
        
        # Wait for page to load completely
        human_like_delay(2, 4)
        human_like_scroll(driver)
        
        # Extract property data from current page
        boxes = driver.find_elements(By.CSS_SELECTOR, "[id^='card_']")
        
        if not boxes:
            print("❌ No property cards found on this page. Stopping.")
            break
        
        print(f"Found {len(boxes)} result boxes on page {current_page}.")
        
        page_properties = []
        
        for index, box in enumerate(boxes):
            print(f"--- Processing property {index + 1} of {len(boxes)} on page {current_page} ---")
            
            property_data = extract_property_data(box)
            page_properties.append(property_data)
            
            # Print brief info
            print(f"✓ {property_data['address'].split(',')[0]} - {property_data['price']}")
            
            # Small delay between processing each property
            human_like_delay(1, 2)
        
        # Add page properties to main list
        all_properties.extend(page_properties)
        
        # Save progress after each page
        save_progress(all_properties, output_filename)
        
        print(f"✅ Page {current_page} completed: {len(page_properties)} properties")
        print(f"📊 Total so far: {len(all_properties)} properties")
        
        # Check if there's a next page
        if current_page >= MAX_PAGES:
            print("🔚 Reached maximum page limit")
            break
            
        if not has_next_page(driver):
            print("🎉 No more pages available. Data collection complete!")
            break
        
        # Go to next page by clicking the next button
        if not go_to_next_page(driver):
            print("❌ Failed to navigate to next page. Stopping.")
            break
        
        # Update current page number
        current_page = get_current_page_number(driver)
        
        # Additional delay between pages
        human_like_delay(2, 4)
    
    # Final save
    save_progress(all_properties, output_filename)
    
    print(f"\n🎉 DATA COLLECTION COMPLETE!")
    print(f"📁 Final file: {output_filename}")
    print(f"📊 Total properties collected: {len(all_properties)}")
    print(f"🔢 Pages processed: {current_page}")
    
    # Display final summary
    properties_with_acres = len([p for p in all_properties if p['acres'] != 'N/A'])
    print(f"🏡 Properties with acres calculated: {properties_with_acres}")
    
    input("Press Enter to close the browser...")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Save whatever data we have on error
    if 'all_properties' in locals():
        save_progress(all_properties, output_filename)
        print(f"💾 Progress saved despite error: {len(all_properties)} properties")
finally:
    driver.quit()