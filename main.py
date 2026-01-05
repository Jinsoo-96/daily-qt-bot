import discord
import os
import asyncio
import datetime
import argparse
import sys
from qt_provider import get_qt_data
from discord_actions import post_daily_qt, create_sunday_gathering_post, send_sunday_summary_embed
from ai_provider import get_ai_reflection

async def run_bot():
    # 1. 인자값 파싱
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()

    # 2. 환경 변수 로드
    token = os.environ.get('DISCORD_BOT_TOKEN')
    qt_channel_id = os.environ.get('QT_CHANNEL_ID')
    sunday_channel_id = os.environ.get('SUNDAY_CHANNEL_ID')

    # 필수 변수 확인
    if not all([token, qt_channel_id, sunday_channel_id]):
        print("❌ 필수 환경 변수가 설정되지 않았습니다.")
        return

    # 3. 디스코드 클라이언트 설정
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'✅ {client.user} 로그인 성공 (모드: {args.mode})')
        
        try:
            # 한국 시간 기준 (KST) 설정
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
            weekday = now.weekday()
            
            # --- 큐티 모드 ---
            if args.mode == 'qt':
                print("📖 큐티 포스팅을 시작합니다...")

                # 1. 큐티 데이터 가져오기
                channel = await client.fetch_channel(int(qt_channel_id))
                date, title, bible_range, content = get_qt_data()

                # 2. Gemini AI 해설 생성하기
                ai_commentary = get_ai_reflection(title, bible_range, content)
                if content and ai_commentary:
                    await post_daily_qt(channel, date, bible_range, content, ai_commentary)
                    print(f"✅ {date} 큐티 포스팅 완료")

            
            # --- 주간 태스크 모드 (월/일) ---
            elif args.mode == 'task':
                channel = await client.fetch_channel(int(sunday_channel_id))
                
                if weekday == 0:  # 월요일: 새 포스트 및 투표 생성
                    print("🗓️ 차주 주일 모임 포스트 생성을 시작합니다...")
                    sunday = now + datetime.timedelta(days=6)
                    sunday_str = sunday.strftime("%Y.%m.%d")
                    await create_sunday_gathering_post(channel, sunday_str)
                    print(f"✅ {sunday_str} 모임 포스트 생성 완료")
                    
                elif weekday == 6:  # 일요일: 오늘 포스트 추적 및 나눔 임베드
                    print("📢 오늘 모임 포스트 추적 및 나눔 공지를 시작합니다...")
                    today_str = now.strftime("%Y.%m.%d")
                    await send_sunday_summary_embed(channel, today_str)
                    print(f"✅ {today_str} 나눔 공지 완료")
                else:
                    print(f"ℹ️ 오늘은 {weekday}번째 요일로, 설정된 작업이 없습니다.")

        except Exception as e:
            print(f"❌ 작업 중 오류 발생: {e}")
        
        finally:
            # 작업이 끝나면 봇을 안전하게 종료 (Unclosed connector 방지)
            print("👋 작업을 마치고 봇을 종료합니다.")
            await client.close()

    # 4. 봇 실행
    try:
        await client.start(token)
    except Exception as e:
        print(f"❌ 봇 연결 실패: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass