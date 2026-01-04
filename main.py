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
    intents.guilds = True 
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 로그인 성공.')
        date, title, content = get_qt_data()
        
        try:
            channel = await client.fetch_channel(channel_id)
        except:
            await client.close()
            return

        if isinstance(channel, discord.ForumChannel):
            # [최적화 핵심] 전체 스레드가 아닌 '고정된 메시지/포스트'만 즉시 가져오기
            print("🔓 기존 고정 게시물 해제 작업 시작...")
            try:
                # pins()는 채널 내 고정된 모든 항목을 리스트로 반환합니다.
                pinned_items = await channel.pins() 
                for item in pinned_items:
                    # 포스트(스레드) 고정은 메시지의 thread 속성을 통해 접근합니다.
                    if item.thread and item.thread.flags.pinned:
                        await item.thread.edit(pinned=False)
                        print(f"✔️ 기존 고정 해제 성공: {item.thread.name}")
                        break # 포럼 고정은 하나뿐이므로 즉시 탈출
            except Exception as e:
                print(f"고정 해제 과정 중 알림: {e}")

            # 새 포스트 생성 및 고정
            new_thread = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀이 도착했습니다! @everyone",
                embed=discord.Embed(description=content, color=0x57F287)
            )
            
            await asyncio.sleep(2) 

            try:
                # 포스트 상단 고정 (가장 중요한 자동화 영역)
                await new_thread.thread.edit(pinned=True)
                # 본문 메시지 핀
                await new_thread.message.pin()
                print(f"🚀 [{date}] 새 포스트 상단 고정 완료!")
            except Exception as e:
                print(f"고정 작업 실패: {e}")

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())