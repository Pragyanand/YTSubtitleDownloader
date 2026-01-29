import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
WAIT_TIME_SECONDS = 15

# ORIGINAL PROFILE PATHS (Adjust these based on User's system if needed)
# The user's script had: C:\Users\tiwar\AppData\Local\Google\Chrome\User Data
USER_DATA_DIR = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
PROFILE_DIR = "Profile 2"
CHROME_BINARY_LOCATION = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# CREATE A TEMPORARY COPY OF THE PROFILE
TEMP_USER_DATA_DIR = os.path.join(os.getcwd(), "TempChromeProfile")
TEMP_PROFILE_DIR = "Profile 2"

def setup_temp_profile():
    """Creates a temporary copy of the Chrome profile."""
    # Ensure source exists
    source_profile = os.path.join(USER_DATA_DIR, PROFILE_DIR)
    dest_profile = os.path.join(TEMP_USER_DATA_DIR, TEMP_PROFILE_DIR)

    if not os.path.exists(source_profile):
        print(f"WARNING: Source profile not found at {source_profile}. Automation might run without user data.")
        return False
    
    # Remove old temp profile
    if os.path.exists(TEMP_USER_DATA_DIR):
        try:
            shutil.rmtree(TEMP_USER_DATA_DIR)
        except Exception as e:
            print(f"Warning: Could not remove old temp profile: {e}")
    
    # Copy
    try:
        os.makedirs(TEMP_USER_DATA_DIR, exist_ok=True)
        shutil.copytree(source_profile, dest_profile, dirs_exist_ok=True)
        return True
    except Exception as e:
        print(f"ERROR: Failed to copy profile: {e}")
        return False

def open_videos_stream_generator(video_urls, download_dir=None):
    """
    Generator that opens URLs in Chrome and yields status messages.
    """
    if not video_urls:
        yield "Error: No videos selected."
        return

    yield "Initializing Chrome with User Profile..."
    if not setup_temp_profile():
        yield "Warning: Could not copy profile. Proceeding with clean profile..."

    chrome_options = Options()
    if os.path.exists(CHROME_BINARY_LOCATION):
        chrome_options.binary_location = CHROME_BINARY_LOCATION
    
    # User data directory to keep login session
    user_data_dir = os.path.join(os.getcwd(), "selenium_user_data")
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    
    # Performance and stability preferences
    prefs = {
        "profile.default_content_settings.popups": 0,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    
    if download_dir:
        # Ensure absolute path
        abs_download_dir = os.path.abspath(download_dir)
        if not os.path.exists(abs_download_dir):
            os.makedirs(abs_download_dir)
        prefs["download.default_directory"] = abs_download_dir
        
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Detach: keeps browser open after script ends (for manual saving if needed)
    chrome_options.add_experimental_option("detach", True)
    
    service = Service(executable_path=chromedriver_path) if chromedriver_path and os.path.exists(chromedriver_path) else Service()
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def open_videos_generator(video_urls, download_dir=None, chromedriver_path=None):
    """
    Generator that opens videos one by one and yields status messages.
    """
    driver = None
    try:
        yield f"Initializing Chrome... (Download Dir: {download_dir or 'Default'})"
        if chromedriver_path:
             yield f"Using Custom Driver: {chromedriver_path}"
             
        driver = init_driver(download_dir, chromedriver_path)
        yield "Chrome Browser Launched."
        
        # Initial sleep to ensure browser is ready
        time.sleep(3) 

        total = len(video_urls)
        for i, url in enumerate(video_urls):
            yield f"[{i+1}/{total}] Opening: {url}"
            try:
                driver.get(url)
                # Wait for the script
                for s in range(WAIT_TIME_SECONDS, 0, -1):
                    if s % 5 == 0: # Update every 5 seconds to show life
                        yield f"    ...waiting {s}s for script execution..."
                    time.sleep(1)
            except Exception as e:
                yield f"Error opening {url}: {str(e)}"
        
        yield "All videos processed."
        
    except Exception as e:
        yield f"Critical Error: {str(e)}"
    finally:
        if driver:
            yield "Closing Browser..."
            driver.quit()
            yield "Browser Session Ended."
