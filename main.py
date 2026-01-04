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
            # fetch_channel로 최신 채널 상태 강제 동기화
            channel = await client.fetch_channel(channel_id)
        except:
            await client.close()
            return

        if isinstance(channel, discord.ForumChannel):
            # 1. [핵심 수정] 기존 고정 포스트 해제
            print("🔓 기존 고정 포스트 해제 확인 중...")
            try:
                # 활성화된 모든 스레드를 가져옵니다.
                threads = await channel.guild.active_threads()
                for thread in threads:
                    # 해당 포럼 채널의 스레드이고, 고정(flags.pinned) 상태인지 확인
                    if thread.parent_id == channel.id and thread.flags.pinned:
                        await thread.edit(pinned=False)
                        print(f"✔️ 이전 포스트 고정 해제: {thread.name}")
                        break 
            except Exception as e:
                print(f"고정 해제 로직 실행 중 오류: {e}")

            # 2. 새 포스트 생성
            embed = discord.Embed(description=content, color=0x57F287)
            embed.set_footer(text="출처: 두란노 생명의 삶", icon_url="https://www.duranno.com/favicon.ico")
            
            # create_thread는 Thread 객체를 반환하며, 내부 메시지는 .message로 접근
            new_thread = await channel.create_thread(
                name=f"[{date}] {title}",
                content=f"📖 **{date}** 오늘의 말씀이 도착했습니다! @everyone",
                embed=embed
            )
            
            await asyncio.sleep(2) 

            # 3. [최종 단계] 이중 고정 수행 (포스트 상단 + 본문 메시지)
            try:
                # (1) 포스트 자체를 포럼 상단에 고정
                await new_thread.thread.edit(pinned=True)
                # (2) 포스트 내부의 첫 메시지 고정
                await new_thread.message.pin()
                print(f"🚀 [{date}] 새 포스트 상단 고정 및 본문 고정 완료!")
            except Exception as e:
                print(f"고정 작업 최종 실패: {e}")

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())