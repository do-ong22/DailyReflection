import json
import asyncio
import os
import subprocess
import sys
import datetime

NLM_PATH = r"C:\Users\DONGGEUNKIM\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\nlm.exe"

def get_kst_today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')

class NotebookLMClient:
    def __init__(self, notebook_url):
        self.notebook_url = notebook_url
        self.notebook_id = notebook_url.split('/')[-1] if notebook_url else None

    async def create_notebook(self, title="업무 회고"):
        """새 노트북을 생성하고 URL을 반환합니다."""
        try:
            process = await asyncio.create_subprocess_exec(
                NLM_PATH, "notebook", "create", title,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                result = stdout.decode('utf-8').strip()
                try:
                    data = json.loads(result)
                    if "value" in data and "url" in data["value"]:
                        return data["value"]["url"]
                except:
                    pass
                if "ID:" in result:
                    notebook_id = result.split("ID: ")[-1].strip()
                    return f"https://notebooklm.google.com/notebook/{notebook_id}"
                return result
            elif stderr:
                error = stderr.decode('utf-8')
                raise Exception(error)
            else:
                raise Exception("노트북 생성 실패")
                
        except Exception as e:
            raise Exception(f"노트북 생성 오류: {e}")

    async def clean_all_sources(self):
        """모든 소스를 삭제합니다."""
        try:
            process = await asyncio.create_subprocess_exec(
                NLM_PATH, "source", "list", self.notebook_id, "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                sources = json.loads(stdout.decode('utf-8'))
                deleted_count = 0
                
                for source in sources:
                    await asyncio.create_subprocess_exec(
                        NLM_PATH, "source", "delete", source['id'], "--confirm",
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    print(f"[소스 삭제] {source['title']}")
                    deleted_count += 1
                
                print(f"총 {deleted_count}개 소스 삭제 완료")
        except Exception as e:
            print(f"[소스 정리 오류]: {e}")

    async def add_source(self, filename):
        """노트북에 소스 파일을 추가합니다."""
        try:
            await self.clean_all_sources()
            
            process = await asyncio.create_subprocess_exec(
                NLM_PATH, "source", "add", self.notebook_id, "--file", filename,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            result = stdout.decode('utf-8') if stdout else stderr.decode('utf-8')
            print(f"[소스 추가]: {result.strip()}")
            return True
        except Exception as e:
            print(f"[소스 추가 오류]: {e}")
            return False

    async def get_analysis(self, data_filename):
        """데이터를 NotebookLM에 전달하고 분석 리포트를 받아옵니다."""
        try:
            await self.add_source(data_filename)
            
            prompt = f"""
전달하는 데이터를 기반으로 '오늘의 업무 회고 리포트'를 작성해줘.
필수적으로 한국어로 작성하고, 아래 섹션 형식을 엄격히 지켜줘:

# 🏁 오늘의 업무 회고 리포트

## 1. 오늘 수행한 주요 업무
- (팩트 위주로 정리)

## 2. ⚠️ 업무 누락 및 미결 사항 (Critical)
- (메일/채팅 요청 사항 중 미결된 것 탐지)

## 3. 내일의 주요 일정 및 준비물
- (내일 일정 및 오늘 작업 연계물)

## 4. AI 한 줄 평
- (칭찬 또는 조언)

업무 데이터를 분석해서 회고 리포트를 작성해주세요.
"""

            print(f"--- NotebookLM 분석 요청 중: {self.notebook_id} ---")
            
            import shlex
            safe_prompt = shlex.quote(prompt)
            
            process = await asyncio.create_subprocess_exec(
                NLM_PATH, "notebook", "query", self.notebook_id, prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                result = stdout.decode('utf-8')
                print(f"[NotebookLM 결과 수신]")
                try:
                    data = json.loads(result)
                    if "value" in data and "answer" in data["value"]:
                        return data["value"]["answer"]
                except:
                    pass
                return result
            elif stderr:
                error = stderr.decode('utf-8')
                return f"❌ 오류 발생: {error}"
            else:
                return "⚠️ NotebookLM에서 응답이 없습니다."
                
        except Exception as e:
            return f"❌ 분석 중 오류 발생: {str(e)}"

if __name__ == "__main__":
    async def test():
        client = NotebookLMClient(env.NOTEBOOK_CLIENT)
        result = await client.get_analysis("테스트 데이터")
        print(result)
    
    asyncio.run(test())