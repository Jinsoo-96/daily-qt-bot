import requests
from bs4 import BeautifulSoup
import re

def get_qt_data():
    url = "https://www.duranno.com/qt/view/bible.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        date = soup.select_one('.date li:nth-child(2)').get_text(strip=True) if soup.select_one('.date li:nth-child(2)') else "0000.00.00"
        
        qt_header = soup.select_one('.font-size h1')
        raw_range = qt_header.select_one('span').get_text(strip=True).replace('\xa0', '').replace(' ', '')
        bible_range = re.sub(r'(\d)', r'  \1', raw_range, count=1)
        qt_title = qt_header.select_one('em').get_text(strip=True).replace('\xa0', ' ')
        
        bible_div = soup.select_one('.bible')
        content_parts = [
            "⠀", # 특수 투명 문자
            f"## {qt_title}",
            "⠀",
        ]
        
        for el in bible_div.find_all(['p', 'table']):
            if el.name == 'p' and 'title' in el.get('class', []):
                content_parts.append(f"\n### {el.get_text(strip=True)}")
            elif el.name == 'table':
                num = el.find('th').get_text(strip=True)
                txt = el.find('td').get_text(strip=True)

                # [최종 수정] 1절이면서, 앞에 이미 다른 내용(절)이 기록되어 있을 때만 빈 줄 추가
                # 이렇게 하면 첫 구절이 1절일 때는 빈 줄이 생기지 않습니다.
                if num == '1' and len(content_parts) > 3: # 기본 헤더(제목 등) 개수보다 많을 때
                    content_parts.append("")

                content_parts.append(f"{num}. {txt}")
                
        footer = f"\n\n\n**💡 오늘도 주님의 말씀으로 승리하는 하루가 됩시다!**\n\n@everyone  [_]({url})"
        main_body = "\n".join(content_parts)
        
        max_body_length = 1980 - len(footer)
        if len(main_body) > max_body_length:
            main_body = main_body[:max_body_length - 35] + "\n\n...(본문이 길어 생략되었습니다)"
        
        full_content = main_body + footer
        # [수정] AI 해설용으로 쓸 'main_body'를 추가로 반환합니다.
        return date, qt_title, bible_range, full_content, main_body
        
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return None, None, None, None