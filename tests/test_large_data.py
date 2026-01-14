import pytest
import time
from unittest.mock import MagicMock
from fetch_playlists import get_all_playlists
from sorter import classify_video, get_user_playlists

@pytest.fixture
def mock_youtube():
    return MagicMock()

def test_get_all_playlists_large_scale(mock_youtube):
    """시나리오 1: 1,000개의 재생목록(20페이지) 조회 테스트"""
    total_items = 1000
    page_size = 50
    num_pages = total_items // page_size
    
    responses = []
    for i in range(num_pages):
        next_token = f"token_{i+1}" if i < num_pages - 1 else None
        items = [
            {
                'id': f'PL_ID_{i*page_size + j}',
                'snippet': {'title': f'Playlist {i*page_size + j}'},
                'contentDetails': {'itemCount': 1}
            }
            for j in range(page_size)
        ]
        responses.append({
            'items': items,
            'nextPageToken': next_token
        })
    
    mock_youtube.playlists.return_value.list.return_value.execute.side_effect = responses
    
    start_time = time.time()
    playlists = get_all_playlists(mock_youtube, "UC_LARGE_CHANNEL")
    end_time = time.time()
    
    assert len(playlists) == total_items
    assert playlists[0]['playlist_id'] == 'PL_ID_0'
    assert playlists[-1]['playlist_id'] == 'PL_ID_999'
    print(f"\n[Performance] Fetched {total_items} playlists in {end_time - start_time:.4f}s")

def test_classify_video_performance_large_rules():
    """시나리오 2: 500개의 규칙과 500개의 재생목록 매칭 성능 테스트"""
    # 500개의 규칙 생성 (키워드: Keyword_0, Keyword_1, ...)
    rules_data = {
        "rules": [{"keyword": f"Keyword_{i}"} for i in range(500)]
    }
    # 500개의 사용자 재생목록 생성 (제목: Playlist Title Keyword_0, ...)
    user_playlists = {f"Playlist Title Keyword_{i}": f"PL_ID_{i}" for i in range(500)}
    
    # 마지막(499번째) 규칙에 매칭되는 영상 제목
    video_title = "This video matches Keyword_499 specifically"
    
    start_time = time.time()
    # 1,000번 반복 실행하여 평균 속도 측정
    iterations = 1000
    for _ in range(iterations):
        playlist_id, keyword = classify_video(video_title, rules_data, user_playlists)
    end_time = time.time()
    
    assert playlist_id == "PL_ID_499"
    assert keyword == "Keyword_499"
    avg_time = (end_time - start_time) / iterations
    print(f"[Performance] Avg classification time with 500 rules: {avg_time*1000:.4f}ms")

def test_get_user_playlists_high_volume(mock_youtube):
    """시나리오 3: 500개의 재생목록을 맵으로 변환하는 로직 테스트"""
    # 10페이지 분량의 응답 생성
    responses = []
    for i in range(10):
        next_token = f"token_{i+1}" if i < 9 else None
        items = [{'id': f'ID_{i*50+j}', 'snippet': {'title': f'Title_{i*50+j}'}} for j in range(50)]
        responses.append({'items': items, 'nextPageToken': next_token})
        
    mock_youtube.playlists.return_value.list.return_value.execute.side_effect = responses
    
    start_time = time.time()
    result = get_user_playlists(mock_youtube)
    end_time = time.time()
    
    assert len(result) == 500
    assert result['Title_499'] == 'ID_499'
    print(f"[Performance] Mapped 500 playlists in {end_time - start_time:.4f}s")