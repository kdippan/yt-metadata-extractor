import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

app = Flask(__name__)

# Allow requests from everywhere (Vercel, Localhost, etc.)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ CORRECTED LINE: This looks for the variable named "YOUTUBE_API_KEY" in Render
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

@app.route('/')
def home():
    # Helper to check if server is running and key is loaded
    key_status = "Loaded" if YOUTUBE_API_KEY else "Missing"
    return jsonify({
        "status": "active", 
        "message": "YouTube Backend is Running",
        "key_status": key_status
    })

# --- ROUTE 1: BASIC INFO (SECURE) ---
@app.route('/api/basic-info', methods=['GET'])
def get_video_info():
    video_id = request.args.get('id')
    
    # Validation
    if not video_id:
        return jsonify({'error': 'Missing video ID'}), 400
    
    if not YOUTUBE_API_KEY:
        print("CRITICAL ERROR: API Key is missing from Environment Variables.")
        return jsonify({'error': 'Server API Key not configured'}), 500

    # The Server talks to Google (Securely using the key)
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={YOUTUBE_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Check if Google returned an error (like Quota Exceeded)
        if 'error' in data:
            return jsonify({'error': data['error']['message']}), 400
            
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROUTE 2: TRANSCRIPTS ---
@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({'error': 'Missing video ID'}), 400
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        # Combine text for easy copying
        full_text = " ".join([i['text'] for i in transcript_list])
        return jsonify({
            'full_text': full_text,
            'timeline': transcript_list
        })
    except Exception as e:
        return jsonify({'error': 'Transcript disabled or not available'}), 404

# --- ROUTE 3: DOWNLOAD FORMATS ---
@app.route('/api/formats', methods=['GET'])
def get_formats():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'error': 'Missing video URL'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats = []
            # Extract only mp4 files with audio
            for f in info.get('formats', []):
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none':
                    formats.append({
                        'resolution': f.get('format_note', 'N/A'),
                        'filesize': f.get('filesize_approx', 0),
                        'url': f.get('url'),
                        'ext': f.get('ext')
                    })
            
            return jsonify({
                'formats': formats,
                'title': info.get('title')
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
