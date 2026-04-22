import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import datetime
import asyncio
import threading
import schedule
from dotenv import load_dotenv
from collector import authenticate, get_today_data

# .env 로드
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# 디스코드 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 스케줄 관련 변수
schedule_time = None
scheduler_running = False

def analyze_gaps(data):
    """메일/채팅에서 요청사항 및 누락 과업을 탐지합니다."""
    emails = data.get('communications', {}).get('emails', [])
    chats = data.get('communications', {}).get('chats', [])
    events = data.get('events', [])
    artifacts = data.get('artifacts', [])
    
    gaps = []
    
    # 의무 표현 키워드
    keywords = ["요청", "부탁", "확인", "전달", "드릴게요", "주세요", "까지", "언제", "회의"]
    
    # 1. 메일 분석
    for email in emails:
        content = (email['subject'] + email['snippet']).lower()
        if any(kw in content for kw in keywords):
            # 관련 문서 작업이 있는지 확인 (간이 매칭)
            related_found = any(email['subject'][:5] in art['file_name'] for art in artifacts)
            if not related_found:
                gaps.append(f"**메일 피드백 누락**: {email['from']}님의 '{email['subject']}' 메일에 대한 후속 조치가 감지되지 않았습니다.")
                
    # 2. 채팅 분석
    for chat in chats:
        if any(kw in chat['snippet'] for kw in keywords):
            gaps.append(f"**채팅 확인 필요**: {chat['sender'] if 'sender' in chat else chat['from']}님의 요청 사항('{chat['snippet'][:20]}...')에 대한 자료 준비 상태를 확인해 보세요.")
            
    # 3. 일정-문서 불일치 분석 (점심 제외)
    for event in events:
        if event['time'] == "All Day": continue
        if "점심" in event['title'] or "Lunch" in event['title']: continue
        
        related_found = False
        event_keywords = [kw for kw in event['title'].split() if len(kw) > 1]
        for art in artifacts:
            if any(kw in art['file_name'] for kw in event_keywords):
                related_found = True
                break
        
        if not related_found:
            gaps.append(f"**일정 미결 소견**: '{event['title']}' 일정이 있었으나 관련 작업 결과물(Drive 문서 등)이 확인되지 않았습니다.")

    return gaps

