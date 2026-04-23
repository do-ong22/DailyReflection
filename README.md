# 📋 일일 업무 회고 리포트 봇

Google 데이터(calendar, gmail, chat, drive)를 자동으로 수집하여 NotebookLM으로 분석하고 Discord로 리포트를 받아볼 수 있습니다.

## 🚀 시작하기

### 1. Bot 초대하기 (Discord 서버에 Bot 추가)

#### Step 1-1: 초대 링크 열기
아래 링크를 브라우저 주소창에 붙여넣기하거나 클릭하세요:

```
https://discord.com/oauth2/authorize?client_id=1496386596650483762&permissions=397284711488&integration_type=0&scope=bot+applications.commands
```

<img width="1905" height="165" alt="image" src="https://github.com/user-attachments/assets/7fdabd44-8301-4c94-aaaa-1b9fd2830e47" />


#### Step 1-2: Discord에 로그인
- Discord 계정으로 로그인되어 있지 않으면 로그인하세요
- Discord 웹사이트나 앱에서 로그인 상태 확인

#### Step 1-3: Bot을 추가할 서버 선택
1. 링크를 열면 "Discord 애플리케이션 hinzufügen" (애플리케이션 추가) 페이지가 나옴
2. "서버 추가" 드롭다운 메뉴에서 Bot을 추가할 서버 선택
   - **주의**: 서버 관리자 권한이 있어야 합니다 (서버 설정 > 관리자 역할 필요)
3. 팝업되는 창에서 "새로운 서버 생성"이 아닌 기존 서버 선택

<img width="1893" height="847" alt="image" src="https://github.com/user-attachments/assets/913539e5-2ed5-42e6-a79d-e6601e1289aa" />


#### Step 1-4: 권한 확인
1. "이 애플리케이션이 다음에 액세스하도록 허용:" 메시지가 표시됨
2. Bot에 필요한 권한들이 자동으로 체크됨
3. "승인" 버튼 클릭

<img width="1893" height="845" alt="image" src="https://github.com/user-attachments/assets/b0307a7a-4ad1-43a0-873e-845c63d17441" />


#### Step 1-5: Bot 초대 완료
1. "_CAPCTION_Bot이 서버에 추가되었습니다" 메시지 확인
2. Discord 서버 채널 목록에 Bot이 나타남 (초록색 상태 표시)

<img width="611" height="398" alt="image" src="https://github.com/user-attachments/assets/596e51b4-f63d-4f30-85b7-1faa4734f8b4" />
<img width="1812" height="806" alt="image" src="https://github.com/user-attachments/assets/359836e3-0a35-4d2e-8bbd-147d32b19dc4" />


#### Step 1-6: Bot 명령어 확인
- Discord 서버의 `/로그인`, `/시작` 등 슬래시 명령어가 자동완성에 나타나는지 확인
- 나타나지 않으면 잠시 후 (1-2분) 다시 시도
<img width="1806" height="816" alt="image" src="https://github.com/user-attachments/assets/4bf74dfa-06de-4303-899d-4850c14b1041" />

---

### 2. 처음 설정 (처음 1회)

#### Step 2-1: /로그인 명령어 입력
1. Discord 채널에 `/로그인` 입력
2. Bot이 "Google 로그인 필요" 메시지 전송

#### Step 2-2: Google 로그인
1. Bot이 전송한 URL 클릭 (예: `https://accounts.google.com/...` 형태)
2. 브라우저에서 Google 계정으로 로그인
3. "허용" 버튼 클릭하여 권한 부여

#### Step 2-3: 노트북 생성 확인
1. Bot이 "설정 완료" 또는 "노트북 생성됨" 확인 메시지 전송
2. Google Drive에 노트북이 자동 생성된 것 확인 (선택사항)

---

### 3. 리포트 생성

#### /로그인 명령어 사용 (첫 1회만)

```
/로그인
```

1. Discord 채널에 `/로그인` 입력
<img width="1441" height="820" alt="image" src="https://github.com/user-attachments/assets/57527c42-4786-47c5-ae73-429ad50041ca" />
</br>
2. Bot이 "Google 로그인 필요" 메시지 전송
<img width="481" height="134" alt="image" src="https://github.com/user-attachments/assets/2d24df22-9e73-4a56-9473-9e22447fbf50" />
</br>
3. Bot이 전송한 URL 클릭 (예: `https://accounts.google.com/...` 형태)
</br>
4. 브라우저에서 Google 계정으로 로그인
</br>
5. "허용" 버튼 클릭하여 권한 부여
</br>
6. Bot이 "설정 완료" 또는 "노트북 생성됨" 확인 메시지 전송
<img width="1090" height="510" alt="image" src="https://github.com/user-attachments/assets/70788b5e-0c7a-4c66-974d-5cd35db68212" />




