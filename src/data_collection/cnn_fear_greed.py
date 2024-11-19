import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import logging

class CNNFearGreedIndex:
    def __init__(self):
        self.url = 'https://edition.cnn.com/markets/fear-and-greed'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_fear_greed_data(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 숫자를 포함하는 span 요소 찾기
            fear_greed_value = soup.find('span', class_='market-fng-gauge__dial-number-value')
            
            if fear_greed_value:
                value = fear_greed_value.text.strip()
                return {
                    'timestamp': datetime.now().isoformat(),
                    'value': value
                }
            else:
                logging.error("Could not find fear and greed value")
                return None

        except requests.RequestException as e:
            logging.error(f"Error fetching CNN Fear & Greed Index: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None

    def save_to_file(self, data):
        try:
            if not data:
                return False
                
            # data/raw 디렉토리 생성
            os.makedirs('data/raw', exist_ok=True)
            file_path = 'data/raw/fear_greed_index.csv'
            
            # 파일이 없으면 헤더 추가
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('timestamp,value\n')
            
            # 데이터 추가
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{data['timestamp']},{data['value']}\n")
            
            return True

        except Exception as e:
            logging.error(f"Error saving data: {e}")
            return False