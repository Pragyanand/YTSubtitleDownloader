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
    
    print(f"DEBUG: Looking for source profile at: {source_profile}")

    if not os.path.exists(source_profile):
        print(f"WARNING: Source profile not found at {source_profile}.")
        print(f"DEBUG: Available profiles in {USER_DATA_DIR}:")
        try:
            for item in os.listdir(USER_DATA_DIR):
                if os.path.isdir(os.path.join(USER_DATA_DIR, item)) and (item.startswith("Profile") or item == "Default"):
                    print(f"  - {item}")
        except:
            pass
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
        print(f"DEBUG: Copying profile from {source_profile} to {dest_profile}...")
        shutil.copytree(source_profile, dest_profile, dirs_exist_ok=True)
        print("DEBUG: Profile copied successfully.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to copy profile: {e}")
        return False

from selenium.webdriver.chrome.service import Service
import subprocess

def init_driver(download_dir=None, chromedriver_path=None):
    """
    Initialize Chrome driver with optional specific download directory.
    Uses 'TempChromeProfile' (copied from `PROFILE_DIR`) to ensure Extensions work.
    """
    
    # 1. SETUP PROFILE
    print("Setting up temporary profile for automation...")
    if not setup_temp_profile():
        print("Profile setup failed or skipped. Proceeding without user data...")
    
    chrome_options = Options()
    
    # --- ANTI-DETECTION MEASURES ---
    # Enable extensions
    chrome_options.add_argument("--enable-extensions")
    
    # Remove automation indicators
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Normal window size (bots often use weird sizes)
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # Disable infobars
    chrome_options.add_argument("--disable-infobars")
    
    # 2. USE THE TEMP PROFILE
    chrome_options.add_argument(f"user-data-dir={TEMP_USER_DATA_DIR}")
    chrome_options.add_argument(f"profile-directory={TEMP_PROFILE_DIR}")
    
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
    
    # Detach: keeps browser open after script ends
    chrome_options.add_experimental_option("detach", True)
    
    # Exclude automation switches - CRITICAL for anti-detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # LOGIC: Custom Path OR System Defaults
    service = Service(executable_path=chromedriver_path) if chromedriver_path and os.path.exists(chromedriver_path) else Service()
    
    # Suppress CMD window
    service.creation_flags = subprocess.CREATE_NO_WINDOW
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # --- STEALTH: Hide webdriver property via CDP ---
    try:
        # This removes the navigator.webdriver = true flag
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Spoof plugins to look like a real browser
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Spoof languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """
        })
        print("DEBUG: Anti-detection scripts injected successfully.")
    except Exception as e:
        print(f"Warning: Could not inject anti-detection script: {e}")
        
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
                
                # --- FAILSAFE 1: Wait for page to stabilize ---
                time.sleep(3)
                
                # --- FAILSAFE 2: Trigger yt-navigate-finish event via JS ---
                # This mimics YouTube's SPA navigation event that Tampermonkey listens for
                try:
                    driver.execute_script("""
                        window.dispatchEvent(new CustomEvent('yt-navigate-finish'));
                        console.log('[Selenium] Dispatched yt-navigate-finish event');
                    """)
                except Exception as js_err:
                    print(f"Warning: Could not inject JS event: {js_err}")
                
                # --- FAILSAFE 3: Refresh page if first video (forces full reload trigger) ---
                if i == 0:
                    time.sleep(2)
                    driver.refresh()
                    time.sleep(3)
                    # Re-dispatch event after refresh
                    try:
                        driver.execute_script("window.dispatchEvent(new CustomEvent('yt-navigate-finish'));")
                    except:
                        pass
                
                # Dynamic Wait Time: 25s for first video, 15s for subsequent
                wait_seconds = 25 if i == 0 else 15
                
                # Wait for the script
                for s in range(wait_seconds, 0, -1):
                    if s % 5 == 0: # Update every 5 seconds to show life
                        yield f"    ...waiting {s}s for script execution..."
                    time.sleep(1)
            except Exception as e:
                yield f"Error opening {url}: {str(e)}"
        
        yield "All videos processed."
        
    except GeneratorExit:
        # Client disconnected, clean exit without yielding
        pass
    except Exception as e:
        yield f"Critical Error: {str(e)}"
    finally:
        if driver:
            # Do NOT yield here to avoid 'generator ignored GeneratorExit' if client disconnected
            # Just print to console for server logs
            print("Closing Browser due to generator exit/completion...")
            try:
                driver.quit()
            except:
                pass
            print("Browser Session Ended.")
