import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
# 👇 Renaming import to avoid conflicts
from youtube_transcript_api import YouTubeTranscriptApi as YTApi
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

@app.route('/')
def home():
    return jsonify({
        "status": "active", 
        "message": "YouTube Backend is Running",
        "key_check": "Found" if YOUTUBE_API_KEY else "Missing"
    })

# --- ROUTE 1: BASIC INFO ---
@app.route('/api/basic-info', methods=['GET'])
def get_video_info():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Missing video ID'}), 400
    if not YOUTUBE_API_KEY: return jsonify({'error': 'Server API Key not configured'}), 500

    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROUTE 2: TRANSCRIPTS (FIXED) ---
@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Missing video ID'}), 400
    
    try:
        # 👇 Using the renamed import 'YTApi'
        transcript_list = YTApi.get_transcript(
            video_id, 
            languages=['en', 'en-US', 'hi', 'a.en', 'a.hi']
        )
        full_text = " ".join([i['text'] for i in transcript_list])
        return jsonify({'full_text': full_text})
        
    except TranscriptsDisabled:
        return jsonify({'error': 'Subtitles are disabled for this video.'}), 404
    except NoTranscriptFound:
        return jsonify({'error': 'No transcript found in English or Hindi.'}), 404
    except Exception as e:
        return jsonify({'error': f"Transcript Error: {str(e)}"}), 500

# --- ROUTE 3: DOWNLOADS (ANDROID SPOOFING) ---
@app.route('/api/formats', methods=['GET'])
def get_formats():
    video_url = request.args.get('url')
    if not video_url: return jsonify({'error': 'Missing video URL'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'geo_bypass': True,
            # 👇 CRITICAL FIX: Pretend to be an Android App to bypass "Sign In"
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = []
            
            for f in info.get('formats', []):
                # Filter for MP4s with audio
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none':
                    formats.append({
                        'resolution': f.get('format_note', 'N/A'),
                        'filesize': f.get('filesize_approx', 0),
                        'url': f.get('url'),
                        'ext': f.get('ext')
                    })
            
            return jsonify({'formats': formats, 'title': info.get('title')})
            
    except Exception as e:
        error_msg = str(e)
        print(f"DL Error: {error_msg}")
        
        if "Sign in" in error_msg:
            return jsonify({'error': 'YouTube Blocked Server (Try again in 1 hour)'}), 429
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
