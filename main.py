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
        content_parts = [f"# {qt_title}", f"`📜 {bible_range}`", "---", "### 📖 성경 말씀"]
        for el in bible_div.find_all(['p', 'table']):
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"\n**{el.get_text(strip=True)}**")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                content_parts.append(f"> **{num}** {txt}")
        content_parts.append("*💡 오늘도 주님의 말씀으로 승리하는 청년부가 됩시다!*")
        
        full_content = "\n".join(content_parts)
        # 디스코드 글자 수 제한(2000자) 안전장치
        if len(full_content) > 1950:
            full_content = full_content[:1950] + "\n\n...(이하 생략 - 더 보기는 홈페이지를 참고하세요)"
            
        return date, qt_title, full_content
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
        if not content:
            await client.close()
            return
        
        try:
            channel = await client.fetch_channel(channel_id)
            if isinstance(channel, discord.ForumChannel):
                # 1. 기존 고정 해제 (최신순 루프 최적화)
                active_threads = await channel.guild.active_threads()
                for thread in active_threads:
                    if thread.parent_id == channel.id and thread.flags.pinned:
                        await thread.edit(pinned=False)
                        print(f"✔️ 이전 포스트 고정 해제: {thread.name}")
                        break

                # 2. 새 포스트 생성 (본문 content 사용)
                new_post = await channel.create_thread(
                    name=f"[{date}] {title}",
                    content=content 
                )
                
                await asyncio.sleep(2)

                try:
                    # 포스트 목록 상단 고정
                    await new_post.thread.edit(pinned=True)
                    # 포스트 내부 본문 메시지 고정
                    await new_post.message.pin()
                    print(f"🚀 [{date}] 게시 및 상단 고정 완료!")
                except Exception as e:
                    print(f"고정 실패: {e}")
        except Exception as e:
            print(f"오류 발생: {e}")

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())