# server/scheduler/daily_reporter.py

import os
import sys
import json
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv

# 프로젝트 루트 경로 설정
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 프로젝트 모듈 import
from src.data_collection.news_api import NewsAPIClient
from src.data_collection.yahoo_finance import YahooFinance
from src.data_collection.cnn_fear_greed import CNNFearGreedIndex
from src.data_processing.market_data_visualization import MarketVisualizer
from server.components.summerize.webloader import getRagResponse_LLAMA

class DailyMarketReporter:
    """일일 시장 데이터 수집 및 리포팅 클래스"""
    
    def __init__(self):
        """
        초기화
        - 환경 변수 로드
        - 로깅 설정
        - 데이터 수집기 초기화
        """
        # 환경 변수 로드
        load_dotenv(os.path.join(project_root, '.env'))
        
        # 로그 디렉토리 설정
        self.log_dir = os.path.join(project_root, 'logs', 'scheduler')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # API 키 설정
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.kakao_token = os.getenv('KAKAO_ACCESS_TOKEN')
        
        # 데이터 수집기 초기화
        self.initialize_collectors()
        
        self.logger.info("DailyMarketReporter 초기화 완료")

    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger('DailyMarketReporter')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러
        log_file = os.path.join(
            self.log_dir, 
            f'market_report_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def initialize_collectors(self):
        """데이터 수집기 초기화"""
        try:
            self.news_collector = NewsAPIClient(self.news_api_key)
            self.market_collector = YahooFinance()
            self.fear_greed_collector = CNNFearGreedIndex()
            self.visualizer = MarketVisualizer()
            self.logger.info("데이터 수집기 초기화 완료")
        except Exception as e:
            self.logger.error(f"데이터 수집기 초기화 실패: {str(e)}")
            raise

    def collect_market_data(self):
        """시장 데이터 수집"""
        try:
            self.logger.info("시장 데이터 수집 시작")
            
            # 주식 시장 데이터
            market_data = self.market_collector.get_market_summary()
            self.logger.info("주식 시장 데이터 수집 완료")
            
            # Fear & Greed 지수
            fear_greed = self.fear_greed_collector.get_fear_greed_data()
            self.logger.info("Fear & Greed 지수 수집 완료")
            
            return market_data, fear_greed
            
        except Exception as e:
            self.logger.error(f"시장 데이터 수집 실패: {str(e)}")
            return None, None

    def collect_news_data(self):
        """뉴스 데이터 수집"""
        try:
            self.logger.info("뉴스 데이터 수집 시작")
            news_data = self.news_collector.collect_news()
            self.logger.info(f"뉴스 데이터 수집 완료: {len(news_data['articles'])}개 기사")
            return news_data
        except Exception as e:
            self.logger.error(f"뉴스 데이터 수집 실패: {str(e)}")
            return None

    def generate_market_visuals(self):
        """시장 데이터 시각화"""
        try:
            self.logger.info("시각화 생성 시작")
            visuals = self.visualizer.generate_market_report()
            self.logger.info("시각화 생성 완료")
            return visuals
        except Exception as e:
            self.logger.error(f"시각화 생성 실패: {str(e)}")
            return None

    def create_llm_summary(self, news_data):
        """LLM을 사용한 뉴스 요약 생성"""
        try:
            self.logger.info("LLM 뉴스 요약 시작")
            news_texts = [
                f"{article['title']}: {article['summary']}" 
                for article in news_data['articles'][:5]
            ]
            news_context = "\n".join(news_texts)
            
            prompt = (
                "다음 뉴스들의 핵심 내용을 3-4줄로 요약해주세요. "
                "각 뉴스의 중요도를 고려하여 투자자 관점에서 중요한 내용을 중심으로 요약해주세요:\n\n"
                f"{news_context}"
            )
            
            summary = getRagResponse_LLAMA(prompt)
            self.logger.info("LLM 뉴스 요약 완료")
            return summary
            
        except Exception as e:
            self.logger.error(f"LLM 요약 생성 실패: {str(e)}")
            return None

    def format_daily_report(self, market_data, fear_greed, news_summary):
        """일일 리포트 포맷팅"""
        try:
            report = []
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 헤더
            report.append(f"📊 일일 시장 리포트 ({current_time})")
            report.append("\n💹 주요 지수 동향")
            
            # 주요 지수
            indices = {
                '^GSPC': 'S&P 500', 
                '^DJI': 'Dow Jones', 
                '^IXIC': 'NASDAQ'
            }
            for symbol, name in indices.items():
                if symbol in market_data:
                    data = market_data[symbol]
                    report.append(
                        f"• {name}: {data['formatted_price']} ({data['change_percent']:+.2f}%)"
                    )
            
            # Fear & Greed 지수
            if fear_greed:
                report.append("\n🎯 투자 심리 지표")
                report.append(f"• Fear & Greed 지수: {fear_greed['value']}")
                
                # 지수 해석 추가
                value = float(fear_greed['value'])
                if value <= 25:
                    mood = "극도의 공포"
                elif value <= 45:
                    mood = "공포"
                elif value <= 55:
                    mood = "중립"
                elif value <= 75:
                    mood = "탐욕"
                else:
                    mood = "극도의 탐욕"
                report.append(f"• 현재 시장 심리: {mood}")
            
            # 뉴스 요약
            if news_summary:
                report.append("\n📰 주요 뉴스 요약")
                report.append(news_summary)
            
            # 푸터
            report.append("\n\n💡 투자 유의사항")
            report.append("- 본 리포트는 투자 참고 자료일 뿐, 투자 권유가 아닙니다")
            report.append("- 투자 결정은 본인의 판단과 책임하에 신중히 이루어져야 합니다")
            
            return "\n".join(report)
            
        except Exception as e:
            self.logger.error(f"리포트 포맷팅 실패: {str(e)}")
            return "리포트 생성 중 오류가 발생했습니다."

    def send_kakao_message(self, message):
        """카카오톡 메시지 발송"""
        try:
            self.logger.info("카카오톡 메시지 발송 시작")
            
            url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
            headers = {
                'Authorization': f'Bearer {self.kakao_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # 메시지 길이 제한 처리
            if len(message) > 4000:
                message = message[:3800] + "...\n[메시지가 너무 길어 일부 생략되었습니다]"
            
            template_object = {
                'object_type': 'text',
                'text': message,
                'link': {
                    'web_url': 'https://finance.yahoo.com',
                    'mobile_web_url': 'https://finance.yahoo.com'
                }
            }
            
            data = {
                'template_object': json.dumps(template_object)
            }
            
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code == 200:
                self.logger.info("카카오톡 메시지 발송 성공")
            else:
                self.logger.error(f"카카오톡 메시지 발송 실패: {response.text}")
                
        except Exception as e:
            self.logger.error(f"카카오톡 메시지 발송 오류: {str(e)}")

    def run_daily_report(self):
        """일일 리포트 실행"""
        try:
            self.logger.info("일일 리포트 생성 시작")
            
            # 1. 데이터 수집
            market_data, fear_greed = self.collect_market_data()
            news_data = self.collect_news_data()
            
            if not market_data or not news_data:
                raise Exception("필수 데이터 수집 실패")
            
            # 2. 시각화 생성
            self.generate_market_visuals()
            
            # 3. LLM 뉴스 요약
            news_summary = self.create_llm_summary(news_data)
            
            # 4. 리포트 포맷팅
            report = self.format_daily_report(market_data, fear_greed, news_summary)
            
            # 5. 카카오톡 발송
            self.send_kakao_message(report)
            
            self.logger.info("일일 리포트 생성 및 발송 완료")
            
        except Exception as e:
            error_msg = f"일일 리포트 생성 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            # 오류 발생 시 관리자에게 알림
            self.send_kakao_message(f"⚠️ 시스템 오류 발생\n{error_msg}")

def main():
    """메인 실행 함수"""
    try:
        reporter = DailyMarketReporter()
        reporter.run_daily_report()
    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()