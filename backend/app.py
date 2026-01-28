import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
# Renaming import to prevent conflicts
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

# --- ROUTE 2: TRANSCRIPTS ---
@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Missing video ID'}), 400
    
    try:
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

# --- ROUTE 3: DOWNLOADS (iOS SPOOF - NO PROXY) ---
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
            # 👇 iOS Client Spoofing (Most reliable free method)
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web'],
                    'player_skip': ['webpage', 'configs', 'js'],
                }
            },
            # Emulate a real iPhone user agent
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = []
            
            for f in info.get('formats', []):
                # Get MP4s with both audio and video
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
            # This is the unavoidable "IP Ban" message
            return jsonify({'error': 'YouTube has temporarily blocked this server IP. Please try again in 3-6 hours.'}), 429
            
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
