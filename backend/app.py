import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

app = Flask(__name__)

# CORS Setup: Allow all domains initially so your Vercel deploy works immediately.
# Once deployed, you can replace "*" with your specific custom domain.
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return jsonify({"status": "active", "message": "YouTube Backend is Running"})

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
        # YouTube often blocks generic IP requests for transcripts
        return jsonify({'error': 'Transcript disabled or not available'}), 404

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
