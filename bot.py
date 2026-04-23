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
from googleapiclient.discovery import build

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
        description="Google 데이터(일정, 메일, Drive)를 수집하여 자동으로 리포트를 생성합니다.",
        color=0x5865F2
    )
    embed.add_field(name="📌 사용 방법", value="1. `/로그인`으로 설정\n2. `/시작`으로 리포트 생성\n3. `/자동실행`으로 매일 자동 설정", inline=False)
    embed.add_field(name="💡 팁", value="처음에는 `/로그인`만 입력하면 됩니다!", inline=False)

    config = load_config()
    
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(embed=embed)
                break

from notebook_client import NotebookLMClient

CONFIG = load_config()
NOTEBOOK_URL = CONFIG.get('notebook_url')

@bot.tree.command(name='로그인', description='Google 인증을 시작합니다 (처음 1회)')
async def login(ctx):
    config = load_config()
    
    await ctx.response.send_message("🔐 **Google 인증을 시작합니다...**\n브라우저가 열리면 Google로 로그인 해주세요.")
    
    creds = authenticate()
    if not creds:
        await ctx.followup.send("❌ Google 인증에 실패했습니다. 다시 시도해 주세요.")
        return
    
    await ctx.followup.send("🆕 **새 노트북을 생성합니다...**")
    try:
        client = NotebookLMClient(None)
        notebook_url = await client.create_notebook("업무 회고 리포트")
        config['notebook_url'] = notebook_url
        save_config(config)
    except Exception as e:
        await ctx.followup.send(f"⚠️ 노트북 생성 실패: {e}\nhttps://notebooklm.google.com에서 직접 만들어 주세요.")
        return
    
    await ctx.followup.send(
        f"✅ **설정 완료!**\n\n"
        f"👉 이제 `/시작`으로 리포트를 생성해 보세요!"
    )

@bot.tree.command(name='시작', description='업무 데이터를 수집하여 리포트를 생성합니다.')
async def start_cmd(ctx):
    config = load_config()
    notebook_url = config.get('notebook_url')
    
    creds = authenticate()
    if not creds:
        await ctx.response.send_message("❌ **설정이 필요합니다!**\n`/로그인`으로 먼저 설정해 주세요.")
        return
    
    if not notebook_url:
        await ctx.response.send_message("❌ 설정이 필요합니다.\n`/로그인`으로 먼저 설정해 주세요.")
        return

    await ctx.response.send_message("📊 **데이터를 수집 중입니다...**")
    stats = get_today_data()
    
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{date_str}_업무_통합_데이터.txt"
    
    if not os.path.exists(file_name):
        await ctx.followup.send("⚠️ 데이터 파일 생성에 실패했습니다.")
        return

    await ctx.followup.send(f"🧠 **분석 중...**\n(수집 완료: 일정 {stats['events']}, 메일 {stats['emails']}, 채팅 {stats['chats']})")
    
    try:
        client = NotebookLMClient(notebook_url)
        report_content = await client.get_analysis(file_name)
        
        os.remove(file_name)
        
        await ctx.followup.send(f"🏁 **오늘의 업무 회고 리포트**\n{'-'*30}")
        
        if len(report_content) > 2000:
            for i in range(0, len(report_content), 2000):
                await ctx.followup.send(report_content[i:i+2000])
        else:
            await ctx.followup.send(report_content)
            
    except Exception as e:
        await ctx.followup.send(f"❌ 분석 중 오류가 발생했습니다: {e}")

@bot.tree.command(name='리포트', description='Drive에 저장된 최종 업무 보고서를 가져옵니다.')
async def report_cmd(ctx):
    creds = authenticate()
    if not creds:
        await ctx.response.send_message("❌ **설정이 필요합니다.**\n`/로그인 [노트북URL]`로 먼저 설정해 주세요.")
        return
    
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{date_str}_최종_보고서.txt"
    
    await ctx.response.send_message(f"📂 드라이브에서 `{file_name}`을 찾는 중...")
    
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(q=f"name='{file_name}' and trashed=false", fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            await ctx.followup.send(f"⚠️ `{file_name}` 파일을 찾을 수 없습니다.\nNotebookLM 결과를 해당 이름으로 드라이브에 저장해 주세요.")
            return
            
        file_id = files[0]['id']
        content = service.files().get_media(fileId=file_id).execute().decode('utf-8')
        
        await ctx.followup.send(f"🏁 **오늘의 업무 회고 리포트** ({date_str})\n{'-'*30}\n{content}")
        
    except Exception as e:
        await ctx.followup.send(f"❌ 오류 발생: {e}")

async def run_scheduled_report():
    """스케줄된 시간에 실행될 리포트 생성"""
    global bot
    creds = authenticate()
    if not creds:
        return

    config = load_config()
    notebook_url = config.get('notebook_url')
    if not notebook_url:
        return
    
    stats = get_today_data()
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f"{date_str}_업무_통합_데이터.txt"

    if not os.path.exists(file_name):
        return

    try:
        client = NotebookLMClient(notebook_url)
        report_content = await client.get_analysis(file_name)

        os.remove(file_name)

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

@bot.tree.command(name='자동실행', description='매일 자동 실행 시간 설정')
@app_commands.describe(time='시간 (예: 18:00), on/off로 활성화/비활성화')
async def autostart_cmd(ctx, time: str = None):
    global schedule_time, scheduler_running

    if time is None:
        if schedule_time:
            await ctx.response.send_message(f"⏰ 현재 자동 실행 시간: **{schedule_time}**\n`/자동실행 18:00`으로 변경, `/자동실행 off`로 해제")
        else:
            await ctx.response.send_message("⏰ 자동 실행이 설정되지 않았습니다.\n`/자동실행 18:00`으로 시간을 설정해 주세요.")
        return

    if time.lower() == "off":
        scheduler_running = False
        schedule.clear()
        await ctx.response.send_message("⏰ 자동 실행이 비활성화되었습니다.")
        return

    if time.lower() == "on":
        if schedule_time:
            scheduler_running = True
            schedule.every().day.at(schedule_time).do(lambda: asyncio.run(run_scheduled_report()))
            await ctx.response.send_message(f"⏰ 자동 실행이 활성화되었습니다. 매일 {schedule_time}에 실행됩니다.")
        else:
            await ctx.response.send_message("⏰ 설정된 시간이 없습니다. `/자동실행 18:00`으로 시간을 설정해 주세요.")
        return

    try:
        datetime.datetime.strptime(time, "%H:%M")
    except ValueError:
        await ctx.response.send_message("❌ 시간 형식이 올바르지 않습니다.\n예: `/자동실행 18:00`")
        return

    schedule_time = time
    scheduler_running = True
    schedule.clear()
    schedule.every().day.at(time).do(lambda: asyncio.run(run_scheduled_report()))

    await ctx.response.send_message(f"⏰ 자동 실행 시간이 **{time}**로 설정되었습니다.\n매일 이 시간에 자동으로 리포트가 생성됩니다.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
