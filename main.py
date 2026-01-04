import discord
import requests
from bs4 import BeautifulSoup
import os
import asyncio

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
    channel_id_str = os.environ.get('FORUM_CHANNEL_ID')
    if not token or not channel_id_str: return
    
    channel_id = int(channel_id_str)
    intents = discord.Intents.default()
    # ⚠️ 중요: 봇이 채널 정보를 제대로 읽으려면 아래 설정이 필요합니다.
    intents.guilds = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 로그인 성공. 작업 시작...')
        date, title, content = get_qt_data()
        channel = client.get_channel(channel_id)

        if channel and isinstance(channel, discord.ForumChannel):
            # [수정] channel.threads 대신 active_threads() 사용하여 실시간 서버 데이터 호출
            print("🔍 기존 고정 게시물 찾는 중...")
            try:
                # 활성 스레드 목록을 서버에서 직접 가져옵니다.
                active_threads = await channel.guild.active_threads()
                for thread in active_threads:
                    # 해당 포럼 채널에 속해 있고, 고정된(pinned) 스레드인지 확인
                    if thread.parent_id == channel.id and thread.pinned:
                        await thread.edit(pinned=False)
                        print(f"🔓 기존 고정 해제: {thread.name}")
                        break # 하나만 풀면 되므로 즉시 탈출
            except Exception as e:
                print(f"고정 해제 과정 오류(무시가능): {e}")

            # 새 포스트 생성
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            thread_with_message = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀 @everyone",
                embed=embed
            )
            
            await asyncio.sleep(2) # 서버 반영 대기

            # 본문 메시지 고정 및 포스트 상단 고정
            try:
                await thread_with_message.message.pin()
                await thread_with_message.thread.edit(pinned=True)
                print(f"🚀 [{date}] 게시 및 고정 완료!")
            except Exception as e:
                print(f"고정 작업 실패: {e}")

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())