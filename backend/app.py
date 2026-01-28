import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp

app = Flask(__name__)

# Allow requests from everywhere (Vercel, Localhost, etc.)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load the API Key safely
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

@app.route('/')
def home():
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
    
    if not video_id:
        return jsonify({'error': 'Missing video ID'}), 400
    
    if not YOUTUBE_API_KEY:
        print("CRITICAL ERROR: API Key is missing from Environment Variables.")
        return jsonify({'error': 'Server API Key not configured'}), 500

    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={YOUTUBE_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'error' in data:
            return jsonify({'error': data['error']['message']}), 400
            
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROUTE 2: TRANSCRIPTS (UPDATED) ---
@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({'error': 'Missing video ID'}), 400
    
    try:
        # Try to fetch transcript in English, Hindi, or Auto-generated English/Hindi
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=['en', 'en-US', 'hi', 'a.en', 'a.hi']
        )
        
        full_text = " ".join([i['text'] for i in transcript_list])
        return jsonify({
            'full_text': full_text,
            'timeline': transcript_list
        })
    except TranscriptsDisabled:
        return jsonify({'error': 'Subtitles are disabled for this video'}), 404
    except NoTranscriptFound:
        return jsonify({'error': 'No transcript found in English or Hindi'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROUTE 3: DOWNLOAD FORMATS (ANTI-BOT) ---
@app.route('/api/formats', methods=['GET'])
def get_formats():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'error': 'Missing video URL'}), 400

    try:
        # Configuration to bypass simple bot detection
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            # Pretend to be a real browser to avoid "Sign in" errors
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extract_flat': 'in_playlist', # Don't download entire playlists
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats = []
            # Extract only usable mp4 files with audio
            for f in info.get('formats', []):
                # We want files that have both video (vcodec!=none) and audio (acodec!=none) if possible,
                # OR high quality standalone video.
                if f.get('ext') == 'mp4':
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
        print(f"Download Error: {str(e)}")
        # Return a cleaner error message to the user
        if "Sign in" in str(e):
            return jsonify({'error': 'YouTube is blocking server downloads (Bot Protection). Try again later.'}), 403
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
