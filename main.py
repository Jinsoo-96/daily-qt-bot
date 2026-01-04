import discord
import requests
from bs4 import BeautifulSoup
import os
import asyncio

def get_qt_data():
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        date_el = soup.select_one('.date li:nth-child(2)')
        date = date_el.get_text(strip=True) if date_el else "0000.00.00"

        qt_header = soup.select_one('.font-size h1')
        if not qt_header:
            return None, None, None
            
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')

        content_parts = []
        content_parts.append(f"# {qt_title}") 
        content_parts.append(f"`📜 {bible_range}`") 
        content_parts.append("\n---") 
        content_parts.append("### 📖 성경 말씀")
        
        bible_div = soup.select_one('.bible')
        elements = bible_div.find_all(['p', 'table'])
        
        for el in elements:
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"\n**{el.get_text(strip=True)}**")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                content_parts.append(f"> **{num}** {txt}")

        content_parts.append("\n---\n*💡 오늘도 주님의 말씀으로 승리하는 청년부가 됩시다!*")
        
        return date, qt_title, "\n".join(content_parts)
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return None, None, None

async def run_bot():
    token = os.environ.get('DISCORD_BOT_TOKEN')
    channel_id_str = os.environ.get('FORUM_CHANNEL_ID')
    
    if not token or not channel_id_str:
        print("❌ 환경변수 설정 오류")
        return

    channel_id = int(channel_id_str)
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 로그인 성공. 작업 시작...')
        date, title, content = get_qt_data()
        channel = client.get_channel(channel_id)

        if channel and isinstance(channel, discord.ForumChannel):
            
            # --- [개선 포인트 1] 기존 고정 포스트 해제 ---
            # 모든 글을 뒤지지 않고 현재 활성화된 스레드 중 고정된 것만 타겟팅
            print("🔓 기존 고정 포스트 확인 중...")
            for thread in channel.threads:
                if thread.pinned:
                    try:
                        await thread.edit(pinned=False)
                        print(f"✔️ 기존 고정 해제 완료: {thread.name}")
                        break # 포럼은 고정이 하나뿐이므로 하나 찾으면 바로 종료
                    except:
                        pass

            # --- [개선 포인트 2] 새 포스트 생성 및 이중 고정 ---
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            # 포스트 생성
            thread_with_message = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀이 도착했습니다! @everyone",
                embed=embed
            )
            
            # 시스템 안정성을 위해 1.5초 대기
            await asyncio.sleep(1.5)

            # 1. 메시지 고정 (포스트 내부 최상단 고정)
            try:
                await thread_with_message.message.pin()
                print("📌 포스트 내부 본문 고정 성공")
            except: pass

            # 2. 포스트 고정 (포럼 목록 최상단 고정)
            try:
                await thread_with_message.thread.edit(pinned=True)
                print("🔝 포럼 목록 상단 고정 성공")
            except: pass

            print(f"🚀 [{date}] 모든 게시 및 정리 작업 완료!")
        
        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())