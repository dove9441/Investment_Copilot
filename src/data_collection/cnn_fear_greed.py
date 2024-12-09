# cnn_fear_greed.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import logging
import json

class CNNFearGreedIndex:
    def __init__(self):
        """초기화 함수 - 기본 설정 및 URL 정의"""
        # 실제 Fear & Greed 데이터가 있는 URL
        self.url = 'https://production.dataviz.cnn.io/index/fearandgreed/current'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.cnn.com/'
        }
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        print("CNNFearGreedIndex 초기화 완료")

    def get_fear_greed_data(self):
        """Fear & Greed 지수 데이터 수집"""
        try:
            print("데이터 수집 시작...")
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            print("데이터 응답 내용:", data)  # 응답 내용 확인
            
            if isinstance(data, dict) and 'score' in data:
                score = float(data['score'])
                print(f"수집된 Fear & Greed 지수: {score}")
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'value': score
                }
                
            elif isinstance(data, dict) and 'fear_and_greed' in data:
                score = float(data['fear_and_greed'].get('score', 0))
                print(f"수집된 Fear & Greed 지수: {score}")
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'value': score
                }
                
            else:
                print("예상된 데이터 형식이 아닙니다:", data)
                return None

        except requests.RequestException as e:
            print(f"네트워크 요청 오류: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            self.logger.error(f"원본 응답: {response.text}")
            return None
        except Exception as e:
            print(f"예상치 못한 오류 발생: {e}")
            return None

    def save_to_file(self, data):
        """수집된 데이터를 CSV 파일로 저장"""
        try:
            if not data:
                print("저장할 데이터가 없습니다")
                return False
                
            # data/raw 디렉토리 생성
            os.makedirs('data/raw', exist_ok=True)
            file_path = 'data/raw/fear_greed_index.csv'
            
            print(f"데이터 저장 시작: {file_path}")
            
            # 파일이 없으면 헤더 추가
            file_exists = os.path.exists(file_path)
            mode = 'a' if file_exists else 'w'
            
            with open(file_path, mode, encoding='utf-8') as f:
                if not file_exists:
                    f.write('timestamp,value\n')
                f.write(f"{data['timestamp']},{data['value']}\n")
            
            print(f"데이터 저장 완료: ({data['value']})")
            return True

        except Exception as e:
            print(f"데이터 저장 중 오류 발생: {e}")
            return False

    def backup_scrape_method(self):
        """대체 스크래핑 방법 - 메인 방법 실패시 사용"""
        try:
            print("대체 방법으로 데이터 수집 시도...")
            response = requests.get(
                'https://edition.cnn.com/markets/fear-and-greed',
                headers=self.headers
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            fear_greed_div = soup.find('div', {'class': 'market-fng-gauge__dial-number-value'})
            
            if fear_greed_div and fear_greed_div.text.strip():
                value = float(fear_greed_div.text.strip())
                print(f"대체 방법으로 수집된 지수: {value}")
                return {
                    'timestamp': datetime.now().isoformat(),
                    'value': value
                }
            return None
            
        except Exception as e:
            print(f"대체 수집 방법 실패: {e}")
            return None


def main():
    """메인 실행 함수"""
    print("=== CNN Fear & Greed Index 수집 시작 ===")
    
    collector = CNNFearGreedIndex()
    
    # 첫 번째 방법으로 시도
    data = collector.get_fear_greed_data()
    
    # 첫 번째 방법 실패시 대체 방법 시도
    if not data:
        print("기본 방법 실패, 대체 방법 시도...")
        data = collector.backup_scrape_method()
    
    # 데이터 저장
    if data:
        success = collector.save_to_file(data)
        if success:
            print(f"Fear & Greed 지수 ({data['value']}) 저장 완료")
        else:
            print("데이터 저장 실패")
    else:
        print("모든 수집 방법 실패")

if __name__ == "__main__":
    main()