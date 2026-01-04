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

        # 1. 날짜 및 제목 정보 추출
        date_el = soup.select_one('.date li:nth-child(2)')
        date = date_el.get_text(strip=True) if date_el else "0000.00.00"

        qt_header = soup.select_one('.font-size h1')
        if not qt_header:
            return None, None, None
            
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')

        # 2. 본문 마크다운 조립 (디자인 업그레이드)
        content_parts = []
        content_parts.append(f"# {qt_title}") # 큰 제목
        content_parts.append(f"`📜 {bible_range}`") # 성경 범위 강조
        content_parts.append("\n---") # 상단 구분선
        content_parts.append("### 📖 성경 말씀")
        
        bible_div = soup.select_one('.bible')
        elements = bible_div.find_all(['p', 'table'])
        
        for el in elements:
            if el.name == 'p' and 'title' in el.get('class', []):
                # 단락 제목이 있는 경우 (예: [하나님의 은혜])
                content_parts.append(f"\n**{el.get_text(strip=True)}**")
            elif el.name == 'table':
                # 실제 성경 구절
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                # 구절마다 왼쪽 라인(인용구) 추가하여 정갈하게 표현
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
        return

    channel_id = int(channel_id_str)
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        date, title, content = get_qt_data()
        channel = client.get_channel(channel_id)

        if channel and isinstance(channel, discord.ForumChannel):
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            # 포스트 생성
            thread_with_message = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀이 도착했습니다! @everyone",
                embed=embed
            )
            
            await asyncio.sleep(1.5)

            # 1. 메시지 고정 (포스트 내부)
            try:
                await thread_with_message.message.pin()
            except: pass

            # 2. 포스트 고정 (포럼 목록)
            try:
                await thread_with_message.thread.edit(pinned=True)
            except: pass

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())