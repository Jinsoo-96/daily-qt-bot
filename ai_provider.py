from google import genai  # 라이브러리 이름이 'google-genai'이지만 import는 'google.genai' 혹은 'google'에서 합니다.
from google.genai import types
import os
import time

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_reflection(bible_title, bible_range, content_body):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
당신은 두 역할을 동시에 수행합니다.

1) 성경 중심의 기독교 세계관 위에서,
   복음주의 신학 전통에 기반한 뛰어난 성서신학자
2) 따뜻하고 문학적인 묵상 에세이를 쓰는 작가

아래에 제공된 [성경 본문]을 기반으로
오늘 하루를 위한 큐티 묵상 글을 작성하십시오.

[작성 규칙]
- 전체 분량은 공백 포함 2000자 이내로 작성한다
- 한국어로 작성한다
- 과도한 설교체나 교훈적 표현은 피하고, 차분하고 따뜻한 톤을 유지한다
- 신학적 해설과 묵상 에세이가 자연스럽게 하나의 흐름으로 이어지도록 한다
- 본문에 없는 내용을 단정적으로 추가하지 않는다
- 독자의 일상과 연결되는 묵상적 적용을 포함한다
- 20~30대 신앙인이 겪는 현실적인 고민(진로, 관계, 불안, 반복되는 일상 등)을 은근히 반영한다
- 독자를 다그치거나 평가하지 않는다
- 디스코드에서 사용할 수 있는 마크다운 형식으로 가독성 좋게 작성한다.

[구성]
1. **본문 해설**
   - 본문의 역사적·문맥적 의미를 간결하고 깊이 있게 설명한다
   - 핵심 신학 주제를 명확히 드러낸다

2. **묵상 에세이**
   - 오늘을 살아가는 신앙인의 마음에 말을 건네는 문체로 작성한다
   - 설명보다 묵상의 흐름을 우선한다

3. **하루를 위한 묵상 질문 3가지**
   - 정답을 요구하지 않는 질문
   - 자기 성찰과 기도로 이어질 수 있도록 구성한다
   - 번호를 붙여 제시한다

[성경 제목: {bible_title} {bible_range}]
[성경 본문]
{content_body}
"""
    max_retries = 3  # 최대 3번 시도
    retry_delay = 2  # 실패 시 2초 대기 후 다시 시도
    # 안전 설정: 성경 본문 분석 중 차단되는 일을 방지합니다.
    # 2. 안전 설정 (확실한 최신 문법입니다)
    # 성경 본문의 특정 단어가 차단되는 것을 방지하기 위해 BLOCK_NONE으로 설정합니다.
    config = types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
        ]
    )
    
    for attempt in range(max_retries):
        try:
            print(f"🤖 AI 응답 생성 중... (시도 {attempt + 1}/{max_retries})")
            # 3. 콘텐츠 생성 (최신 문법: client.models.generate_content)
            response = client.models.generate_content(
                model='gemini-3-flash',
                contents=prompt,
                config=config)
            
            # 응답이 성공적으로 왔고 텍스트가 있는 경우
            if response and response.text:
                return response.text
            
            # 응답은 왔으나 텍스트가 없는 경우 (Safety Filter 작동 등)
            else:
                print("⚠️ AI 응답이 비어있습니다. 다시 시도합니다.")
                
        except Exception as e:
            print(f"❌ 시도 {attempt + 1} 실패: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay) # 잠시 대기 후 다음 루프 진행
            else:
                # 모든 시도가 실패했을 때 보낼 메시지
                return "🙏 현재 AI가 묵상을 준비하는 데 어려움을 겪고 있습니다. 잠시 후 다시 확인해 주세요."

    return "🙏 묵상 내용을 생성할 수 없습니다."
