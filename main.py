import discord
import os
import asyncio
import datetime
import argparse
from qt_provider import get_qt_data
from discord_actions import post_daily_qt, create_sunday_gathering_post, send_sunday_summary_embed

async def run_bot():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()

    token = os.environ.get('DISCORD_BOT_TOKEN')
    qt_channel_id = int(os.environ.get('QT_CHANNEL_ID'))
    sunday_channel_id = int(os.environ.get('SUNDAY_CHANNEL_ID'))
    
    intents = discord.Intents.default()
    intents.message_content = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        # 한국 시간 기준 (KST)
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        weekday = now.weekday()
        
        if args.mode == 'qt':
            channel = await client.fetch_channel(qt_channel_id)
            date, title, bible_range, content = get_qt_data()
            if content: await post_daily_qt(channel, date, bible_range, content)
            
        elif args.mode == 'task':
            channel = await client.fetch_channel(sunday_channel_id)
            
            if weekday == 0: # 월요일 오전 9시 실행 가정
                # 6일 뒤 일요일 날짜 계산
                sunday = now + datetime.timedelta(days=6)
                await create_sunday_gathering_post(channel, sunday.strftime("%Y.%m.%d"))
                
            elif weekday == 6: # 일요일 12시 30분 실행 가정
                # 오늘 날짜로 포스트 추적
                await send_sunday_summary_embed(channel, now.strftime("%Y.%m.%d"))

        await client.close()

    await client.start(token)

if __name__ == "__main__":
    asyncio.run(run_bot())