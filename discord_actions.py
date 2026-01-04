import discord
import asyncio
import datetime

# 1. 큐티 포스트
async def post_daily_qt(channel, date, bible_range, content):
    active_threads = await channel.guild.active_threads()
    for thread in active_threads:
        if thread.parent_id == channel.id and thread.flags.pinned:
            await thread.edit(pinned=False); break
    new_post = await channel.create_thread(name=f"{date} - {bible_range}", content=content)
    await asyncio.sleep(2)
    await new_post.thread.edit(pinned=True)
    await new_post.message.pin()

# 2. 월요일: 차주 주일 모임 포스트 & 투표 생성
async def create_sunday_gathering_post(channel, sunday_date_str):
    # 포스트 생성
    result = await channel.create_thread(
        name=f"{sunday_date_str} 모임",
        content=f"🗓️ **{sunday_date_str} 주일 모임 안내**\n이번 주 모임 참석 여부를 확인해 주세요!\n@everyone"
    )
    
    # [중요] result에서 진짜 스레드 객체를 꺼냅니다.
    target_thread = result.thread
    
    # 안정화를 위해 2초 대기
    await asyncio.sleep(2)
    
    # 투표 생성
    poll = discord.Poll(
        question="**참여 가능인원 확인* \n\n- **금요일 오후 8시까지 투표해주시고, 변경사항이 있으신 분은 개인연락 부탁드려요. \n- 혹시 차량 필요하신 분 미리 남겨두면 좋을 것 같아요.",
        duration=datetime.timedelta(hours=107)
    )
    poll.add_answer(text="가능", emoji="✅")
    poll.add_answer(text="불가능", emoji="❌")
    poll.add_answer(text="미정(개인 연락하겠습니다)", emoji="💬")

    # 꺼내온 스레드 객체(target_thread)에 투표 전송
    await target_thread.send(poll=poll)
    print(f"✅ {sunday_date_str} 포스트 생성 및 투표 전송 완료")

# 3. 일요일: 오늘 모임 포스트 추적 및 임베드 전송
async def send_sunday_summary_embed(channel, today_date_str):
    target_thread = None
    
    # 1. 기존 포스트 찾기
    async for thread in channel.archived_threads(limit=20):
        if today_date_str in thread.name and "모임" in thread.name:
            target_thread = thread; break
    if not target_thread:
        for thread in channel.threads:
            if today_date_str in thread.name and "모임" in thread.name:
                target_thread = thread; break

    # 2. 포스트를 못 찾았다면? 새로 생성
    if not target_thread:
        print(f"⚠️ {today_date_str} 포스트를 찾지 못해 새로 생성합니다.")
        
        # [수정 포인트] .thread 를 붙여서 실제 스레드 객체를 가져와야 합니다.
        result = await channel.create_thread(
            name=f"{today_date_str} 모임",
            content=f"🗓️ **{today_date_str} 주일 모임** (자동 생성됨)"
        )
        target_thread = result.thread # 여기서 진짜 방(Thread)을 꺼냅니다.
        
        await asyncio.sleep(2)

    # 3. 임베드 전송
    try:
        embed = discord.Embed(
            title="📢 오늘 모임 정리 및 나눔",
            description="오늘 모임의 내용을 아래 양식에 맞춰 한 줄 정도로 정리해 주세요!",
            color=discord.Color.blue()
        )
        embed.add_field(name="📝 작성 내용", value="• 오늘 모임 인원수\n• 장소\n• 간략한 나눔 내용 (한 줄)", inline=False)
        embed.set_footer(text="함께 나눌 수 있어 감사합니다. ✨ @everyone")
        
        # 이제 .send 가 정상 작동합니다.
        await target_thread.send(embed=embed)
        print(f"✅ {today_date_str} 포스트에 나눔 공지 완료")
            
    except Exception as e:
        print(f"❌ 임베드 전송 중 오류 발생: {e}")