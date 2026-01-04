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
    intents.guilds = True  # 서버 정보를 읽기 위해 필수
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 로그인 성공.')
        date, title, content = get_qt_data()
        
        # 1. 채널 객체 획득 (캐시가 아닌 서버에서 직접 가져오기)
        try:
            channel = await client.fetch_channel(channel_id)
        except Exception as e:
            print(f"채널 획득 실패: {e}")
            await client.close()
            return

        if channel and isinstance(channel, discord.ForumChannel):
            # 2. [핵심] 기존 고정 포스트(Thread) 해제
            print("🔓 기존 고정 포스트 해제 시도...")
            # channel.threads는 현재 떠있는 스레드만 보여주므로, 
            # 확실하게 '고정된 목록'을 불러오는 fetch_threads() 활용
            try:
                # 활성 스레드 중 고정된 것을 필터링
                active_threads = await channel.guild.active_threads()
                for thread in active_threads:
                    if thread.parent_id == channel.id and thread.pinned:
                        await thread.edit(pinned=False)
                        print(f"✔️ 이전 포스트 고정 해제: {thread.name}")
                        break # 하나만 고정되므로 하나 찾으면 종료
            except Exception as e:
                print(f"고정 해제 중 오류: {e}")

            # 3. 새 포스트 생성
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            new_post = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀이 도착했습니다! @everyone",
                embed=embed
            )
            
            # 4. 새 포스트 '목록 상단' 고정 및 '내부 본문' 고정
            await asyncio.sleep(2) # 서버 반영 대기
            try:
                # 포스트 자체를 포럼 상단에 고정 (사용자님이 원하시는 기능)
                await new_post.thread.edit(pinned=True)
                # 포스트 내부 첫 메시지 고정 (가독성용)
                await new_post.message.pin()
                print(f"🚀 [{date}] 새 포스트 상단 고정 완료!")
            except Exception as e:
                print(f"고정 실패: {e}")

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())