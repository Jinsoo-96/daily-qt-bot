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
        
        # 날짜 추출 (0000.00.00 형식)
        date = soup.select_one('.date li:nth-child(2)').get_text(strip=True) if soup.select_one('.date li:nth-child(2)') else "0000.00.00"
        
        qt_header = soup.select_one('.font-size h1')
        # [수정] 성경 범위에서 모든 공백 제거 (예: 2:28~3:12)
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', '').replace(' ', '')
        # 큐티 제목 추출
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')
        
        bible_div = soup.select_one('.bible')
        # [수정] 본문 구성: 제목에서 성경 범위(bible_range)는 제외함
        content_parts = [
            f"# {qt_title}",
            "~~　　　　　　　　　　　　　　　　　　　　~~", # 가로선 효과
            "\n"
        ]
        
        for el in bible_div.find_all(['p', 'table']):
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"\n**{el.get_text(strip=True)}**")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                
                # '숫자.' 형식을 사용하면 디스코드에서 자동으로 들여쓰기 리스트를 만듭니다.
                # 단, 인용구(>) 안에서 사용하면 왼쪽 바(|)와 함께 정렬되어 훨씬 보기 좋습니다.
                content_parts.append(f"> {num}. {txt}")
                
        content_parts.append("**💡 오늘도 주님의 말씀으로 승리하는 하루가 됩시다!** \n@everyone")
        
        full_content = "\n".join(content_parts)
        if len(full_content) > 1950:
            full_content = full_content[:1950] + "\n\n...(본문이 길어 생략되었습니다)"
            
        return date, qt_title, bible_range, full_content
    except:
        return None, None, None, None

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
        date, title, bible_range, content = get_qt_data()
        if not content:
            await client.close()
            return
        
        try:
            channel = await client.fetch_channel(channel_id)
            if isinstance(channel, discord.ForumChannel):
                # 1. 기존 고정 해제 (최신순 필터링)
                active_threads = await channel.guild.active_threads()
                for thread in active_threads:
                    if thread.parent_id == channel.id and thread.flags.pinned:
                        await thread.edit(pinned=False)
                        print(f"✔️ 이전 포스트 고정 해제: {thread.name}")
                        break

                # 2. [수정] 새 포스트 생성: 제목에 날짜와 성경 범위를 넣음
                new_post = await channel.create_thread(
                    name=f"[{date}] {bible_range}",
                    content=content 
                )
                
                await asyncio.sleep(2)

                try:
                    # 포스트 상단 고정
                    await new_post.thread.edit(pinned=True)
                    # 본문 메시지 고정
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