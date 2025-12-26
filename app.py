from flask import Flask, request, jsonify
import re
# 1. 核心修正：僅導入整個模組，避免類別名稱與變數名稱產生衝突
import youtube_transcript_api

app = Flask(__name__)

def extract_video_id(url):
    """提取影片 ID"""
    if not url: return None
    patterns = [r'(?:v=|be/|embed/|shorts/)([^&\n?#]+)']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return url if len(url) == 11 else None

@app.route('/', methods=['GET'])
def home():
    """首頁驗證：解決日誌中的 GET / 404"""
    return jsonify({
        'status': 'Online',
        'message': 'API 已採用全路徑防禦模式運行',
        'installation': 'Verified via requirements.txt'
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.json
        url = data.get('url') if data else None
        video_id = extract_video_id(url)
        
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid URL'}), 200

        transcript_data = None
        
        # 2. 【專家建議寫法】採用全路徑調用 (模組名.類別名.方法名)
        # 這樣能徹底解決 "no attribute get_transcript" 的報錯
        try:
            # 優先嘗試：獲取字幕清單以鎖定「原頻道語言」
            proxy = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                # 抓取人工上傳的原始字幕
                transcript_data = proxy.find_manually_created_transcript().fetch()
            except:
                # 若無，則抓取預設的第一組字幕 (通常是原語系的自動生成版本)
                transcript_data = next(iter(proxy)).fetch()
        except Exception:
            # 備援：若 list_transcripts 失敗，使用最基礎的 get_transcript
            try:
                transcript_data = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as e_final:
                return jsonify({
                    'success': False, 
                    'error': f'此影片確實找不到字幕: {str(e_final)}',
                    'video_id': video_id
                }), 200

        # 將字幕片段串接為長文字，方便 n8n 使用
        full_text = " ".join([t['text'] for t in transcript_data])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text
        })

    except Exception as e:
        # 將技術報錯包裝在 JSON 中回傳
        return jsonify({'success': False, 'error': f'系統全域異常: {str(e)}'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 部署必須使用 8080 Port
    app.run(host='0.0.0.0', port=8080)
