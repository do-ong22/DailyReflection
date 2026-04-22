# Role: 일일 업무 회고 리포트 생성 에이전트
# Goal: 산발적으로 흩어진 일일 업무 데이터(메일, 채팅, 일정, 문서)를 단일 컨텍스트로 결합하여 업무 누락을 방지하고 자동화된 업무 보고서를 생성함.
# Trigger: Discord `/start` 명령어 실행

# 1. 개요 (Overview)
 목적: 산발적으로 흩어진 일일 업무 데이터(메일, 채팅, 일정, 문서)를 단일 컨텍스트로 결합하여 업무 누락을 방지하고 자동화된 업무 보고서를 생성함.

 대상 플랫폼: Google Workspace API (Gmail, Calendar, Chat, Drive)

 실행 환경: Discord Bot (Python) + NotebookLM CLI (Gemini 2.5)

# 2. 실행 방법 (How to Use)
Discord 채널에서 `/start` 명령어 입력

# 3. 처리 흐름 (Processing Flow)
1. **인증**: Google OAuth (token.json 생성) - 최초 1회
2. **데이터 수집**: collector.py → daily_data.json + {YYYY-MM-DD}_업무_통합_데이터.txt
3. **분석**: notebook_client.py → NotebookLM(Gemini 2.5) 분석 요청
4. **결과 전송**: Discord 채널에 리포트 메시지 발송

# 4. 확인 방법 (How to Verify)
- Discord 채널에 출력되는 Markdown 형식의 리포트 메시지
- 로컬 파일: daily_data.json (수집 데이터), {YYYY-MM-DD}_업무_통합_데이터.txt (분석용)

# 5. 데이터 파이프라인 (Data Pipeline)
 5.1 수집 대상 데이터 (Input Sources)
 - Google Calendar: 오늘 + 내일 일정 (제목, 시간, 설명)
 - Gmail: 오늘 수신/발신된 이메일 (제목, 발신자, 스니펫)
 - Google Chat: Gmail API의 is:chat 필터로 검색 (보낸이, 내용)
 - Google Drive: 오늘 수정된 문서 (파일명, 수정 시간)

 5.2 데이터 추출 결과물
 - daily_data.json: 수집된 전체 데이터 (JSON)
 - {YYYY-MM-DD}_업무_통합_데이터.txt: NotebookLM용 텍스트 소스 파일

```json
{
  "date": "2026-04-22",
  "events": [{"time": "10:00", "title": "AAS 모델링 주간 회의", "desc": "도장 로봇 서브모델 확정"}],
  "communications": {
    "emails": [{"from": "팀장님", "subject": "계획서 보완 요청", "snippet": "...기술 사양 보완 바랍니다."}],
    "chats": [{"sender": "김철수", "text": "내일 오전까지 레이저 용접기 사양서 전달할게요."}]
  },
  "artifacts": [{"file_name": "도장로봇_참조모델_V1.docx", "last_mod": "15:30"}]
}
```

# 6. 핵심 분석 로직 (Gemini Prompt Logic)
 6.1 맥락 연결 (Contextual Stitching)
 에이전트는 '이벤트'와 '커뮤니케이션' 간의 상관관계를 분석합니다.

 예: 10시 회의(Calendar)에서 논의된 '도장 로봇'이 오후 3시 문서 수정(Drive)으로 이어졌는지 확인.

 6.2 누락 과업 탐지 (Gap Detection)
 메일이나 채팅에서 발견된 의무 표현("~해주세요", "~까지 드릴게요", "확인 부탁")이 캘린더 등록이나 실제 문서 결과물로 이어지지 않은 경우 '누락 후보'로 분류합니다.

# 7. 결과물 형식 (Output Template)
 NotebookLM(Gemini 2.5)이 생성하는 Markdown 보고서 양식입니다.

 # 🏁 오늘의 업무 회고 리포트

 ## 1. 오늘 수행한 주요 업무
 - (팩트 위주로 정리)

 ## 2. ⚠️ 업무 누락 및 미결 사항 (Critical)
 - (메일/채팅 요청 사항 중 미결된 것 탐지)

 ## 3. 내일의 주요 일정 및 준비물
 - (내일 일정 및 오늘 작업 연계물)

 ## 4. AI 한 줄 평
 - (칭찬 또는 조언)

# 8. 단계별 개발 로드맵 (Roadmap)
 Step 1 (Connector): Google Apps Script 또는 Python을 이용하여 각 서비스의 오늘 치 데이터를 텍스트로 추출하는 스크립트 작성.

 Step 2 (Prompting): Gemini CLI에 전달할 '업무 요약 및 누락 탐지 전용' 시스템 프롬프트 고도화.

 Step 3 (Integration): 매일 특정 시간(예: 17:30)에 스크립트가 실행되어 Gemini 분석 결과를 슬랙(Slack)이나 메일로 전송하도록 설정.
