import pytest
from unittest.mock import MagicMock
from fetch_playlists import get_all_playlists
from fetch_playlist_items import get_playlist_items
from sorter import get_uploads_playlist_id, add_video_to_playlist, get_user_playlists

@pytest.fixture
def mock_youtube():
    """YouTube API 클라이언트의 메서드 체이닝을 모킹하기 위한 픽스처"""
    mock = MagicMock()
    return mock

# --- Tests for fetch_playlists.py ---

def test_get_all_playlists_single_page(mock_youtube):
    mock_response = {
        'items': [
            {
                'id': 'PL_ID_1',
                'snippet': {'title': 'Playlist 1'},
                'contentDetails': {'itemCount': 5}
            }
        ]
    }
    mock_youtube.playlists.return_value.list.return_value.execute.return_value = mock_response
    
    playlists = get_all_playlists(mock_youtube, "UC_CHANNEL_ID")
    
    assert len(playlists) == 1
    assert playlists[0]['playlist_id'] == 'PL_ID_1'

# --- Tests for fetch_playlist_items.py ---

def test_get_playlist_items(mock_youtube):
    mock_response = {
        'items': [
            {
                'snippet': {
                    'title': 'Video 1',
                    'resourceId': {'videoId': 'VID_123'},
                    'position': 0
                }
            }
        ]
    }
    mock_youtube.playlistItems.return_value.list.return_value.execute.return_value = mock_response
    
    items = get_playlist_items(mock_youtube, "PL_ID", "My Playlist")
    
    assert len(items) == 1
    assert items[0]['video_id'] == 'VID_123'

# --- Tests for sorter.py (API related) ---

def test_get_uploads_playlist_id(mock_youtube):
    """채널 정보를 조회하여 업로드 재생목록 ID를 가져오는지 테스트"""
    mock_response = {
        'items': [{
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UU_UPLOADS_ID'
                }
            }
        }]
    }
    mock_youtube.channels.return_value.list.return_value.execute.return_value = mock_response
    
    uploads_id = get_uploads_playlist_id(mock_youtube, "UC_ID")
    
    assert uploads_id == 'UU_UPLOADS_ID'
    mock_youtube.channels.return_value.list.assert_called_once_with(
        part="contentDetails", id="UC_ID"
    )

def test_get_user_playlists(mock_youtube):
    """사용자의 재생목록을 {제목: ID} 맵으로 변환하는지 테스트"""
    mock_response = {
        'items': [
            {'id': 'ID1', 'snippet': {'title': 'Title1'}},
            {'id': 'ID2', 'snippet': {'title': 'Title2'}}
        ]
    }
    mock_youtube.playlists.return_value.list.return_value.execute.return_value = mock_response
    
    result = get_user_playlists(mock_youtube)
    
    assert result == {'Title1': 'ID1', 'Title2': 'ID2'}
    mock_youtube.playlists.return_value.list.assert_called_once()
    # mine=True 파라미터 확인
    args, kwargs = mock_youtube.playlists.return_value.list.call_args
    assert kwargs['mine'] is True

def test_add_video_to_playlist_success(mock_youtube):
    """비디오 추가 API가 성공적으로 호출되는지 테스트"""
    mock_youtube.playlistItems.return_value.insert.return_value.execute.return_value = {}
    
    success = add_video_to_playlist(mock_youtube, "VID_123", "PL_456")
    
    assert success is True
    mock_youtube.playlistItems.return_value.insert.assert_called_once()
    # body 구조 확인
    args, kwargs = mock_youtube.playlistItems.return_value.insert.call_args
    assert kwargs['body']['snippet']['playlistId'] == "PL_456"
    assert kwargs['body']['snippet']['resourceId']['videoId'] == "VID_123"

def test_add_video_to_playlist_failure(mock_youtube):
    """API 호출 중 에러 발생 시 False를 반환하는지 테스트"""
    mock_youtube.playlistItems.return_value.insert.return_value.execute.side_effect = Exception("API Error")
    
    success = add_video_to_playlist(mock_youtube, "VID_123", "PL_456")
    
    assert success is False