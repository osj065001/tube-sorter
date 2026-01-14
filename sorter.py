import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# 설정 파일 경로
TOKEN_FILE = 'token.json'
RULES_FILE = 'rules.json'
STATE_FILE = 'state.json'

def get_youtube_client():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("token.json not found. Run authorize.py first.")
    
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_state(last_published_at):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_published_at': last_published_at}, f)

def get_uploads_playlist_id(youtube, channel_id):
    request = youtube.channels().list(part="contentDetails", id=channel_id)
    response = request.execute()
    return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

def add_video_to_playlist(youtube, video_id, playlist_id):
    try:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        request.execute()
        return True
    except Exception as e:
        print(f"Error adding video {video_id} to playlist {playlist_id}: {e}")
        return False

def get_user_playlists(youtube):
    """현재 로그인한 사용자의 모든 재생목록을 가져와 {제목: ID} 맵을 반환합니다."""
    playlists = {}
    next_page_token = None
    while True:
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        for item in response.get('items', []):
            playlists[item['snippet']['title']] = item['id']
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return playlists

def find_playlist_id_by_keyword(keyword, user_playlists):
    """사용자의 재생목록 중 키워드가 포함된 가장 적절한 재생목록 ID를 찾습니다."""
    for title, pl_id in user_playlists.items():
        if keyword in title:
            return pl_id
    return None

def main():
    youtube = get_youtube_client()
    rules_data = load_json(RULES_FILE)
    state = load_json(STATE_FILE) or {'last_published_at': '1970-01-01T00:00:00Z'}
    
    last_ts = state['last_published_at']
    channel_id = os.getenv("TARGET_CHANNEL_ID")
    
    if not channel_id:
        print("Error: TARGET_CHANNEL_ID not found in .env")
        return

    # 0. 현재 계정의 재생목록 정보 동적 로드
    print("Fetching your playlists to match keywords...")
    user_playlists = get_user_playlists(youtube)

    # 1. 업로드된 동영상 목록 가져오기
    uploads_id = get_uploads_playlist_id(youtube, channel_id)
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_id,
        maxResults=20
    )
    response = request.execute()
    
    new_videos = []
    for item in response.get('items', []):
        published_at = item['snippet']['publishedAt']
        if published_at > last_ts:
            new_videos.append({
                'id': item['contentDetails']['videoId'],
                'title': item['snippet']['title'],
                'published_at': published_at
            })

    if not new_videos:
        print("No new videos found.")
        return

    # 2. 분류 및 등록 (과거 순부터 처리하기 위해 정렬)
    new_videos.sort(key=lambda x: x['published_at'])
    
    latest_published_at = last_ts
    
    for video in new_videos:
        print(f"Processing: {video['title']}")
        matched = False
        for rule in rules_data['rules']:
            if rule['keyword'] in video['title']:
                print(f" -> Matching rule '{rule['keyword']}' found. Looking for playlist...")
                
                # 동적으로 재생목록 ID 찾기
                dynamic_playlist_id = find_playlist_id_by_keyword(rule['keyword'], user_playlists)
                
                if dynamic_playlist_id:
                    print(f" -> Found playlist ID: {dynamic_playlist_id}. Adding video...")
                    if add_video_to_playlist(youtube, video['id'], dynamic_playlist_id):
                        print(f" -> Successfully added!")
                        matched = True
                        break
                else:
                    print(f" -> Warning: No playlist found on your account containing keyword '{rule['keyword']}'")
        
        if not matched:
            print(f" -> No matching rules or playlist found for this video.")
        
        latest_published_at = video['published_at']

    # 3. 상태 저장
    save_state(latest_published_at)
    print(f"\nUpdate complete. Last processed timestamp: {latest_published_at}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
