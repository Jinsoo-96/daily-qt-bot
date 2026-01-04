import discord
import requests
from bs4 import BeautifulSoup
import os
import asyncio

def get_qt_data():
    # ... (데이터 스크래핑 로직은 이전과 동일)
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        date_el = soup.select_one('.date li:nth-child(2)')
        date = date_el.get_text(strip=True) if date_el else "0000.00.00"
        qt_header = soup.select_one('.font-size h1')
        if not qt_header: return None, None, None
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')
        bible_div = soup.select_one('.bible')
        content_parts = [f"# {qt_title}", f"`📜 {bible_range}`", "\n---", "### 📖 성경 말씀"]
        for el in bible_div.find_all(['p', 'table']):
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"\n**{el.get_text(strip=True)}**")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                content_parts.append(f"> **{num}** {txt}")
        content_parts.append("\n---\n*💡 오늘도 주님의 말씀으로 승리하는 청년부가 됩시다!*")
        return date, qt_title, "\n".join(content_parts)
    except: return None, None, None

async def run_bot():
    token = os.environ.get('DISCORD_BOT_TOKEN')
    channel_id = int(os.environ.get('FORUM_CHANNEL_ID'))
    
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 로그인 성공')
        date, title, content = get_qt_data()
        channel = client.get_channel(channel_id)

        if channel and isinstance(channel, discord.ForumChannel):
            
            # [추가된 로직] 1. 기존에 고정된 포스트들 모두 고정 해제
            print("🔍 기존 고정 포스트 정리 중...")
            for thread in channel.threads:
                if thread.pinned:
                    try:
                        await thread.edit(pinned=False)
                        print(f"🔓 기존 고정 해제: {thread.name}")
                    except:
                        pass
            
            # 아카이브(숨겨진) 된 스레드 중에서도 고정된 게 있을 수 있으므로 처리
            async for thread in channel.archived_threads(pinned=True):
                try:
                    await thread.edit(pinned=False)
                except:
                    pass

            # 2. 새 포스트 생성
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            thread_with_message = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀이 도착했습니다! @everyone",
                embed=embed
            )
            
            await asyncio.sleep(1.5)

            # 3. 새 본문 메시지 고정 (내부)
            try:
                await thread_with_message.message.pin()
                print("📌 새 본문 메시지 고정 완료")
            except: pass

            # 4. 새 포스트 상단 고정 (포럼 목록)
            try:
                await thread_with_message.thread.edit(pinned=True)
                print("🔝 새 포스트 상단 고정 완료")
            except: pass

            print(f"🚀 오늘의 QT 게시 및 정리 완료!")
        
        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())