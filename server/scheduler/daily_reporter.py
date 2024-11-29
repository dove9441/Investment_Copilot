import os
import sys
import json
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, List, Optional, Tuple

# 프로젝트 루트 경로 설정
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 프로젝트 모듈 import
from src.data_collection.news_api import NewsAPIClient
from src.data_collection.yahoo_finance import YahooFinance
from src.data_collection.cnn_fear_greed import CNNFearGreedIndex
from src.data_processing.market_data_visualization import MarketVisualizer
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class DailyMarketReporter:
    """일일 시장 데이터 수집 및 리포팅 클래스"""
    
    def __init__(self):
        """초기화 함수"""
        self._initialize_environment()
        self._setup_logging()
        self._initialize_collectors()
        self.logger.info("DailyMarketReporter 초기화 완료")

    def _initialize_environment(self):
        """환경 변수 및 디렉토리 초기화"""
        load_dotenv(os.path.join(project_root, '.env'))
        self.log_dir = os.path.join(project_root, 'logs', 'scheduler')
        os.makedirs(self.log_dir, exist_ok=True)
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.kakao_token = os.getenv('KAKAO_ACCESS_TOKEN')
        if not self.news_api_key or not self.kakao_token:
            raise ValueError("필수 API 키가 설정되지 않았습니다.")

    def _setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger('DailyMarketReporter')
        self.logger.setLevel(logging.INFO)
        log_file = os.path.join(
            self.log_dir, 
            f'market_report_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _initialize_collectors(self):
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    def collect_market_data(self) -> Tuple[Dict, Dict]:
        """시장 데이터 수집 (재시도 로직 포함)"""
        try:
            self.logger.info("시장 데이터 수집 시작")
            market_data = self.market_collector.get_market_summary()
            self.logger.info("주식 시장 데이터 수집 완료")
            fear_greed = self.fear_greed_collector.get_fear_greed_data()
            self.logger.info("Fear & Greed 지수 수집 완료")
            return market_data, fear_greed
        except Exception as e:
            self.logger.error(f"시장 데이터 수집 실패: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    def collect_news_data(self) -> Dict:
        """뉴스 데이터 수집 (재시도 로직 포함)"""
        try:
            self.logger.info("뉴스 데이터 수집 시작")
            news_data = self.news_collector.collect_news()
            if news_data and news_data['articles']:
                self.logger.info(f"뉴스 데이터 수집 완료: {len(news_data['articles'])}개 기사")
                return news_data
            else:
                raise ValueError("수집된 뉴스 데이터가 없습니다.")
        except Exception as e:
            self.logger.error(f"뉴스 데이터 수집 실패: {str(e)}")
            raise

    def generate_market_visuals(self) -> Optional[Dict]:
        """시장 데이터 시각화"""
        try:
            self.logger.info("시각화 생성 시작")
            visuals = self.visualizer.generate_market_report()
            self.logger.info("시각화 생성 완료")
            return visuals
        except Exception as e:
            self.logger.error(f"시각화 생성 실패: {str(e)}")
            return None

    def create_llm_summary(self, news_data: Dict) -> str:
        """LLM을 사용한 뉴스 요약 생성"""
        try:
            self.logger.info("LLM 뉴스 요약 시작")
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY가 설정되지 않았습니다.")
            recent_articles = news_data['articles'][:5]
            news_texts = []
            for article in recent_articles:
                title = article.get('title', '')
                content = article.get('content', article.get('description', ''))
                if title and content:
                    news_texts.append(f"제목: {title}\n내용: {content}")
            if not news_texts:
                raise ValueError("요약할 뉴스 텍스트가 없습니다.")
            combined_text = "\n\n".join(news_texts)
            prompt = f"""다음 뉴스들을 분석하고 주식 시장에 미치는 영향을 한글로 요약해주세요:

{combined_text}

다음 형식으로 작성해주세요:
제목: (전체 내용을 대표하는 제목)
요약: (핵심 내용을 3줄로 요약)
시장 영향: (주식 시장에 미칠 수 있는 영향을 설명)"""
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=groq_api_key
            )
            combine_prompt = PromptTemplate(
                input_variables=['text'], 
                template="You are a financial analyst participating in 1:1 dialogue. Please analyze and respond about market news: {text}."
            )
            chain = LLMChain(llm=llm, prompt=combine_prompt, verbose=True)
            response = chain.invoke({'text': prompt})
            summary = response['text']
            self.logger.info("LLM 뉴스 요약 완료")
            return summary
        except Exception as e:
            self.logger.error(f"LLM 요약 생성 실패: {str(e)}")
            return "뉴스 요약을 생성하는 중 오류가 발생했습니다."

    def _interpret_fear_greed(self, value: float) -> str:
        """Fear & Greed 지수 해석"""
        if value <= 25:
            return "극도의 공포"
        elif value <= 45:
            return "공포"
        elif value <= 55:
            return "중립"
        elif value <= 75:
            return "탐욕"
        else:
            return "극도의 탐욕"

    def _get_investment_warnings(self) -> List[str]:
        """투자 유의사항 목록"""
        return [
            "- 본 리포트는 투자 참고 자료일 뿐, 투자 권유가 아닙니다",
            "- 투자 결정은 본인의 판단과 책임하에 신중히 이루어져야 합니다",
            "- 과거의 수익률이 미래의 수익률을 보장하지 않습니다"
        ]

    def format_daily_report(self, market_data: Dict, fear_greed: Dict, news_summary: str) -> str:
        """일일 리포트 포맷팅"""
        try:
            report = []
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            report.append(f"📊 일일 시장 리포트 ({current_time})")
            report.append("\n💹 주요 지수 동향")
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
            if fear_greed:
                report.append("\n🎯 투자 심리 지표")
                report.append(f"• Fear & Greed 지수: {fear_greed['value']}")
                value = float(fear_greed['value'])
                mood = self._interpret_fear_greed(value)
                report.append(f"• 현재 시장 심리: {mood}")
            if news_summary:
                report.append("\n📰 주요 뉴스 요약")
                report.append(news_summary)
            report.append("\n\n💡 투자 유의사항")
            report.extend(self._get_investment_warnings())
            return "\n".join(report)
        except Exception as e:
            self.logger.error(f"리포트 포맷팅 실패: {str(e)}")
            return "리포트 생성 중 오류가 발생했습니다."

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    def send_kakao_message(self, message: str):
        """카카오톡 메시지 발송 (재시도 로직 포함)"""
        try:
            self.logger.info("카카오톡 메시지 발송 시작")
            url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
            headers = {
                'Authorization': f'Bearer {self.kakao_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
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
            response.raise_for_status()
            self.logger.info("카카오톡 메시지 발송 성공")
        except Exception as e:
            self.logger.error(f"카카오톡 메시지 발송 오류: {str(e)}")
            raise

    def run_daily_report(self) -> bool:
        """일일 리포트 실행"""
        success = False
        try:
            self.logger.info("일일 리포트 생성 시작")
            market_data, fear_greed = self.collect_market_data()
            news_data = self.collect_news_data()
            if not market_data or not news_data:
                raise Exception("필수 데이터 수집 실패")
            visuals = self.generate_market_visuals()
            news_summary = self.create_llm_summary(news_data)
            report = self.format_daily_report(market_data, fear_greed, news_summary)
            self.send_kakao_message(report)
            self.logger.info("일일 리포트 생성 및 발송 완료")
            success = True
        except Exception as e:
            error_msg = f"일일 리포트 생성 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            try:
                self.send_kakao_message(f"⚠️ 시스템 오류 발생\n{error_msg}")
            except:
                self.logger.error("오류 알림 발송 실패")
        return success


def main():
    """메인 실행 함수"""
    try:
        reporter = DailyMarketReporter()
        success = reporter.run_daily_report()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
