import pytest
from unittest.mock import MagicMock
from googleapiclient.errors import HttpError
from sorter import get_uploads_playlist_id, add_video_to_playlist, get_user_playlists

@pytest.fixture
def mock_youtube():
    """YouTube API 클라이언트 모킹 픽스처"""
    return MagicMock()

def create_http_error(status, message, reason="error"):
    """Google API의 HttpError 객체를 시뮬레이션하기 위한 헬퍼 함수"""
    resp = MagicMock()
    resp.status = status
    resp.reason = reason
    # JSON 형식의 에러 메시지 생성
    content = bytes(f'{{"error": {{"message": "{message}", "errors": [{{"reason": "{reason}"}}]}}}}', 'utf-8')
    return HttpError(resp, content)

def test_get_uploads_playlist_id_channel_not_found(mock_youtube):
    """시나리오 1: 존재하지 않는 채널 ID 조회 시 ValueError 발생 여부"""
    # API는 성공했지만 결과가 비어있는 경우 (items가 빈 리스트)
    mock_youtube.channels.return_value.list.return_value.execute.return_value = {'items': []}
    
    with pytest.raises(ValueError, match="Channel not found"):
        get_uploads_playlist_id(mock_youtube, "INVALID_CHANNEL_ID")

def test_get_user_playlists_quota_exceeded(mock_youtube):
    """시나리오 2: API 할당량 초과(403) 시 대응 확인"""
    error = create_http_error(403, "Quota Exceeded", "quotaExceeded")
    mock_youtube.playlists.return_value.list.return_value.execute.side_effect = error
    
    # sorter.py의 get_user_playlists는 내부에서 try-except로 로깅 후 {} 반환
    result = get_user_playlists(mock_youtube)
    
    assert result == {}

def test_add_video_to_playlist_auth_error(mock_youtube):
    """시나리오 3: 인증 오류(401) 발생 시 False 반환 여부"""
    error = create_http_error(401, "Invalid Credentials", "authError")
    mock_youtube.playlistItems.return_value.insert.return_value.execute.side_effect = error
    
    success = add_video_to_playlist(mock_youtube, "VID_123", "PL_456")
    
    assert success is False

def test_get_user_playlists_network_timeout(mock_youtube):
    """시나리오 4: 네트워크 타임아웃 등 일반적인 Exception 발생 시 대응"""
    mock_youtube.playlists.return_value.list.return_value.execute.side_effect = TimeoutError("Connection timed out")
    
    result = get_user_playlists(mock_youtube)
    
    assert result == {}

def test_get_all_playlists_malformed_data(mock_youtube):
    """시나리오 5: API 응답 형식이 예상과 다를 때 (items 키 누락)"""
    from fetch_playlists import get_all_playlists
    
    # items 키가 없는 응답
    mock_youtube.playlists.return_value.list.return_value.execute.return_value = {'kind': 'youtube#playlistListResponse'}
    
    # get_all_playlists 코드를 보면 response['items']를 직접 참조하므로 KeyError가 발생할 것임
    # 이 테스트를 통해 코드의 취약점을 발견할 수 있습니다.
    with pytest.raises(KeyError):
        get_all_playlists(mock_youtube, "UC_ID")
