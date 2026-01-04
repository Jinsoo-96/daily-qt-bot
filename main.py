import requests
from bs4 import BeautifulSoup
import os

def get_qt():
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 1. 날짜 추출 (포스트 제목용)
        date_el = soup.select_one('.date li:nth-child(2)')
        date_title = date_el.get_text(strip=True) if date_el else "오늘의 QT"

        # 2. 제목 및 성경 범위 추출
        qt_header = soup.select_one('.font-size h1')
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')

        # 3. 본문 내용 마크다운 구성
        bible_div = soup.select_one('.bible')
        content_parts = []
        
        # 본문 상단에 큰 제목과 범위 강조
        content_parts.append(f"# {qt_title}") 
        content_parts.append(f"> **{bible_range}**\n")

        elements = bible_div.find_all(['p', 'table'])
        for el in elements:
            if el.name == 'p' and 'title' in el.get('class', []):
                # 소제목 (📌 아이콘과 함께 강조)
                subtitle = el.get_text(strip=True)
                content_parts.append(f"### 📌 {subtitle}")
            elif el.name == 'table':
                # 절 번호는 굵게, 말씀은 일반 텍스트
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                content_parts.append(f"**{num}** {txt}")

        full_markdown = "\n".join(content_parts)

        # 4. 디스코드 전송 데이터 (포스트 형식)
        payload = {
            # 일반 채널일 경우 제목처럼 보이게 함
            "content": f"## 📅 {date_title} 새 포스트", 
            "embeds": [{
                "title": f"{date_title} 말씀 묵상",
                "description": full_markdown,
                "color": 5763719, # 청년부 느낌의 녹색 계열 (성장)
                "footer": {
                    "text": "출처: 두란노 생명의 삶",
                    "icon_url": "https://www.duranno.com/favicon.ico"
                }
            }]
        }
        
        # 만약 포럼 채널을 사용한다면 포스트 제목을 날짜로 설정
        # (웹후크가 포럼용일 경우 아래 thread_name이 제목이 됩니다)
        payload["thread_name"] = f"[{date_title}] {qt_title}"
        
        return payload

    except Exception as e:
        print(f"오류 발생: {e}")
        return None

# 전송 로직
webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
if webhook_url:
    payload = get_qt()
    if payload:
        # 디스코드 전송
        response = requests.post(webhook_url, json=payload)
        if response.status_code in [200, 204]:
            print(f"✅ 성공: {payload['thread_name']} 게시 완료")
        else:
            print(f"❌ 실패: {response.status_code}")