#### /시작 명령어 사용 (매일 사용)

```
/시작
```
<img width="1099" height="336" alt="image" src="https://github.com/user-attachments/assets/e5404f31-dac2-428a-b9ec-8578695d4190" />

1. Discord 채널에 `/시작` 입력
2. Bot이 순차적으로 처리:
   - `📅 캘린더 데이터 수집 중...` → 캘린더 일정 수집
   - `📧 Gmail 데이터 수집 중...` → 메일 수집
   - `💾 Drive 데이터 수집 중...` → Drive 문서 수집
   - `🔍 NotebookLM 분석 중...` → AI 분석
3. 분석 완료 후 Discord에 리포트 전송
<img width="632" height="1100" alt="image" src="https://github.com/user-attachments/assets/d99b51f2-dd78-4d92-8487-8b058f94f28a" />

---

## 명령어 모음

<img width="645" height="386" alt="image" src="https://github.com/user-attachments/assets/806d07b3-be9a-4f42-a44a-e147bb542b65" />


| 명령어 | 설명 |
|--------|------|
| `/도움말` | 모든 명령어와 사용 방법 확인 |
| `/로그인` | 처음 1회 설정 (Google 권한 부여 + 노트북 생성) |
| `/시작` | 데이터 수집 + NotebookLM 분석 + 리포트 전송 |
| `/리포트` | Drive에 저장된 최근 리포트 가져오기 |
| `/자동실행 18:00` | 매일 정해진 시간에 자동 리포트 생성 |
| `/자동실행 off` | 자동 실행 해제 |

---

## Bot 접속 시 자동 안내

Bot이 서버에 접속하면 자동으로 사용 안내 메시지가 전송됩니다.

```
┌─────────────────────────────────────────┐
│ 📋 일일 업무 회고 리포트 봇               │ 
│                                          │
│ 🔰 처음 설정 (1회만)                     │
│   /로그인 → Google 로그인 → 설정 완료     │
│                                         │
│ 📊 리포트 생성                           │
│   /시작 → 데이터 수집 → AI 분석           │
│                                         │
│ ⚡ 자동 실행                            │
│   /자동실행 18:00 → 매일 18시 자동        │
│                                         │
│ 💡 명령어 보기                          │
│   /도움말 → 모든 명령어 확인              │
└─────────────────────────────────────────┘
```

---

## 전체 사용 흐름

```
┌─────────────────────────────────────────────────────────┐
│ 1단계: Bot 초대                                          │
│   └─ Discord 초대 URL 열기 → 서버 선택 → 허용 클릭        │
├─────────────────────────────────────────────────────────┤
│ 2단계: 1회 설정 (/로그인)                                │
│   └─ Google 로그인 → 권한 부여 → 노트북 자동 생성         │
├────────────────────────────────────────────────────────┤
│ 3단계: 매일 사용 (/시작)                                │
│   └─ 데이터 수집 → AI 분석 → Discord 리포트 수신         │
└────────────────────────────────────────────────────────┘
```

---

## 사용 예시

```
1. Bot 초대 후 처음 접속
   /로그인
   → Google 로그인 → 설정 완료 메시지

2. 매일 아침 리포트 받기
   /시작
   → 캘린더 수집 → 메일 수집 → 분석 → 리포트 전송

3. 매일 18시 자동 리포트 설정
   /자동실행 18:00
   → 매일 18시에 자동 리포트 생성

4. 이전 리포트 다시 보기
   /리포트
   → Drive에서 최근 리포트 가져와서 전송
```

---

## ⚠️ 주의사항

- **PC 실행 시**: Bot은 항상 실행 중이어야 합니다. PC를 끄면 동작 안 합니다. (제 컴퓨터에서 계속 실행 중인 상태입니다.)
- **서버 관리자 권한**: Bot을 초대하려면 서버 관리자이거나 관리자 역할이 필요합니다.
- **Google 권한**: `/로그인` 시 Google 계정 권한 부여가 필요합니다.
- **자동실행**: PC가 꺼지면 자동실행도 작동하지 않습니다. (24시간 가동 서버 필요)
