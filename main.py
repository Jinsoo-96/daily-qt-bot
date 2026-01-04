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

        # 1. 날짜 추출
        date_el = soup.select_one('.date li:nth-child(2)')
        date = date_el.get_text(strip=True) if date_el else "0000.00.00"

        # 2. 제목 및 성경 범위 추출
        qt_header = soup.select_one('.font-size h1')
        bible_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', ' ')
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')

        # 3. 본문 내용 추출 (디스코드 마크다운 적용)
        bible_div = soup.select_one('.bible')
        content_parts = []
        
        # 제목과 범위를 맨 위에 배치
        content_parts.append(f"# {qt_title}")  # 가장 큰 제목
        content_parts.append(f"> **{bible_range}**\n") # 인용구 + 굵게

        elements = bible_div.find_all(['p', 'table'])
        for el in elements:
            if el.name == 'p' and 'title' in el.get('class', []):
                # 소제목 (중간 크기 헤더)
                subtitle = el.get_text(strip=True)
                content_parts.append(f"## 📌 {subtitle}")
            elif el.name == 'table':
                # 절 번호는 굵게, 내용은 일반 텍스트
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)
                content_parts.append(f"**{num}** {txt}")

        # 전체 텍스트 합치기
        full_markdown = "\n".join(content_parts)

        # ==========================================
        # [검증용] 디스코드 마크다운 미리보기 파일 생성
        # ==========================================
        debug_filename = "debug_qt_preview.txt"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(f"--- DISCORD PREVIEW ({date}) ---\n\n")
            f.write(full_markdown)
            f.write("\n\n------------------------------")
        
        print(f"✅ 마크다운 미리보기 파일 생성 완료: {os.path.abspath(debug_filename)}")
        # ==========================================

        # 실제 디스코드 전송용 데이터
        payload = {
            "embeds": [{
                "title": f"📖 오늘의 QT ({date})",
                "description": full_markdown, # 마크다운이 포함된 본문
                "color": 5814783,
                "footer": {
                    "text": "출처: 두란노 생명의 삶",
                    "icon_url": "https://www.duranno.com/favicon.ico"
                }
            }]
        }
        return payload

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

# 실행부
webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
payload = get_qt()

if webhook_url and payload:
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 204:
        print("🚀 디스코드 전송 성공!")
    else:
        print(f"⚠️ 전송 실패: {response.status_code}")
elif not webhook_url:
    print("📢 웹후크 URL이 없어 파일만 생성되었습니다. 내용을 확인해보세요!")