def generate_report(data):
    """gemini.md의 결과물 형식(Section 4)을 정확히 따르는 리포트를 생성합니다."""
    report = [f"# 🏁 오늘의 업무 회고 리포트"]
    
    events = data.get('events', [])
    artifacts = data.get('artifacts', [])
    emails = data.get('communications', {}).get('emails', [])
    chats = data.get('communications', {}).get('chats', [])

    # 1. 오늘 수행한 주요 업무
    report.append("\n## 1. 오늘 수행한 주요 업무")
    tasks = []
    if artifacts:
        for art in artifacts:
            tasks.append(f"**[문서 작업]** {art['file_name']} 업데이트 (Drive 이력 근거)")
    
    for event in events:
        if event['time'] != "All Day" and "점심" not in event['title'] and "Lunch" not in event['title']:
            event_text = f"**[일정 소화]** {event['title']} ({event['time']})"
            # 설명(desc)이 있으면 추가 정보로 표시
            if event.get('desc') and len(event['desc']) > 5:
                # HTML 태그 제거 (간이)
                clean_desc = event['desc'].replace('<br>', '\n').replace('<b>', '').replace('</b>', '').strip()
                if len(clean_desc) > 100:
                    clean_desc = clean_desc[:100] + "..."
                event_text += f"\n  └ *상세: {clean_desc}*"
            tasks.append(event_text)
            
    if tasks:
        for task in tasks[:5]:
            report.append(f"- {task}")
    else:
        report.append("- 오늘 기록된 주요 업무 수행 내역이 없습니다.")

    # 2. 업무 누락 및 미결 사항 (Critical)
    report.append("\n## 2. ⚠️ 업무 누락 및 미결 사항")
    gaps = analyze_gaps(data)
    if gaps:
        for gap in gaps[:4]:
            report.append(f"- {gap}")
    else:
        report.append("- 현재 감지된 주요 누락 사항이 없습니다. 차분한 마무리가 가능합니다.")

    # 3. 내일의 주요 일정 및 준비물
    report.append("\n## 3. 내일의 주요 일정 및 준비물")
    tomorrow_events = data.get('tomorrow_events', [])
    if tomorrow_events:
        for event in tomorrow_events:
            report.append(f"- **{event['time']}**: {event['title']}")
    else:
        report.append("- 특별한 내일 일정이 등록되어 있지 않습니다.")
    
    if artifacts:
        report.append(f"- **[준비물]**: 오늘 작업한 {artifacts[0]['file_name']} 최종본")

    # 4. AI 한 줄 평
    report.append("\n## 4. 한 줄 평")
    if gaps:
        report.append("\"오늘 수신된 요청 사항들 중 일부 미결된 항목이 보입니다. 퇴근 전 간단한 피드백을 남겨 업무 누락을 방지하는 것을 추천합니다.\"")
    else:
        report.append("\"오늘 계획된 일정과 목표를 차질 없이 수행하셨습니다. 완벽한 하루 마무리입니다!\"")

    return "\n".join(report)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Logged in as {bot.user.name}')
    print(f'✅ Slash commands synced')

    embed = discord.Embed(
        title="📋 일일 업무 회고 리포트 봇",
        description="업무 데이터를 자동으로 수집하여 AI 분석 리포트를 생성합니다.",
        color=0x5865F2
    )
    embed.add_field(name="📌 사용 가능한 명령어", value="", inline=False)
    embed.add_field(name="/login", value="Google OAuth 인증 시작 (최초 1회)", inline=True)
    embed.add_field(name="/start", value="업무 데이터 수집 및 리포트 생성", inline=True)
    embed.add_field(name="/report", value="Drive에서 최종 보고서 가져오기", inline=True)
    embed.add_field(name="/autostart", value="자동 실행 시간 설정 (예: /autostart 18:00)", inline=True)
    embed.add_field(name="----------", value="----------", inline=False)
    embed.add_field(name="💡 팁", value="`/autostart 18:00`로 매일 자동 생성 가능!", inline=False)

    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(embed=embed)
                break

from notebook_client import NotebookLMClient

NOTEBOOK_URL = os.getenv('NOTEBOOK_URL')

@bot.tree.command(name='start', description='업무 데이터를 수집하고 AI 분석 업무 회고 리포트를 생성합니다.')
async def start(ctx):
    creds = authenticate()
    if not creds:
        await ctx.send("❌ `/login`을 먼저 진행해 주세요.")
        return

    status_msg = await ctx.send("📊 데이터를 수집 중입니다...")
    stats = get_today_data()
    
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{date_str}_업무_통합_데이터.txt"
    
    if not os.path.exists(file_name):
        await status_msg.edit(content="⚠️ 데이터 파일 생성에 실패했습니다.")
        return

    await status_msg.edit(content=f"🧠 **NotebookLM(Gemini 2.5) 분석 시작...**\n(수집 완료: 일정 {stats['events']}, 메일 {stats['emails']}, 채팅 {stats['chats']})")
    
    try:
        # NotebookLM API(MCP) 호출
        client = NotebookLMClient(NOTEBOOK_URL)
        report_content = await client.get_analysis(file_name)
        
        # 3. 결과 전송
        await ctx.send(f"🏁 **오늘의 업무 회고 리포트 (NotebookLM 자동 분석)**\n{'-'*30}")
        
        # 2000자 초과 시 분할 전송
        if len(report_content) > 2000:
            for i in range(0, len(report_content), 2000):
                await ctx.send(report_content[i:i+2000])
        else:
            await ctx.send(report_content)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(content=f"❌ 분석 중 오류가 발생했습니다: {e}")

