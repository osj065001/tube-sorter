# YouTube 자동 분류 및 재생목록 등록 시스템 구축 로드맵

본 문서는 `tube-sorter` 프로젝트를 YouTube Data API v3와 GitHub Actions를 활용한 자동화 시스템으로 진화시키기 위한 단계별 가이드를 제공합니다.

---

## 🏗 전체 아키텍처 흐름
1. **신규 영상 감지:** 채널의 최신 업로드 확인 (증분 업데이트)
2. **필터링 로직:** 제목, 태그, 설명을 기반으로 카테고리 분류
3. **재생목록 등록:** 분류된 카테고리에 맞는 재생목록에 영상 추가
4. **자동화:** GitHub Actions를 통한 주기적(Cron) 실행

---

## 📅 단계별 추진 계획

### Phase 1: 인증 아키텍처 전환 (OAuth 2.0)
사용자의 재생목록을 수정하기 위해서는 단순 API Key가 아닌 사용자 권한이 포함된 OAuth 인증이 필요합니다.
- **Task:** Google Cloud Console에서 OAuth 2.0 클라이언트 ID 생성
- **Task:** 서버 없이 인증을 갱신하기 위한 `refresh_token` 발급 및 관리 로직 구현
- **Goal:** GitHub Actions 환경에서 브라우저 개입 없이 API 호출 권한 유지

### Phase 2: 필터링 및 분류 엔진 설계
영상을 어떤 기준으로 분류할지 결정하는 비즈니스 로직($\text{Business Logic}$)을 정교화합니다.
- **Task:** `rules.json` 설정을 통해 키워드 기반 매핑 테이블 작성
- **Mathematical Logic:** 
  $$F(v) = \begin{cases} P_{A} & \text{if } \text{keyword} \in v.title \\ P_{B} & \text{if } v.duration > 600 \\ \text{ignore} & \text{otherwise} \end{cases}
$$
- **Goal:** 유연하고 확장 가능한 분류 규칙 시스템 구축

### Phase 3: 증분 업데이트 ($ \text{Incremental Update}$) 구현
API 할당량($\text{Quota}$)을 효율적으로 관리하기 위해 변경사항만 처리합니다.
- **Task:** 마지막으로 처리한 `videoId` 또는 `publishedAt`을 상태(State)로 저장
- **Task:** 중복 처리를 방지하기 위한 체크 로직 구현
- **Goal:** 신규로 업로드된 영상만 선별적으로 처리하여 시스템 부하 최적화

### Phase 4: 재생목록 등록 기능 구현
실제 YouTube 재생목록에 영상을 삽입하는 기능을 완성합니다.
- **API:** `youtube.playlistItems().insert`
- **Task:** 재생목록 존재 여부 확인 및 자동 생성(선택 사항) 로직
- **Goal:** 필터링된 결과가 실제 YouTube 계정에 반영되도록 구현

### Phase 5: GitHub Actions 워크플로우 구축
모든 프로세스를 클라우드 환경에서 자동화합니다.
- **Task:** `.github/workflows/main.yml` 파일 작성 (Cron 설정)
- **Task:** `GitHub Secrets`를 통한 보안 자격 증명(OAuth Secrets) 관리
- **Task:** 실행 후 상태 변화(CSV 업데이트)를 다시 저장소에 커밋하는 자동화 로직
- **Goal:** 수동 개입 없는 완전 무인 자동화 시스템 완성

---

## 🛠 주요 기술 스택
- **Language:** Python 3.x
- **API:** YouTube Data API v3
- **Authentication:** OAuth 2.0 (Google Auth Library)
- **Automation:** GitHub Actions
- **Data:** Pandas (CSV-based State Management)

---
*문서 생성일: 2026-01-14*
