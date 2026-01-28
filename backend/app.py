import os
import requests  # <--- Import this
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 1. Get the Key securely from Render Environment
YOUTUBE_API_KEY = os.environ.get('AIzaSyCKnAjWXt4yq-D7YOtBaHZzGTPVLyaZNow')

@app.route('/')
def home():
    return jsonify({"status": "active"})

# --- NEW SECURE ROUTE ---
@app.route('/api/basic-info', methods=['GET'])
def get_video_info():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({'error': 'Missing video ID'}), 400
    
    if not YOUTUBE_API_KEY:
        return jsonify({'error': 'Server API Key not configured'}), 500

    # The Server talks to Google (User never sees the Key)
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={YOUTUBE_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ------------------------

# ... Keep your existing /api/transcript and /api/formats routes below ...
# (Existing code...)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