@bot.tree.command(name='report', description='Drive에 저장된 최종 업무 보고서를 가져옵니다.')
async def report(ctx):
    creds = authenticate()
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{date_str}_최종_보고서.txt"
    
    status_msg = await ctx.send(f"📂 드라이브에서 `{file_name}`을 찾는 중...")
    
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(q=f"name='{file_name}' and trashed=false", fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            await status_msg.edit(content=f"⚠️ `{file_name}` 파일을 찾을 수 없습니다. NotebookLM 결과를 해당 이름으로 드라이브에 저장해 주세요.")
            return
            
        file_id = files[0]['id']
        content = service.files().get_media(fileId=file_id).execute().decode('utf-8')
        
        await ctx.send(f"🏁 **NotebookLM 기반 최종 업무 회고 리포트** ({date_str})\n{'-'*30}\n{content}")
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(content=f"❌ 오류 발생: {e}")

@bot.tree.command(name='login', description='Google OAuth 인증을 시작합니다 (최초 1회)')
async def login(ctx):
    await ctx.send("🔗 구글 인증을 시작합니다. 콘솔의 안내를 따라주세요.")
    authenticate()
    await ctx.send("✅ 인증 완료! 이제 `/start`를 사용해 보세요.")

async def run_scheduled_report():
    """스케줄된 시간에 실행될 리포트 생성"""
    global bot
    creds = authenticate()
    if not creds:
        return

    stats = get_today_data()
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{date_str}_업무_통합_데이터.txt"

    if not os.path.exists(file_name):
        return

    try:
        client = NotebookLMClient(NOTEBOOK_URL)
        report_content = await client.get_analysis(file_name)

        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(f"🏁 **오늘의 업무 회고 리포트 (자동 생성)**\n{'-'*30}")
                    if len(report_content) > 2000:
                        for i in range(0, len(report_content), 2000):
                            await channel.send(report_content[i:i+2000])
                    else:
                        await channel.send(report_content)
                    break
    except Exception as e:
        print(f"[스케줄러] 오류: {e}")

def schedule_runner():
    """스케줄러 실행 루프"""
    while scheduler_running:
        schedule.run_pending()
        asyncio.sleep(1)

@bot.tree.command(name='autostart', description='자동 실행 시간 설정 (예: /autostart 18:00)')
@app_commands.describe(time="설정할 시간 (예: 18:00), on/off로 활성화/비활성화")
async def autostart(ctx, time: str = None):
    global schedule_time, scheduler_running

    if time is None:
        if schedule_time:
            await ctx.send(f"⏰ 현재 자동 실행 시간: **{schedule_time}** (on/off로 변경 가능)")
        else:
            await ctx.send("⏰ 자동 실행이 설정되지 않았습니다. `/autostart 18:00` 형태로 시간을 설정해 주세요.")
        return

    if time.lower() == "off":
        scheduler_running = False
        schedule.clear()
        await ctx.send("⏰ 자동 실행이 비활성화되었습니다.")
        return

    if time.lower() == "on":
        if schedule_time:
            scheduler_running = True
            schedule.every().day.at(schedule_time).do(lambda: asyncio.run(run_scheduled_report()))
            await ctx.send(f"⏰ 자동 실행이 활성화되었습니다. 매일 {schedule_time}에 실행됩니다.")
        else:
            await ctx.send("⏰ 설정된 시간이 없습니다. `/autostart 18:00` 형태로 시간을 설정해 주세요.")
        return

    try:
        datetime.datetime.strptime(time, "%H:%M")
    except ValueError:
        await ctx.send("❌ 시간 형식이 올바르지 않습니다. 예: 18:00")
        return

    schedule_time = time
    scheduler_running = True
    schedule.clear()
    schedule.every().day.at(time).do(lambda: asyncio.run(run_scheduled_report()))

    await ctx.send(f"⏰ 자동 실행 시간이 **{time}**로 설정되었습니다. 이제 매일 이 시간에 자동으로 보고서가 생성됩니다.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
