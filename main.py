import discord
import requests
from bs4 import BeautifulSoup
import os
import asyncio

# 1. 두란노 생명의 삶 데이터 스크래핑
def get_qt_data():
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 날짜 추출
        date_el = soup.select_one('.date li:nth-child(2)')
        date = date_el.get_text(strip=True) if date_el else "0000.00.00"

        # 제목 및 성경 범위 추출
        qt_header = soup.select_one('.font-size h1')
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')

        # 본문 내용 마크다운 구성
        bible_div = soup.select_one('.bible')
        content_parts = []
        content_parts.append(f"# {qt_title}") 
        content_parts.append(f"> **{bible_range}**\n")

        elements = bible_div.find_all(['p', 'table'])
        for el in elements:
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"### 📌 {el.get_text(strip=True)}")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                content_parts.append(f"**{num}** {txt}")

        return date, qt_title, "\n".join(content_parts)
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return None, None, None

# 2. 디스코드 봇 실행 및 포스트 생성/고정
async def run_bot():
    token = os.environ.get('DISCORD_BOT_TOKEN')
    channel_id_str = os.environ.get('FORUM_CHANNEL_ID')
    
    if not token or not channel_id_str:
        print("❌ 환경변수(TOKEN 또는 ID)가 설정되지 않았습니다.")
        return

    channel_id = int(channel_id_str)
    
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 계정으로 로그인 성공!')
        date, title, content = get_qt_data()
        
        if not date:
            await client.close()
            return

        channel = client.get_channel(channel_id)
        if channel and isinstance(channel, discord.ForumChannel):
            # 새 포스트 생성
            embed = discord.Embed(description=content, color=0x57F287) # 연두색(성장)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            # 포스트 생성 (thread_name 사용)
            thread_info = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 {date} 오늘의 말씀이 도착했습니다! @everyone",
                embed=embed
            )
            
            # 생성된 포스트 즉시 고정
            await thread_info.thread.edit(pinned=True)
            print(f"🚀 [{date}] 포스트 생성 및 고정 완료!")
        else:
            print("❌ 포럼 채널을 찾을 수 없거나 ID가 올바르지 않습니다.")
        
        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())