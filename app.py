from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, Response, stream_with_context
import os
import pandas as pd
from werkzeug.utils import secure_filename
from services.youtube_service import fetch_channel_videos_generator
from services.browser_service import open_videos_stream_generator

from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
# Enable CORS for all routes to allow Tampermonkey (from youtube.com) to call us
CORS(app)

app.secret_key = 'supersecretkey'  # Change this for production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'
app.config['LOG_FILE'] = 'download_logs.json'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

def append_log(data):
    logs = []
    if os.path.exists(app.config['LOG_FILE']):
        try:
            with open(app.config['LOG_FILE'], 'r') as f:
                logs = json.load(f)
        except:
            logs = []
            
    data['timestamp'] = datetime.now().isoformat()
    logs.append(data)
    
    with open(app.config['LOG_FILE'], 'w') as f:
        json.dump(logs, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/log', methods=['POST'])
def log_status():
    data = request.json
    # data expects: { videoId, title, status, message }
    if data:
        append_log(data)
        return jsonify({"status": "logged"}), 200
    return jsonify({"error": "no data"}), 400

@app.route('/logs')
def view_logs():
    logs = []
    if os.path.exists(app.config['LOG_FILE']):
        try:
            with open(app.config['LOG_FILE'], 'r') as f:
                logs = json.load(f)
        except:
            pass
    # Sort by new
    logs.reverse()
    return render_template('logs.html', logs=logs)

@app.route('/open-videos-stream', methods=['POST'])
def open_videos_stream():
    video_urls = request.form.getlist('video_urls')
    download_dir = request.form.get('download_dir')
    chromedriver_path = request.form.get('chromedriver_path')
    
    # If using fetch/XHR, we might receive JSON
    if not video_urls and request.is_json:
        data = request.json
        video_urls = data.get('video_urls', [])
        download_dir = data.get('download_dir')
        chromedriver_path = data.get('chromedriver_path')

    if not video_urls:
         return jsonify({"error": "No videos provided"}), 400

    return Response(stream_with_context(browser_service_open_videos_generator(video_urls, download_dir, chromedriver_path)), 
                   mimetype='text/plain')

@app.route('/fetch-stream')
def fetch_videos_stream():
    api_key = request.args.get('api_key')
    channel_id = request.args.get('channel_id')
    
    if not api_key or not channel_id:
        return "Error: API Key and Channel ID are required", 400

    def generate():
        for message in fetch_channel_videos_generator(api_key, channel_id.strip()):
            yield message + "\n"
            
    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/process')
def process_page():
    return render_template('process.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('process_page'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('process_page'))
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Absolute path for display
        full_path = os.path.abspath(filepath)
        
        # Read the file to display
        df = pd.read_excel(filepath)
        # Convert to records for template
        videos = df.to_dict('records')
        
        return render_template('process.html', videos=videos, filename=filename, full_path=full_path)
    else:
        flash('Allowed file types are .xlsx', 'error')
        return redirect(url_for('process_page'))

        flash(f'Error opening videos: {str(e)}', 'error')
        return redirect(url_for('process_page'))

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

@app.route('/download-script')
def download_script():
    return send_from_directory(app.config['STATIC_FOLDER'], 'userscript.js', as_attachment=True)

@app.route('/api/browse-folder')
def browse_folder():
    """
    Opens a native folder picker dialog on the server (local machine).
    """
    import tkinter as tk
    from tkinter import filedialog
    
    try:
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw() # Hide the main window
        root.attributes('-topmost', True) # Bring dialog to front
        
        folder_selected = filedialog.askdirectory()
        
        root.destroy()
        
        if folder_selected:
            return jsonify({"path": folder_selected.replace('/', '\\')}) # Windows path fmt
        return jsonify({"path": ""}) # Cancelled
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/browse-file')
def browse_file():
    """
    Opens a native file picker dialog on the server (local machine).
    """
    import tkinter as tk
    from tkinter import filedialog
    
    try:
        root = tk.Tk()
        root.withdraw() 
        root.attributes('-topmost', True)
        
        file_selected = filedialog.askopenfilename(
            title="Select chromedriver.exe",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        
        root.destroy()
        
        if file_selected:
            return jsonify({"path": file_selected.replace('/', '\\')})
        return jsonify({"path": ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
