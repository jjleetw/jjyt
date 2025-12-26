from flask import Flask, request, jsonify
import re
# 核心修正：直接導入整個模組，避免名稱衝突
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

def extract_video_id(url):
    """提取 YouTube 影片 ID"""
    if not url: return None
    patterns = [r'(?:v=|be/|embed/|shorts/)([^&\n?#]+)']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return url if len(url) == 11 else None

@app.route('/', methods=['GET'])
def home():
    """首頁測試路由，確保不再出現 GET / 404"""
    return jsonify({
        'status': 'Online',
        'message': 'API 已採用防禦模式運行',
        'mode': 'Original Language'
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': '請提供 url 參數'}), 200
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': '無效的 YouTube 連結'}), 200

        transcript_list = None
        
        # --- 核心修正：採用全路徑調用，避開 "No attribute" 報錯 ---
        try:
            # 優先嘗試：獲取字幕清單以鎖定原頻道語言
            # 使用全路徑 youtube_transcript_api.YouTubeTranscriptApi
            transcript_list_obj = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                # 優先抓取手動上傳的原始字幕
                transcript_list = transcript_list_obj.find_manually_created_transcript().fetch()
            except:
                # 若無手動，抓取第一個可用的字幕 (原語系自動生成)
                transcript_list = next(iter(transcript_list_obj)).fetch()
                
        except Exception:
            # 備援：若 list_transcripts 仍失敗，退回最基礎的 get_transcript
            try:
                transcript_list = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as e_final:
                return jsonify({
                    'success': False, 
                    'error': f'此影片確實無字幕內容: {str(e_final)}',
                    'video_id': video_id
                }), 200

        # 將字幕片段串接為整段文字，方便 n8n 使用
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text
        })

    except Exception as e:
        # 將技術報錯轉換為 JSON
        return jsonify({'success': False, 'error': f'程式執行錯誤: {str(e)}'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 部署必須使用 8080 Port
    app.run(host='0.0.0.0', port=8080)
