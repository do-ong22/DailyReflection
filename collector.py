import os
import json
import datetime
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    return datetime.datetime.now(KST)

# 필요한 권한 범위 (모두 읽기 전용으로 제한)
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: 'credentials.json' 파일을 찾을 수 없습니다.")
                print("Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하여 다운로드하세요.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_today_data():
    creds = authenticate()
    if not creds:
        return

    now = get_kst_now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    today_str = now.strftime('%Y-%m-%d')

    data = {
        "date": today_str,
        "events": [],
        "communications": {"emails": [], "chats": []},
        "artifacts": []
    }

    # 1. Google Calendar (오늘과 내일 일정 수집)
    try:
        service = build('calendar', 'v3', credentials=creds)
        # 2일치 데이터 수집 (KST 기준)
        tomorrow = now + datetime.timedelta(days=1)
        end_of_tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        
        events_result = service.events().list(calendarId='primary', timeMin=start_of_day,
                                              timeMax=end_of_tomorrow, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        data['events'] = []
        data['tomorrow_events'] = []
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_date = start[:10]
            event_data = {
                "time": start[11:16] if 'T' in start else "All Day",
                "title": event.get('summary', '(No Title)'),
                "desc": event.get('description', '')
            }
            
            if event_date == today_str:
                data['events'].append(event_data)
            else:
                data['tomorrow_events'].append(event_data)
    except Exception as e:
        print(f"Calendar Error: {e}")

    # 2. Gmail & Google Chat (Gmail API를 통해 채팅 검색 가미)
    try:
        service = build('gmail', 'v1', credentials=creds)
        # 일반 메일 검색
        email_query = f"after:{today_str.replace('-', '/')} -label:chat"
        email_results = service.users().messages().list(userId='me', q=email_query).execute()
        for msg in email_results.get('messages', [])[:10]:
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = m['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            data['communications']['emails'].append({
                "from": sender,
                "subject": subject,
                "snippet": m.get('snippet', '')
            })

        # 구글 채팅 검색 (Gmail API의 is:chat 필터 활용)
        chat_query = f"after:{today_str.replace('-', '/')} is:chat"
        chat_results = service.users().messages().list(userId='me', q=chat_query).execute()
        for msg in chat_results.get('messages', [])[:10]:
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            sender = next((h['value'] for h in m['payload']['headers'] if h['name'] == 'From'), 'Chat User')
            data['communications']['chats'].append({
                "from": sender,
                "snippet": m.get('snippet', '')
            })
    except Exception as e:
        print(f"Communications Error: {e}")

    # 3. Google Drive
    try:
        service = build('drive', 'v3', credentials=creds)
        query = f"modifiedTime > '{start_of_day}'"
        results = service.files().list(
            q=query, 
            fields="files(id, name, modifiedTime, lastModifyingUser)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        for f in files:
            # 내가 마지막으로 수정한 경우 또는 내가 생성한 경우만 포함
            last_user = f.get('lastModifyingUser', {})
            if last_user.get('me'):
                utc_time = datetime.datetime.strptime(f['modifiedTime'][:19], '%Y-%m-%dT%H:%M:%S')
                kst_time = utc_time + datetime.timedelta(hours=9)
                data['artifacts'].append({
                    "file_name": f['name'],
                    "last_mod": kst_time.strftime('%H:%M')
                })
    except Exception as e:
        print(f"Drive Error: {e}")

    with open('daily_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Successfully saved data to daily_data.json")
    
    # NotebookLM 전용 통합 텍스트 파일 생성 (로컬 저장)
    save_local_context_file(data)
    
    # 수집 통계 반환
    stats = {
        "events": len(data['events']),
        "emails": len(data['communications']['emails']),
        "chats": len(data['communications']['chats']),
        "artifacts": len(data['artifacts'])
    }
    return stats

def save_local_context_file(data):
    """수집된 데이터를 NotebookLM용 텍스트 파일로 만들어 로컬에 저장합니다."""
    try:
        file_name = f"{data['date']}_업무_통합_데이터.txt"
        
        content = [
            f"=== {data['date']} 업무 통합 데이터 소스 ===",
            "\n[1. 오늘의 일정]",
        ]
        # (기존 내용 동일)
        for e in data['events']:
            content.append(f"- {e['time']}: {e['title']}\n  상세: {e['desc'] or '없음'}")
            
        content.append("\n[2. 내일의 일정]")
        for e in data['tomorrow_events']:
            content.append(f"- {e['time']}: {e['title']}")
            
        content.append("\n[3. 이메일 수신 내역]")
        for em in data['communications']['emails']:
            content.append(f"- 보낸이: {em['from']}\n  제목: {em['subject']}\n  요약: {em['snippet']}")
            
        content.append("\n[4. 채팅 메시지 내역]")
        for ch in data['communications']['chats']:
            content.append(f"- 보낸이: {ch['from']}\n  내용: {ch['snippet']}")
            
        content.append("\n[5. 구글 드라이브 문서 작업]")
        for art in data['artifacts']:
            content.append(f"- 파일명: {art['file_name']} (수정시간: {art['last_mod']})")

        full_text = "\n".join(content)
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Created local source file: {file_name}")
            
    except Exception as e:
        print(f"Local Save Error: {e}")

if __name__ == "__main__":
    get_today_data()
