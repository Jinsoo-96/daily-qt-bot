import discord
import asyncio
import datetime

# 1. 큐티 포스트
async def post_daily_qt(channel, date, bible_range, content, ai_reflection):
    # 1. 기존 고정된 스레드 해제
    active_threads = await channel.guild.active_threads()
    for thread in active_threads:
        if thread.parent_id == channel.id and thread.flags.pinned:
            await thread.edit(pinned=False)
            break

    # 2. 새 포럼 포스트(스레드) 생성
    new_post = await channel.create_thread(name=f"{date} - {bible_range}", content=content)
    target_thread = new_post.thread
    await asyncio.sleep(2)

    # 3. AI 해설 전송 로직 (문단 단위 분할)
    MAX_LEN = 1900
    ai_header = "✨ **AI 말씀 해설 & 묵상 에세이**\n\n"
    
    # 내부 전송용 함수
    async def send_chunk(text):
        if text.strip():
            await target_thread.send(content=text)
            await asyncio.sleep(2)

    # 1. 헤더와 내용을 하나로 합침
    full_text = ai_header + ai_reflection

    # 2. 전체 길이가 짧으면 그냥 한 번에 보냄
    if len(full_text) <= MAX_LEN:
        await send_chunk(full_text)
    else:
        # ---------------------------------------------------------
        # [전략 1] '### 묵상 에세이:' 제목을 기준으로 이등분 시도
        # ---------------------------------------------------------
        split_keyword = "### 묵상 에세이:"
        
        if split_keyword in full_text:
            # 키워드 기준으로 앞(해설)과 뒤(에세이)를 나눔
            parts = full_text.split(split_keyword, 1)
            first_part = parts[0].strip()
            second_part = (split_keyword + parts[1]).strip()
            
            # 나눈 두 파트가 각각 1900자 이내라면, 이대로 전송하고 종료
            if len(first_part) <= MAX_LEN and len(second_part) <= MAX_LEN:
                await send_chunk(first_part)
                await send_chunk(second_part)
                print("✅ 전략 1(키워드 분할)로 전송 성공")
                return
            
        # ---------------------------------------------------------
        # [전략 2] 전략 1이 실패한 경우 (에세이가 너무 길거나 키워드 없음)
        # 안전 모드: 인용구(>) 서식을 유지하며 문단 분할
        # ---------------------------------------------------------
        print("⚠️ 전략 2(문단 분할) 시작")
        paragraphs = full_text.split("\n\n")
        buffer = ""

        for para in paragraphs:
            para = para.strip()
            if not para: continue

            # 문단 하나 자체가 1900자를 넘는 경우 (강제 분할)
            if len(para) > MAX_LEN:
                if buffer:
                    await send_chunk(buffer)
                    buffer = ""
                
                # 인용문인지 확인
                is_quote = para.startswith(">")
                
                # 1500자 단위로 자르면서, 잘린 뒷부분에 > 붙여주기
                for i in range(0, len(para), 1500):
                    chunk = para[i:i+1500]
                    # 인용문인데 잘린 뒷부분에 > 가 없다면 붙여줌
                    if is_quote and not chunk.startswith(">"):
                        chunk = "> " + chunk
                    await send_chunk(chunk)
                continue

            # 일반적인 문단 처리
            if len(buffer) + len(para) + 2 > MAX_LEN:
                await send_chunk(buffer)
                # 버퍼를 새로 시작할 때, 현재 문단이 인용문이면 서식 유지 확인 (이미 para에 포함되어 있음)
                buffer = para + "\n\n"
            else:
                buffer += para + "\n\n"

        if buffer:
            await send_chunk(buffer)

    print(f"✅ {date} 큐티 본문 고정 및 AI 해설 전송 완료")

    # 4. 포스트 및 메시지 핀 고정 (가장 마지막에 실행)
    await target_thread.edit(pinned=True)
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
        question="참여 가능인원 확인 \n\n- 금요일 오후 8시까지 투표해주시고, 변경사항이 있으신 분은 개인연락 부탁드려요. \n- 혹시 차량 필요하신 분 미리 남겨두면 좋을 것 같아요.",
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
        result = await channel.create_thread(
            name=f"{today_date_str} 모임",
            content=f"🗓️ **{today_date_str} 주일 모임**"
        )
        target_thread = result.thread 
        await asyncio.sleep(2)

    # 3. 임베드 전송
    try:
        embed = discord.Embed(
            title="📢 오늘 모임 정리 및 나눔",
            description="오늘 모임의 내용을 아래 양식에 맞춰 한 줄 정도로 정리해 주세요!",
            color=discord.Color.blue()
        )
        embed.add_field(name="📝 작성 내용", value="• 오늘 모임 인원수(+ 누구누구 왔는지)\n• 장소\n• 간략한 나눔 내용 (한 줄)", inline=False)
        # 푸터의 @everyone은 알림 기능은 없지만, 누가 대상인지 보여주는 용도로 둡니다.
        embed.set_footer(text="함께 나눌 수 있어 감사합니다. ✨")
        
        # [핵심 수정] content="@everyone"을 추가하여 실제 알림이 울리게 합니다.
        await target_thread.send(content="@everyone", embed=embed)
        print(f"✅ {today_date_str} 포스트에 나눔 공지 완료")
            
    except Exception as e:
        print(f"❌ 임베드 전송 중 오류 발생: {e}")