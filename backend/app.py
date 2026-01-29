import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
# ✅ FIX: Standard import to prevent "AttributeError"
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

@app.route('/')
def home():
    return jsonify({"status": "active", "version": "Pro 2.0"})

# --- ROUTE 1: ADVANCED METADATA (Stable API) ---
@app.route('/api/basic-info', methods=['GET'])
def get_video_info():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Missing video ID'}), 400
    if not YOUTUBE_API_KEY: return jsonify({'error': 'Server API Key not configured'}), 500

    # Requesting ALL metadata parts
    parts = "snippet,statistics,contentDetails,status,recordingDetails,liveStreamingDetails,topicDetails"
    url = f"https://www.googleapis.com/youtube/v3/videos?part={parts}&id={video_id}&key={YOUTUBE_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            return jsonify({'error': 'Video not found'}), 404

        item = data['items'][0]
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        content = item.get('contentDetails', {})
        status = item.get('status', {})
        recording = item.get('recordingDetails', {})
        
        # Structure the Pro Data
        pro_data = {
            "id": item.get('id'),
            "basic": {
                "title": snippet.get('title'),
                "description": snippet.get('description'),
                "thumbnails": snippet.get('thumbnails'),
                "channelTitle": snippet.get('channelTitle'),
                "channelId": snippet.get('channelId'),
                "publishedAt": snippet.get('publishedAt'),
                "tags": snippet.get('tags', [])
            },
            "metrics": {
                "viewCount": statistics.get('viewCount', 0),
                "likeCount": statistics.get('likeCount', 0),
                "commentCount": statistics.get('commentCount', 0),
            },
            "technical": {
                "duration": content.get('duration'), # ISO 8601
                "definition": content.get('definition', 'sd').upper(), # HD/SD
                "dimension": content.get('dimension', '2d').upper(),   # 2D/3D
                "projection": content.get('projection'),
                "caption": content.get('caption') == 'true',
                "licensedContent": content.get('licensedContent', False)
            },
            "status": {
                "privacyStatus": status.get('privacyStatus'),
                "license": status.get('license'), # youtube/creativeCommon
                "embeddable": status.get('embeddable'),
                "madeForKids": status.get('madeForKids')
            },
            "location": recording.get('location', None), # GPS coords
            "live": item.get('liveStreamingDetails', None)
        }
        
        return jsonify(pro_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROUTE 2: TRANSCRIPT (Fixed Import) ---
@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Missing ID'}), 400
    
    try:
        # ✅ FIX: Using the class directly
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=['en', 'en-US', 'hi', 'a.en', 'a.hi']
        )
        full_text = " ".join([i['text'] for i in transcript_list])
        return jsonify({'full_text': full_text, 'timeline': transcript_list})
    except TranscriptsDisabled:
        return jsonify({'error': 'Captions are disabled by the creator.'}), 404
    except NoTranscriptFound:
        return jsonify({'error': 'No suitable language found.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROUTE 3: DOWNLOADS (Resistant Mode) ---
@app.route('/api/formats', methods=['GET'])
def get_formats():
    video_url = request.args.get('url')
    if not video_url: return jsonify({'error': 'Missing URL'}), 400

    try:
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'skip_download': True,
            'geo_bypass': True,
            # Trying "Android Creator" client (often more stable)
            'extractor_args': {'youtube': {'player_client': ['android_creator', 'web']}},
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = []
            for f in info.get('formats', []):
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none':
                    formats.append({
                        'res': f.get('format_note', 'N/A'),
                        'size': f.get('filesize_approx', 0),
                        'url': f.get('url'),
                        'ext': f.get('ext')
                    })
            return jsonify({'formats': formats})
            
    except Exception as e:
        # Don't crash the whole app if downloads fail
        if "Sign in" in str(e):
            return jsonify({'error': 'Server Cooldown'}), 429
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
