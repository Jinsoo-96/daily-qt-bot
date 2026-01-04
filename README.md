# 📖 청년부 오늘의 QT 디스코드 봇 (Daily QT Bot)

두란노 **'생명의 삶'**의 매일 말씀을 자동으로 스크랩하여 디스코드 **포럼(Forum) 채널**에 게시하고, 해당 포스트를 **상단 고정(Pin)**해 주는 자동화 봇입니다.

## ✨ 주요 기능
* **포럼 포스트 자동 생성**: 매일 아침 날짜를 제목으로 한 새로운 게시글을 생성합니다.
* **상단 고정 (Auto-Pin)**: 최신 말씀이 항상 포럼 상단에 위치하도록 자동으로 '핀'을 꽂습니다.
* **마크다운 최적화**: `#`, `###`, `> ` 등 디스코드 마크다운을 활용해 가독성 높은 디자인을 제공합니다.
* **서버리스 운영**: GitHub Actions를 통해 24시간 서버 가동 없이 매일 정해진 시간에 작동합니다.

## 🛠 기술 스택
* **언어**: Python 3.9+
* **라이브러리**: `discord.py`, `BeautifulSoup4`, `requests`
* **플랫폼**: GitHub Actions (Automation)

## 🚀 설정 방법 (Setup Guide)

### 1. 디스코드 봇 설정 (Developer Portal)
1. [Discord Developer Portal](https://discord.com/developers/applications)에서 애플리케이션 생성
2. **Bot** 메뉴에서 `Message Content Intent`를 반드시 **ON**으로 활성화
3. **OAuth2 -> URL Generator**에서 `bot` 스코프와 `Administrator` 권한을 선택하여 서버에 초대

### 2. GitHub Secrets 등록
저장소의 **Settings > Secrets and variables > Actions**에 아래 항목을 추가합니다.

| Name | Description |
| :--- | :--- |
| `DISCORD_BOT_TOKEN` | 디스코드 개발자 포털에서 발급받은 봇의 Token |
| `FORUM_CHANNEL_ID` | 게시글이 올라갈 포럼 채널의 숫자 ID (개발자 모드 활용) |

### 3. 자동 실행 스케줄
* **실행 시간**: 매일 한국 시간(KST) **오전 06:00**
* **수동 실행**: GitHub 저장소의 `Actions` 탭 -> `Daily QT Bot` 선택 -> `Run workflow` 클릭으로 즉시 실행 가능

## 📁 파일 구성
* `main.py`: 웹 스크래핑 및 디스코드 봇 구동 로직
* `.github/workflows/run_qt.yml`: GitHub Actions 자동화 스크립트
* `README.md`: 프로젝트 설명서

## ⚠️ 주의 사항
* 본 봇은 **두란노 생명의 삶** 웹사이트의 구조에 의존합니다. 사이트 레이아웃이 변경될 경우 스크래핑 코드 수정이 필요할 수 있습니다.
* 성경 본문의 저작권은 **대한성서공회**에, 콘텐츠 권한은 **두란노**에 있습니다.