from flask import Flask, request, jsonify, send_file, render_template_string
import os
import uuid
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==================================================
# 🔧 CONFIG
# ==================================================
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB
file_db = {}

# ==================================================
# 📄 HTML + CSS (Embedded)
# ==================================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📤 File to Link</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { max-width: 600px; width: 100%; }
        .card { background: #161b22; padding: 32px; border-radius: 16px; border: 1px solid #30363d; }
        .card h1 { font-size: 28px; margin-bottom: 4px; color: #f0f6fc; }
        .card p { color: #8b949e; margin-bottom: 20px; }
        .drop-zone { border: 2px dashed #30363d; border-radius: 12px; padding: 40px 20px; text-align: center; cursor: pointer; transition: 0.3s; background: #0d1117; }
        .drop-zone:hover { border-color: #58a6ff; background: #161b22; }
        .drop-zone.dragover { border-color: #238636; background: #1c2a1c; }
        .drop-zone input { display: none; }
        .drop-zone .icon { font-size: 48px; }
        .drop-zone .text { color: #8b949e; font-size: 16px; }
        .drop-zone .text strong { color: #f0f6fc; }
        .progress-container { margin-top: 16px; display: none; }
        .progress-container .progress-bar { width: 100%; height: 8px; background: #30363d; border-radius: 8px; overflow: hidden; }
        .progress-container .progress-bar .fill { height: 100%; width: 0%; background: linear-gradient(90deg, #238636, #3fb950); transition: width 0.1s linear; border-radius: 8px; }
        .progress-container .progress-text { display: flex; justify-content: space-between; margin-top: 6px; font-size: 14px; color: #8b949e; }
        .progress-container .progress-text .percent { color: #f0f6fc; font-weight: 600; }
        .result-box { background: #0d1117; padding: 16px; border-radius: 8px; border: 1px solid #30363d; margin-top: 16px; display: none; }
        .result-box .url { color: #58a6ff; word-break: break-all; font-family: monospace; font-size: 14px; }
        .result-box .label { color: #8b949e; font-size: 13px; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; font-weight: 600; cursor: pointer; background: #1f6feb; color: white; margin-top: 8px; }
        .btn:hover { background: #388bfd; }
        .footer { margin-top: 20px; font-size: 13px; color: #8b949e; text-align: center; }
        .credit { color: #f0883e; font-weight: 600; }
        .file-list { margin-top: 16px; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #0d1117; border-radius: 6px; border: 1px solid #30363d; margin-top: 6px; }
        .file-item .fname { color: #f0f6fc; font-weight: 500; font-size: 13px; }
        .file-item .flink { color: #58a6ff; font-size: 12px; text-decoration: none; }
        .file-item .flink:hover { text-decoration: underline; }
        .file-item .fsize { color: #8b949e; font-size: 11px; }
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #238636; color: white; padding: 12px 24px; border-radius: 8px; display: none; z-index: 999; }
        .toast.error { background: #da3633; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .result-box { animation: fadeIn 0.4s ease; }
        @media (max-width: 600px) { .card { padding: 20px; } }
    </style>
</head>
<body>

<div class="container">
    <div class="card">
        <h1>📤 File to Link</h1>
        <p>Upload any file → Get instant download link</p>

        <div class="drop-zone" id="dropZone">
            <div class="icon">📂</div>
            <div class="text">
                <strong>Click to upload</strong> or drag & drop<br>
                <span style="font-size:13px;color:#8b949e;">Max file size: 5 GB</span>
            </div>
            <input type="file" id="fileInput" />
        </div>

        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="fill" id="progressFill"></div>
            </div>
            <div class="progress-text">
                <span id="progressLabel">Uploading...</span>
                <span class="percent" id="progressPercent">0%</span>
            </div>
        </div>

        <div class="result-box" id="resultBox">
            <div class="label">✅ Upload complete! Share this link:</div>
            <div class="url" id="resultUrl">https://your-domain.com/api/download/abc123</div>
            <button class="btn" onclick="copyUrl()">📋 Copy Link</button>
        </div>

        <div class="file-list" id="fileList"></div>

        <div class="footer">
            <span class="credit">🔥 Developed by @SATVIR_EXPLOITS</span>
        </div>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
// =============================================
// 🔥 FRONTEND JS
// =============================================

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressLabel = document.getElementById('progressLabel');
const progressPercent = document.getElementById('progressPercent');
const resultBox = document.getElementById('resultBox');
const resultUrl = document.getElementById('resultUrl');
const fileList = document.getElementById('fileList');
const toast = document.getElementById('toast');

let selectedFile = null;

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFile(e.dataTransfer.files[0]);
    }
});
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    const maxSize = 5 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('❌ File too large. Max 5 GB.', 'error');
        return;
    }
    selectedFile = file;
    uploadFile(file);
}

async function uploadFile(file) {
    resultBox.style.display = 'none';
    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';
    progressLabel.textContent = `📤 Uploading ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = percent + '%';
                progressPercent.textContent = percent + '%';
                if (percent < 30) {
                    progressLabel.textContent = `📤 Uploading ${file.name}... (${percent}%)`;
                } else if (percent < 70) {
                    progressLabel.textContent = `📤 Uploading ${file.name}... (${percent}%) — almost there!`;
                } else {
                    progressLabel.textContent = `📤 Finalizing ${file.name}... (${percent}%)`;
                }
            }
        });

        xhr.onload = function() {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                if (data.success) {
                    resultUrl.textContent = data.download_url;
                    resultBox.style.display = 'block';
                    showToast('✅ File uploaded successfully!');
                    addFileToList(data.filename, data.download_url, data.size);
                } else {
                    showToast('❌ ' + data.error, 'error');
                }
            } else {
                showToast('❌ Upload failed. Try again.', 'error');
            }
            progressContainer.style.display = 'none';
        };

        xhr.onerror = function() {
            showToast('❌ Network error. Try again.', 'error');
            progressContainer.style.display = 'none';
        };

        xhr.send(formData);

    } catch (err) {
        showToast('❌ ' + err.message, 'error');
        progressContainer.style.display = 'none';
    }
}

function copyUrl() {
    const url = resultUrl.textContent;
    navigator.clipboard.writeText(url).then(() => {
        showToast('✅ Link copied!');
    }).catch(() => {
        const range = document.createRange();
        range.selectNode(resultUrl);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        document.execCommand('copy');
        showToast('✅ Link copied!');
    });
}

function addFileToList(name, url, size) {
    const div = document.createElement('div');
    div.className = 'file-item';
    const sizeMB = (size / (1024 * 1024)).toFixed(2);
    div.innerHTML = `
        <span class="fname">📄 ${name}</span>
        <span class="fsize">${sizeMB} MB</span>
        <a href="${url}" target="_blank" class="flink">🔗 Link</a>
    `;
    fileList.prepend(div);
}

function showToast(msg, type = '') {
    toast.textContent = msg;
    toast.className = 'toast' + (type === 'error' ? ' error' : '');
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

async function loadRecent() {
    try {
        const res = await fetch('/api/files');
        const data = await res.json();
        if (data.files) {
            data.files.forEach(f => {
                addFileToList(f.name, f.url, f.size);
            });
        }
    } catch(e) {}
}

document.addEventListener('DOMContentLoaded', loadRecent);
</script>
</body>
</html>
"""

# =============================================
# 🚀 FLASK ROUTES
# =============================================

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Max 5 GB'}), 400

    file_id = str(uuid.uuid4())[:8]
    original_name = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{original_name}")
    file.save(file_path)

    file_db[file_id] = {
        'name': original_name,
        'path': file_path,
        'size': size,
        'uploaded': datetime.datetime.now().isoformat()
    }

    download_url = f"{request.host_url}api/download/{file_id}"

    return jsonify({
        'success': True,
        'file_id': file_id,
        'filename': original_name,
        'size': size,
        'download_url': download_url,
        'message': 'File uploaded successfully!'
    })

@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    if file_id not in file_db:
        return jsonify({'error': 'File not found'}), 404

    file_info = file_db[file_id]
    file_path = file_info['path']

    if not os.path.exists(file_path):
        return jsonify({'error': 'File deleted'}), 404

    return send_file(file_path, as_attachment=True, download_name=file_info['name'])

@app.route('/api/files', methods=['GET'])
def list_files():
    files = []
    for fid, info in file_db.items():
        files.append({
            'id': fid,
            'name': info['name'],
            'size': info['size'],
            'url': f"{request.host_url}api/download/{fid}"
        })
    return jsonify({'files': files})

# =============================================
# 🚀 VERCEL EXPORT
# =============================================
# Vercel needs this exact export — 'app' object
# =============================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
