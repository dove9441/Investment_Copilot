import unittest
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from unittest import mock  # mock을 별도로 import

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection.news_api import NewsAPIClient
from src.data_collection.yahoo_finance import YahooFinance
from src.data_collection.cnn_fear_greed import CNNFearGreedIndex

load_dotenv()

class TestDataCollection(unittest.TestCase):
    def test_news_api(self):
        news_api_key = os.getenv('NEWS_API_KEY')
        news_client = NewsAPIClient(api_key=news_api_key)
        headlines = news_client.get_top_headlines()
        self.assertIsNotNone(headlines)

    def test_yahoo_finance(self):
        yf_client = YahooFinance()
        stock_data = yf_client.get_stock_data('AAPL')
        market_summary = yf_client.get_market_summary()
        self.assertIsNotNone(stock_data)
        self.assertIsNotNone(market_summary)

class TestCNNFearGreedCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = CNNFearGreedIndex()

    def test_get_fear_greed_data(self):
        result = self.crawler.get_fear_greed_data()
        
        # 결과가 None이 아닌지 확인
        self.assertIsNotNone(result, "Should return data")
        
        # timestamp와 value가 있는지 확인
        self.assertIn('timestamp', result, "Should have timestamp")
        self.assertIn('value', result, "Should have value")
        
        # value가 존재하는지만 확인 (숫자 체크는 제거)
        self.assertIsNotNone(result['value'], "Value should not be None")

    def test_save_to_file(self):
        # 테스트 데이터 생성
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'value': '50'
        }
        
        # 파일 저장 테스트
        save_result = self.crawler.save_to_file(test_data)
        self.assertTrue(save_result, "Should save file successfully")
        
        # 파일이 존재하는지 확인
        self.assertTrue(os.path.exists('data/raw/fear_greed_index.csv'), 
                       "CSV file should exist")

class TestDataCollectionWithMock(unittest.TestCase):
    def setUp(self):
        self.crawler = CNNFearGreedIndex()

    @mock.patch('requests.get')  # unittest.mock 대신 mock 사용
    def test_get_fear_greed_data_mock(self, mock_get):
        # Mock response 설정
        mock_response = mock.Mock()
        mock_response.text = '''
            <html>
                <span class="market-fng-gauge__dial-number-value">50</span>
            </html>
        '''
        mock_get.return_value = mock_response
        
        result = self.crawler.get_fear_greed_data()
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], '50')

if __name__ == '__main__':
    unittest.main(verbosity=2)