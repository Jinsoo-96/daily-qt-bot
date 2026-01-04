import discord
import requests
from bs4 import BeautifulSoup
import os
import asyncio

# 1. 데이터 가져오기 (기존과 동일)
def get_qt_data():
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        date = soup.select_one('.date li:nth-child(2)').get_text(strip=True) if soup.select_one('.date li:nth-child(2)') else "0000.00.00"
        qt_header = soup.select_one('.font-size h1')
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')

        content_parts = [f"# {qt_title}", f"> **{bible_range}**\n"]
        bible_div = soup.select_one('.bible')
        for el in bible_div.find_all(['p', 'table']):
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"### 📌 {el.get_text(strip=True)}")
            elif el.name == 'table':
                content_parts.append(f"**{el.find('th').get_text(strip=True)}** {el.find('td').get_text(strip=True)}")
        
        return date, qt_title, "\n".join(content_parts)
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return None, None, None

# 2. 봇 실행 및 "메시지" 고정 로직
async def run_bot():
    token = os.environ.get('DISCORD_BOT_TOKEN')
    channel_id_str = os.environ.get('FORUM_CHANNEL_ID')
    channel_id = int(channel_id_str)
    
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user}로 로그인 성공!')
        date, title, content = get_qt_data()
        channel = client.get_channel(channel_id)

        if channel and isinstance(channel, discord.ForumChannel):
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            # 포스트 생성
            # thread_with_message.message가 바로 본문 메시지입니다.
            thread_with_message = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 {date} 오늘의 말씀 @everyone",
                embed=embed
            )
            
            # [수정 포인트] 생성된 포스트의 '첫 번째 메시지'를 고정합니다.
            await thread_with_message.message.pin()
            print(f"✅ [{date}] 포스트 내부 메시지 고정 완료!")
        
        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())