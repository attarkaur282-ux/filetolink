from flask import Flask, request, jsonify, render_template_string, send_file, redirect, url_for
import os
import uuid
import time
import json
from datetime import datetime
import urllib.parse

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB

# ============================================
# CONFIG
# ============================================
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# File database
DB_FILE = 'files.json'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

# ============================================
# DATABASE FUNCTIONS
# ============================================
def load_files():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_files(files):
    with open(DB_FILE, 'w') as f:
        json.dump(files, f, indent=2)

# ============================================
# HTML TEMPLATE
# ============================================
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>EXPLOITS - File Upload</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Rajdhani', 'Segoe UI', sans-serif;
            background: #0a0a0f;
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(ellipse at 20% 50%, rgba(255,153,51,0.05) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, rgba(0,255,102,0.05) 0%, transparent 60%);
            z-index: 0;
            animation: bgPulse 8s ease-in-out infinite alternate;
        }
        @keyframes bgPulse {
            0% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
            background-size: 50px 50px;
            z-index: 0;
            pointer-events: none;
        }
        .container {
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        .glow-card {
            background: rgba(10, 10, 20, 0.88);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 35px 30px 30px;
            border: 1px solid rgba(255,153,51,0.08);
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 60px rgba(255,153,51,0.02);
            animation: cardGlow 5s ease-in-out infinite alternate;
        }
        @keyframes cardGlow {
            0% { border-color: rgba(255,153,51,0.06); }
            100% { border-color: rgba(255,153,51,0.18); }
        }
        .glow-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg at 50% 50%, transparent 0%, rgba(255,153,51,0.04) 25%, transparent 50%, rgba(0,255,102,0.04) 75%, transparent 100%);
            animation: rotateGlow 25s linear infinite;
            pointer-events: none;
        }
        .glow-card > * { position: relative; z-index: 1; }
        
        .header {
            text-align: center;
            margin-bottom: 25px;
        }
        .header .logo {
            font-size: 45px;
            color: #FF9933;
            display: block;
            text-shadow: 0 0 40px rgba(255,153,51,0.15);
            animation: iconFloat 3s ease-in-out infinite;
        }
        @keyframes iconFloat {
            0%, 100% { transform: translateY(0) scale(1); }
            50% { transform: translateY(-5px) scale(1.05); }
        }
        .header h1 {
            font-family: 'Orbitron', 'Segoe UI', sans-serif;
            font-size: 24px;
            font-weight: 900;
            color: #fff;
            letter-spacing: 3px;
        }
        .header h1 .highlight { color: #FF9933; }
        .header .subtitle {
            font-size: 12px;
            color: rgba(255,255,255,0.2);
            font-weight: 400;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-top: 4px;
        }
        .header .subtitle i { color: #00ff66; margin-right: 6px; }
        
        .credit-line {
            text-align: center;
            font-size: 10px;
            color: rgba(255,255,255,0.06);
            margin-bottom: 20px;
            letter-spacing: 1px;
        }
        .credit-line span { color: #FF9933; font-weight: 600; }
        
        .upload-area {
            border: 2px dashed rgba(255,153,51,0.15);
            border-radius: 16px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        .upload-area:hover {
            border-color: #FF9933;
            background: rgba(255,153,51,0.03);
        }
        .upload-area.dragover {
            border-color: #00ff66;
            background: rgba(0,255,102,0.03);
        }
        .upload-area .icon {
            font-size: 50px;
            color: #FF9933;
            display: block;
            margin-bottom: 10px;
        }
        .upload-area .text {
            font-size: 16px;
            font-weight: 600;
            color: rgba(255,255,255,0.5);
        }
        .upload-area .text span { color: #FF9933; }
        .upload-area .sub-text {
            font-size: 12px;
            color: rgba(255,255,255,0.15);
            margin-top: 6px;
        }
        .upload-area input[type="file"] { display: none; }
        
        .progress-box {
            display: none;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 20px;
        }
        .progress-box.show { display: block; }
        .progress-box .file-name {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .progress-box .file-name i { color: #FF9933; margin-right: 8px; }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-bar .fill {
            height: 100%;
            background: linear-gradient(90deg, #FF9933, #00ff66);
            border-radius: 4px;
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-box .status {
            font-size: 11px;
            color: rgba(255,255,255,0.2);
            margin-top: 6px;
            display: flex;
            justify-content: space-between;
        }
        .progress-box .status .percent { color: #00ff66; font-weight: 600; }
        
        .result-box {
            display: none;
            background: rgba(0,255,102,0.03);
            border: 1px solid rgba(0,255,102,0.06);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 20px;
            animation: fadeIn 0.5s ease;
        }
        .result-box.show { display: block; }
        .result-box .success-icon {
            font-size: 30px;
            color: #00ff66;
            display: block;
            text-align: center;
            margin-bottom: 6px;
        }
        .result-box .title {
            text-align: center;
            font-size: 16px;
            font-weight: 700;
            color: #00ff66;
        }
        .result-box .link-box {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 10px 14px;
            margin: 10px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .result-box .link-box input {
            flex: 1;
            background: transparent;
            border: none;
            color: #00ff66;
            font-size: 12px;
            font-family: 'Courier New', monospace;
            outline: none;
            word-break: break-all;
        }
        .result-box .link-box .btn-copy {
            background: rgba(46, 204, 113, 0.12);
            border: 1px solid rgba(46, 204, 113, 0.08);
            color: #2ecc71;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 12px;
            transition: 0.3s;
            white-space: nowrap;
        }
        .result-box .link-box .btn-copy:hover { background: rgba(46, 204, 113, 0.2); }
        .result-box .info {
            font-size: 10px;
            color: rgba(255,255,255,0.15);
            text-align: center;
            margin-top: 6px;
        }
        .result-box .info span { color: #FF9933; }
        
        .recent-box {
            margin-top: 20px;
        }
        .recent-box .title {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
            color: rgba(255,255,255,0.3);
        }
        .recent-box .title i { color: #FF9933; margin-right: 8px; }
        .recent-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            background: rgba(255,255,255,0.02);
            border-radius: 8px;
            margin-bottom: 6px;
            border: 1px solid rgba(255,255,255,0.02);
            transition: all 0.3s ease;
        }
        .recent-item:hover {
            border-color: rgba(255,153,51,0.05);
        }
        .recent-item .info {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .recent-item .info .name {
            font-size: 13px;
            font-weight: 600;
            color: #fff;
        }
        .recent-item .info .detail {
            font-size: 10px;
            color: rgba(255,255,255,0.15);
        }
        .recent-item .info .detail i { margin-right: 4px; }
        .recent-item .actions {
            display: flex;
            gap: 6px;
        }
        .recent-item .actions .btn-sm {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
            border: 1px solid rgba(255,255,255,0.04);
            background: rgba(255,255,255,0.02);
            color: rgba(255,255,255,0.3);
            text-decoration: none;
        }
        .recent-item .actions .btn-sm:hover {
            background: rgba(255,153,51,0.05);
            border-color: rgba(255,153,51,0.05);
            color: #FF9933;
        }
        
        .empty-state {
            text-align: center;
            padding: 30px 20px;
            color: rgba(255,255,255,0.05);
        }
        .empty-state i {
            font-size: 30px;
            display: block;
            margin-bottom: 8px;
        }
        .empty-state p {
            font-size: 12px;
        }
        
        .error-msg {
            color: #ff4444;
            font-size: 12px;
            text-align: center;
            margin-top: 8px;
            display: none;
        }
        .error-msg.show { display: block; }
        
        .footer {
            text-align: center;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.02);
        }
        .footer .credit {
            font-size: 9px;
            color: rgba(255,255,255,0.04);
            letter-spacing: 2px;
        }
        .footer .credit span { color: #FF9933; font-weight: 600; }
        
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 480px) {
            .glow-card { padding: 18px 14px; }
            .header h1 { font-size: 18px; }
            .result-box .link-box { flex-wrap: wrap; }
            .result-box .link-box input { font-size: 10px; }
            .upload-area { padding: 25px 15px; }
            .upload-area .icon { font-size: 35px; }
            .recent-item { flex-direction: column; align-items: flex-start; gap: 8px; }
            .recent-item .actions { width: 100%; justify-content: flex-end; }
        }
    </style>
</head>
<body>

<div class="container">
    <div class="glow-card">
        
        <div class="header">
            <span class="logo"><i class="fas fa-cloud-upload-alt"></i></span>
            <h1><span class="highlight">EXPLOITS</span> Upload</h1>
            <div class="subtitle"><i class="fas fa-file"></i> Share Any File</div>
        </div>
        
        <div class="credit-line">👑 Developed by <span>@SATVIR_EXPLOITS</span> | 📢 <span>@freehackingg</span></div>
        
        <!-- UPLOAD AREA -->
        <div class="upload-area" id="uploadArea">
            <span class="icon"><i class="fas fa-file-upload"></i></span>
            <div class="text">Click or drag file <span>here</span></div>
            <div class="sub-text">Max 5 GB · All files allowed</div>
            <input type="file" id="fileInput">
        </div>
        
        <!-- PROGRESS -->
        <div class="progress-box" id="progressBox">
            <div class="file-name"><i class="fas fa-file"></i> <span id="fileName">file.mp4</span></div>
            <div class="progress-bar">
                <div class="fill" id="progressFill"></div>
            </div>
            <div class="status">
                <span id="progressStatus">Uploading...</span>
                <span class="percent" id="progressPercent">0%</span>
            </div>
        </div>
        
        <!-- RESULT -->
        <div class="result-box" id="resultBox">
            <span class="success-icon"><i class="fas fa-check-circle"></i></span>
            <div class="title">Upload Complete!</div>
            <div class="link-box">
                <input type="text" id="downloadLink" readonly>
                <button class="btn-copy" onclick="copyLink()">📋 Copy</button>
            </div>
            <div class="info">🔗 Link will auto-download · Valid for 7 days · <span id="fileSize">0 MB</span></div>
        </div>
        
        <!-- ERROR -->
        <div class="error-msg" id="errorMsg"></div>
        
        <!-- RECENT UPLOADS -->
        <div class="recent-box">
            <div class="title"><i class="fas fa-history"></i> Recent Uploads</div>
            <div id="recentList">
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No files uploaded yet</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <div class="credit">⚡ Powered by <span>EXPLOITS</span> · Max 5 GB</div>
        </div>
        
    </div>
</div>

<script>
    // ============================================
    // UPLOAD
    // ============================================
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const progressBox = document.getElementById('progressBox');
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    const fileName = document.getElementById('fileName');
    const resultBox = document.getElementById('resultBox');
    const downloadLink = document.getElementById('downloadLink');
    const fileSize = document.getElementById('fileSize');
    const errorMsg = document.getElementById('errorMsg');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            uploadFile();
        }
    });
    
    fileInput.addEventListener('change', uploadFile);
    
    async function uploadFile() {
        const file = fileInput.files[0];
        if (!file) return;
        
        // Check size (5GB)
        if (file.size > 5 * 1024 * 1024 * 1024) {
            showError('File too large! Max 5 GB.');
            return;
        }
        
        // Show progress
        progressBox.classList.add('show');
        resultBox.classList.remove('show');
        errorMsg.classList.remove('show');
        fileName.textContent = file.name;
        progressFill.style.width = '0%';
        progressPercent.textContent = '0%';
        progressStatus.textContent = 'Uploading...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = percent + '%';
                    progressPercent.textContent = percent + '%';
                }
            });
            
            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        if (data.success) {
                            progressStatus.textContent = '✅ Complete!';
                            progressFill.style.width = '100%';
                            progressPercent.textContent = '100%';
                            
                            setTimeout(() => {
                                downloadLink.value = data.download_url;
                                fileSize.textContent = formatSize(file.size);
                                resultBox.classList.add('show');
                                loadRecent();
                            }, 500);
                        } else {
                            showError(data.error || 'Upload failed!');
                        }
                    } catch (e) {
                        showError('Error parsing response');
                    }
                } else {
                    showError('Upload failed! Status: ' + xhr.status);
                }
            };
            
            xhr.onerror = function() {
                showError('Network error! Please try again.');
            };
            
            xhr.open('POST', '/upload', true);
            xhr.send(formData);
            
        } catch (e) {
            showError('Error: ' + e.message);
        }
    }
    
    function copyLink() {
        const link = document.getElementById('downloadLink');
        link.select();
        navigator.clipboard.writeText(link.value).then(() => {
            alert('✅ Link copied!');
        }).catch(() => {
            document.execCommand('copy');
            alert('✅ Link copied!');
        });
    }
    
    function showError(msg) {
        errorMsg.textContent = '⚠️ ' + msg;
        errorMsg.classList.add('show');
        progressBox.classList.remove('show');
        resultBox.classList.remove('show');
    }
    
    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
        return (bytes / 1073741824).toFixed(1) + ' GB';
    }
    
    // ============================================
    // LOAD RECENT
    // ============================================
    async function loadRecent() {
        try {
            const res = await fetch('/api/recent');
            const data = await res.json();
            const list = document.getElementById('recentList');
            
            if (!data.files || data.files.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No files uploaded yet</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            data.files.forEach(f => {
                const size = formatSize(f.size);
                const date = new Date(f.timestamp).toLocaleString();
                html += `
                    <div class="recent-item">
                        <div class="info">
                            <div class="name">${f.original_name}</div>
                            <div class="detail"><i class="fas fa-database"></i> ${size} · <i class="fas fa-clock"></i> ${date}</div>
                        </div>
                        <div class="actions">
                            <a href="${f.download_url}" class="btn-sm" download>⬇️ Download</a>
                            <button class="btn-sm" onclick="copyRecentLink('${f.download_url}')">📋 Copy</button>
                        </div>
                    </div>
                `;
            });
            list.innerHTML = html;
        } catch (e) {
            console.error('Error loading recent:', e);
        }
    }
    
    function copyRecentLink(url) {
        navigator.clipboard.writeText(url).then(() => {
            alert('✅ Link copied!');
        }).catch(() => {
            const input = document.createElement('input');
            input.value = url;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            alert('✅ Link copied!');
        });
    }
    
    // ============================================
    // INIT
    // ============================================
    loadRecent();
</script>

</body>
</html>
"""

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Generate unique ID
        file_id = str(uuid.uuid4())[:8]
        original_name = file.filename
        
        # Save file
        safe_name = f"{file_id}_{original_name}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_name)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        
        # Save to database
        files = load_files()
        files[file_id] = {
            'id': file_id,
            'original_name': original_name,
            'safe_name': safe_name,
            'size': file_size,
            'timestamp': datetime.now().isoformat()
        }
        save_files(files)
        
        download_url = f"{BASE_URL}/download/{file_id}/{original_name}"
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'download_url': download_url,
            'original_name': original_name,
            'size': file_size
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<file_id>/<filename>')
def download_file(file_id, filename):
    files = load_files()
    
    if file_id not in files:
        return "File not found", 404
    
    file_info = files[file_id]
    file_path = os.path.join(UPLOAD_FOLDER, file_info['safe_name'])
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    return send_file(file_path, as_attachment=True, download_name=file_info['original_name'])

@app.route('/api/recent')
def get_recent():
    files = load_files()
    # Sort by timestamp (newest first)
    file_list = sorted(files.values(), key=lambda x: x.get('timestamp', ''), reverse=True)[:20]
    
    # Add download URL
    for f in file_list:
        f['download_url'] = f"{BASE_URL}/download/{f['id']}/{f['original_name']}"
    
    return jsonify({'files': file_list})

@app.route('/api/stats')
def get_stats():
    files = load_files()
    total_files = len(files)
    total_size = sum(f.get('size', 0) for f in files.values())
    
    return jsonify({
        'total_files': total_files,
        'total_size': total_size
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large! Max 5 GB'}), 413

if __name__ == '__main__':
    # Get port from environment for Vercel
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
