[README.md](https://github.com/user-attachments/files/24935386/README.md)
# YT Subtitle Downloader

**YT Subtitle Downloader** is a desktop automation tool designed to help creators, researchers, and archivists batch-download subtitles from multiple YouTube channels efficiently.

---

## 🚀 Features

- **Multi-Channel Support**  
  Fetch video metadata from multiple YouTube channels at once.

- **Search & Filter**  
  Quickly search through thousands of videos to find exactly what you need.

- **Subtitle Automation**  
  Automatically opens selected videos and downloads subtitles in **SRT** or **VTT** format using a browser automation script.

- **Linear Workflow**  
  Simple and clear process: Step 1 → Step 2 → Step 3.

- **Native OS Dialogs**  
  Choose your download folder and ChromeDriver using native Windows file dialogs.

---

## 🛠️ Prerequisites

Before running the application, make sure you have the following installed:

1. **Python 3.10 or newer**  
   https://www.python.org/downloads/

2. **Google Chrome**  
   https://www.google.com/chrome/

3. **ChromeDriver** (must match your Chrome version)  
   - Download: https://googlechromelabs.github.io/chrome-for-testing/  
   - Tip: Check your Chrome version at `chrome://settings/help`

4. **Tampermonkey Browser Extension**  
   Required to run the userscript that triggers subtitle downloads.  
   https://www.tampermonkey.net/

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Pragyanand/YTSubtitleDownloader.git
cd YTSubtitleDownloader
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Usage Guide

### Step 1: Start the Application
Run the Flask app:
```bash
python app.py
```
Open your browser and go to:
```
http://127.0.0.1:5000
```

---

### Step 2: Install the Userscript
1. On the app homepage, click **“Download Script”**.
2. Tampermonkey will open — install the script.
3. This userscript automatically clicks the subtitle download button on YouTube pages.

---

### Step 3: Fetch Channel Data
1. Enter your **YouTube Data API Key**  
   Create one from: https://console.cloud.google.com/apis/credentials

2. Enter one or more **Channel IDs**  
   - Format: `UCxxxxxxxxxxxx`
   - Multiple IDs should be comma-separated.

3. Click **Fetch Data** to load all videos.

---

### Step 4: Download Subtitles
1. Select the videos you want subtitles for.
2. Click **Select Save Directory** to choose where files will be stored.
3. Click **Select ChromeDriver** and locate your `chromedriver.exe`.
4. Press **Start Download**.

Chrome will open automatically and process the selected videos.

---

## ⚠️ Troubleshooting

- **Browser closes immediately**  
  Your ChromeDriver version does not match your Chrome version.

- **No videos found**  
  Verify the Channel ID:
  - Must start with `UC`
  - No extra spaces

- **Subtitles not downloading**  
  Ensure:
  - Tampermonkey is enabled
  - The userscript is installed and active

---

## 📌 Notes

- This tool is intended for educational, archival, and personal use.
- Respect YouTube’s Terms of Service and content creator rights.

