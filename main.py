import discord
import requests
from bs4 import BeautifulSoup
import os
import re
import asyncio

def get_qt_data():
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 날짜 추출
        date = soup.select_one('.date li:nth-child(2)').get_text(strip=True) if soup.select_one('.date li:nth-child(2)') else "0000.00.00"
        
        qt_header = soup.select_one('.font-size h1')
        # 1. 모든 공백을 제거 (요한일서2:28~3:12)
        raw_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', '').replace(' ', '')
        
        # 2. 숫자가 처음 등장하는 위치를 찾아 그 앞에 공백 2개 삽입
        # 결과: 요한일서  2:28~3:12
        bible_range = re.sub(r'(\d)', r'  \1', raw_range, count=1)
        # 큐티 제목
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')
        
        bible_div = soup.select_one('.bible')
        content_parts = [
            f"## {bible_range}",
            f"### {qt_title}",
            "~~　　　　　　　　　　　　　　　　　　　　~~", 
        ]
        
        for el in bible_div.find_all(['p', 'table']):
            if el.name == 'p' and 'title' in el.get('class', []):
                # [하늘색 적용] 텍스트를 ' '로 감싸면 하늘색 박스가 됩니다.
                title_text = el.get_text(strip=True)
                content_parts.append(f"```py\n'{title_text}'```")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                # 숫자 목록 마크다운 (자동 들여쓰기 정렬)
                content_parts.append(f"{num}. {txt}")
                
        # [수정된 부분] 들여쓰기 위치 조정 및 안전한 메시지 결합
        footer = f"\n\n\n**💡 오늘도 주님의 말씀으로 승리하는 하루가 됩시다!**\n\n@everyone  [_]({url})"
        main_body = "\n".join(content_parts)
        
        # 디스코드 2000자 제한 대응 (footer 길이를 뺀 나머지만 본문 허용)
        max_body_length = 1980 - len(footer)
        if len(main_body) > max_body_length:
            main_body = main_body[:max_body_length - 35] + "\n\n...(본문이 길어 생략되었습니다)"
        
        full_content = main_body + footer
        return date, qt_title, bible_range, full_content
        
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return None, None, None, None

async def run_bot():
    token = os.environ.get('DISCORD_BOT_TOKEN')
    channel_id_str = os.environ.get('FORUM_CHANNEL_ID')
    if not token or not channel_id_str: 
        print("❌ 환경 변수 설정이 누락되었습니다.")
        return
    
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
            print("❌ 콘텐츠를 가져오지 못했습니다.")
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

                # 2. 새 포스트 생성 (제목: 날짜)
                new_post = await channel.create_thread(
                    name=f"{date}",
                    content=content 
                )
                
                await asyncio.sleep(2)

                try:
                    # 포스트 목록 상단 고정
                    await new_post.thread.edit(pinned=True)
                    # 포스트 내부 첫 메시지 고정
                    await new_post.message.pin()
                    print(f"🚀 [{date}] 게시 및 상단 고정 완료!")
                except Exception as e:
                    print(f"고정 작업 중 오류: {e}")
        except Exception as e:
            print(f"채널 처리 중 오류: {e}")

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())