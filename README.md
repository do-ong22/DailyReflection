# 일일 업무 회고 리포트 생성 봇

산발적으로 흩어진 일일 업무 데이터(메일, 채팅, 일정, 문서)를 단일 컨텍스트로 결합하여 업무 누락을 방지하고 자동화된 업무 보고서를 생성하는 Discord Bot입니다.

<img width="680" height="887" alt="image" src="https://github.com/user-attachments/assets/8b41c149-5685-4090-bb05-a834e9ef897e" />


## 주요 기능

- **Google Calendar**: 오늘 + 내일 일정 수집
- **Gmail**: 오늘 수신/발신 이메일 수집
- **Google Chat**: 오늘 메시지 수집
- **Google Drive**: 오늘 수정된 문서 수집
- **NotebookLM (Gemini 2.5)**: AI 기반 업무 분석 및 리포트 생성
- **Discord**: 최종 리포트 자동 전송

## 사전 준비 사항

### 1. Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. APIs & Services에서 다음 APIs 활성화:
   - Google Calendar API
   - Gmail API
   - Google Drive API
   - Google Chat API
3. Credentials에서 OAuth 2.0 Client ID 생성
   - Application type: Desktop app
   - `credentials.json` 파일 다운로드

### 2. Discord Bot 생성

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 Application 생성
2. Bot 메뉴에서 Bot 생성
3. Message Content Intent 활성화
4. OAuth2 URL Generator에서 scope 추가: `bot`
5. 생성된 URL로 Discord 서버에 Bot 초대

### 3. NotebookLM CLI 설치

```bash
pip install notebooklm
```

자세한 내용은 [NotebookLM CLI 문서](https://notebooklm.google/) 참조

## 설치 방법

1. 저장소 클론:
```bash
git clone <repository-url>
cd anti
```

2. 가상환경 생성:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
```bash
# .env 파일 생성
DISCORD_BOT_TOKEN=your_discord_bot_token
NOTEBOOK_URL=your_notebooklm_url
```

5. Google OAuth 설정:
   - `credentials.json` 파일을 프로젝트 루트에 배치

## 사용 방법

1. Bot 실행:
```bash
python bot.py
```

2. Discord 채널에서 명령어 입력:

<img width="750" height="433" alt="image" src="https://github.com/user-attachments/assets/51eca60c-7701-4aaa-a526-48dde49084c4" />


| 명령어 | 설명 |
|--------|------|
| `/login` | Google OAuth 인증 시작 (최초 1회) |
| `/start` | 데이터 수집 및 리포트 생성 |
| `/report` | Drive에 저장된 최종 보고서 가져오기 |
| `/autostart` | 자동 실행 시간 설정/해제 |

### 자동 실행 (스케줄러)

Discord 명령어로 스케줄 설정:

| 명령어 | 설명 |
|--------|------|
| `/autostart 18:00` | 매일 18:00에 자동 실행 설정 |
| `/autostart on` | 자동 실행 활성화 |
| `/autostart off` | 자동 실행 비활성화 |
| `/autostart` | 현재 설정 확인 |

## 파일 구조

```
anti/
├── bot.py              # Discord Bot 메인 파일
├── collector.py        # Google API 데이터 수집
├── notebook_client.py  # NotebookLM API 연동
├── scheduler.py       # 자동 실행 스케줄러
├── requirements.txt   # Python 의존성
├── .env                # 환경 변수 (gitignore)
├── .gitignore          # Git 무시 파일
├── credentials.json    # Google OAuth (gitignore)
├── token.json          # Google 인증 토큰 (gitignore)
└── README.md           # 본 파일
```

## 환경 변수

| 변수 | 설명 | 필수 |
|------|------|------|
| DISCORD_BOT_TOKEN | Discord Bot Token | Yes |
| NOTEBOOK_URL | NotebookLM 노트북 URL | Yes |
| DISCORD_CHANNEL_ID | 자동 전송할 Discord 채널 ID | No (스케줄러 사용 시 필수) |
| SCHEDULE_TIME | 자동 실행 시간 (기본값: 18:00) | No |

## 결과물

- **Discord 메시지**: Markdown 형식의 업무 회고 리포트
- **로컬 파일**:
  - `daily_data.json`: 수집된 원본 데이터
  - `{날짜}_업무_통합_데이터.txt`: NotebookLM 분석용 텍스트

## 리포트 예시

```markdown
# 🏁 오늘의 업무 회고 리포트

## 1. 오늘 수행한 주요 업무
- **[문서 작업]** 도장로봇_참조모델_V1.docx 업데이트
- **[일정 소화]** AAS 모델링 주간 회의 (10:00)

## 2. ⚠️ 업무 누락 및 미결 사항
- **메일 피드백 누락**: 팀장님의 '계획서 보완 요청' 메일에 대한 후속 조치가 감지되지 않았습니다.

## 3. 내일의 주요 일정 및 준비물
- **09:00**: 팀 스탠드업 미팅

## 4. 한 줄 평
"오늘 계획서 작성 업무에 집중하셨습니다. 퇴근 전 피드백 확인을 추천합니다."
```

## 라이선스

MIT License
