from flask import Flask, request, jsonify
import re
import traceback
# 修改導入方式，避免名稱衝突
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
            # 使用正確的類別方法獲取字幕清單
            transcript_metadata = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 優先嘗試抓取「非自動生成」的原始字幕 (Manual)
            try:
                transcript_list = transcript_metadata.find_manually_created_transcript().fetch()
            except:
                # 如果沒有手動字幕，則抓取該影片預設的第一個字幕 (包含自動生成)
                # 這會反映原頻道的預設語言設定
                transcript_list = next(iter(transcript_metadata)).fetch()

        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'字幕庫讀取失敗: {str(e)}',
                'video_id': video_id
            }), 404
        
        # 串接為純文字供 n8n 直接寫入 Google Docs
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text,
            'length': len(full_text)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'系統錯誤: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 部署建議使用 8080 端口
    app.run(host='0.0.0.0', port=8080, debug=False)
