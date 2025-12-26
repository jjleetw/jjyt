from flask import Flask, request, jsonify
import re
import traceback
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

def extract_video_id(url):
    """從 URL 提取 YouTube 影片 ID"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if url and len(url) == 11 and "/" not in url:
        return url
    return None

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'service': 'YouTube Transcript API (Original Language Mode)'
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'Missing URL'}), 400
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid ID or URL'}), 400
        
        transcript_list = None
        
        try:
            # 獲取該影片所有的字幕清單
            transcript_metadata = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 【核心修改】：優先抓取頻道主上傳的原始語言字幕 (Manual Transcript)
            try:
                # find_manually_created_transcript 會自動尋找非自動生成的原始字幕
                transcript_list = transcript_metadata.find_manually_created_transcript().fetch()
            except:
                # 如果沒有手動字幕，則抓取任何可用的字幕 (通常是自動生成)
                # 不指定語言，系統會回傳該影片預設的語言
                transcript_list = next(iter(transcript_metadata)).fetch()

        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'No transcript available: {str(e)}',
                'video_id': video_id
            }), 404
        
        # 串接為純文字供 n8n 直接使用
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text,
            'length': len(full_text)
        })

    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 部署建議使用 8080 端口
    app.run(host='0.0.0.0', port=8080, debug=False)
