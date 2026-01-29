from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
import shutil

# --- FILE CONFIGURATION ---
VIDEO_LINKS_FILE = "youtube.txt"
WAIT_TIME_SECONDS = 15

# ====================================================================
# CHROME OPTIONS SETUP: LAUNCH WITH EXTENSIONS
# ====================================================================

# ORIGINAL PROFILE PATHS
USER_DATA_DIR = r"C:\Users\tiwar\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR = "Profile 2"
CHROME_BINARY_LOCATION = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# CREATE A TEMPORARY COPY OF THE PROFILE
TEMP_USER_DATA_DIR = os.path.join(os.getcwd(), "TempChromeProfile")
TEMP_PROFILE_DIR = "Profile 2"

def setup_temp_profile():
    """Creates a temporary copy of the Chrome profile to avoid conflicts."""
    source_profile = os.path.join(USER_DATA_DIR, PROFILE_DIR)
    dest_profile = os.path.join(TEMP_USER_DATA_DIR, TEMP_PROFILE_DIR)
    
    # Remove old temp profile if exists
    if os.path.exists(TEMP_USER_DATA_DIR):
        try:
            shutil.rmtree(TEMP_USER_DATA_DIR)
            print("Removed old temporary profile.")
        except Exception as e:
            print(f"Warning: Could not remove old temp profile: {e}")
    
    # Copy the profile
    try:
        print(f"Copying profile from {source_profile}...")
        os.makedirs(TEMP_USER_DATA_DIR, exist_ok=True)
        shutil.copytree(source_profile, dest_profile, dirs_exist_ok=True)
        print("Profile copied successfully.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to copy profile: {e}")
        return False

# Setup Chrome Options
chrome_options = Options()
chrome_options.binary_location = CHROME_BINARY_LOCATION

# Use the temporary profile directory
chrome_options.add_argument(f"user-data-dir={TEMP_USER_DATA_DIR}")
chrome_options.add_argument(f"profile-directory={TEMP_PROFILE_DIR}")

# Stability fixes
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")

# Additional fixes for profile conflicts
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--remote-debugging-port=9222")  # Use specific port
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Function to read and parse links from the text file
def get_video_links(filepath):
    """Reads the video URLs from a text file, expecting comma-separated values."""
    if not os.path.exists(filepath):
        print(f"ERROR: Video links file not found at {filepath}")
        return []
    
    with open(filepath, 'r') as f:
        content = f.read().strip()
        if not content:
            return []
        
        links = [link.strip() for link in content.split(',') if link.strip()]
        return links

# ====================================================================
# DRIVER LAUNCH & URL ITERATION
# ====================================================================

print(f"--- Attempting to read links from {VIDEO_LINKS_FILE} ---")
video_urls = get_video_links(VIDEO_LINKS_FILE)

if not video_urls:
    print("No valid video links found. Exiting script.")
else:
    print(f"Found {len(video_urls)} links to process.")
    
    # Setup temporary profile
    if not setup_temp_profile():
        print("Failed to setup temporary profile. Exiting.")
        exit(1)
    
    driver = None
    try:
        print("\n--- Launching Chrome ---")
        print("IMPORTANT: Make sure ALL Chrome windows are closed before running this script!")
        time.sleep(2)  # Give user time to read the message
        
        # Initialize Driver with the configured options
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window() 
        print(f"SUCCESS: Chrome launched with profile extensions.")
        
        # Wait a bit for extensions to load
        time.sleep(3)
        
        # Iterate through all the collected URLs
        for i, url in enumerate(video_urls):
            print(f"\n--- Opening Link {i + 1}/{len(video_urls)} ---")
            print(f"URL: {url}")
            
            try:
                # Open the URL
                driver.get(url)
                print(f"Page loaded. Waiting {WAIT_TIME_SECONDS} seconds...")
                
                # Wait for the specified duration
                time.sleep(WAIT_TIME_SECONDS)
                
            except Exception as e:
                print(f"ERROR loading link {i + 1}: {e}")
                continue
        
        print("\n✓ All videos processed successfully.")
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e.__class__.__name__}")
        print(f"Details: {e}")
        print("\nTROUBLESHOOTING STEPS:")
        print("1. Close ALL Chrome windows (including background processes)")
        print("2. Check Task Manager and end any Chrome.exe processes")
        print("3. Run this script again")
        
    finally:
        # Always quit the driver when finished
        if driver:
            print("\nClosing browser...")
            driver.quit()
            print("Browser closed.")
        
        # Optional: Clean up temp profile
        # Uncomment the lines below if you want to delete the temp profile after each run
        # try:
        #     shutil.rmtree(TEMP_USER_DATA_DIR)
        #     print("Temporary profile cleaned up.")
        # except:
        #     pass

print("\n--- Script Finished ---")