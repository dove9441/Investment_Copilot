import requests
import logging
import json
import os
import time
import feedparser
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Union
from dotenv import load_dotenv
from newspaper import Article
import nltk

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class NewsAPIClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API 키가 필요합니다. .env 파일에 NEWS_API_KEY를 설정하세요.")
            
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/'
        self.logger = logging.getLogger(__name__)
        self.data_dir = os.path.join('data', 'raw', 'news')
        
        # 데이터 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        
        # newspaper3k 초기화
        try:
            nltk.data.find('punkt')
        except LookupError:
            print("NLTK punkt 데이터 다운로드 중...")
            nltk.download('punkt', quiet=True)

    def collect_news(self) -> Dict:
        """주요 뉴스 수집 및 처리"""
        try:
            print("\n=== 미국 주요 뉴스 수집 시작 ===")
            
            # 1. Top headlines API 호출
            print("1. 헤드라인 뉴스 수집 중...")
            headlines = self._fetch_top_headlines()
            
            if not headlines or not headlines.get('articles'):
                print("경고: 수집된 뉴스가 없습니다.")
                return self._create_empty_result()

            # 2. 기사 필터링 및 정렬
            print("2. 뉴스 중요도 분석 중...")
            articles = self._process_and_score_articles(headlines['articles'])
            
            # 3. 결과 저장
            print("3. 처리된 뉴스 저장 중...")
            result = self._prepare_result(articles)
            
            print(f"\n=== 뉴스 수집 완료: {len(articles)}개 기사 처리됨 ===\n")
            return result

        except Exception as e:
            self.logger.exception("뉴스 수집 중 오류 발생")
            print(f"오류 발생: {str(e)}")
            return self._create_empty_result()
        

class NewsCollector:
    """통합 뉴스 수집기 클래스"""
    
    def __init__(self, api_key: str = None, output_dir: str = "data/raw/news"):
        """
        통합 뉴스 수집기 초기화
        
        Args:
            api_key: NewsAPI 키 (선택사항)
            output_dir: 뉴스 데이터 저장 디렉토리
        """
        self.api_key = api_key
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # 데이터 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # newspaper3k 초기화
        try:
            nltk.data.find('punkt')
        except LookupError:
            print("NLTK punkt 데이터 다운로드 중...")
            nltk.download('punkt', quiet=True)
        
        # NewsAPI 설정
        self.base_url = 'https://newsapi.org/v2/'
        
        # RSS 피드 설정
        self.economic_sources = {
            'yahoo_finance': {
                'name': 'Yahoo Finance',
                'url': 'https://finance.yahoo.com/news/rssindex',
                'reliability': 8
            },
            'marketwatch': {
                'name': 'MarketWatch',
                'url': 'http://feeds.marketwatch.com/marketwatch/topstories',
                'reliability': 8
            },
            'reuters_markets': {
                'name': 'Reuters Markets',
                'url': 'https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best',
                'reliability': 9
            },
            'seeking_alpha': {
                'name': 'Seeking Alpha',
                'url': 'https://seekingalpha.com/market_currents.xml',
                'reliability': 7
            }
        }
        
        # 키워드 설정
        self.general_keywords = {
            'breaking': 15,
            'urgent': 12,
            'exclusive': 10,
            'alert': 8,
            'just in': 8,
            'developing': 7,
            'major': 6,
            'critical': 6,
            'important': 5
        }
        
        self.economic_keywords = {
            'market': 5,
            'stock': 4,
            'economy': 5,
            'fed': 6,
            'inflation': 5,
            'interest rate': 5,
            'recession': 6,
            'gdp': 4,
            'earnings': 4,
            'investment': 3
        }
        
        # 신뢰도 높은 출처
        self.trusted_sources = {
            'Reuters': 15,
            'Bloomberg': 15,
            'Associated Press': 14,
            'The Wall Street Journal': 13,
            'The New York Times': 12,
            'CNBC': 11,
            'Financial Times': 11,
            'BBC News': 10,
            'CNN': 9,
            'The Washington Post': 9
        }
        
        print("NewsCollector 초기화 완료")

    def collect_all_news(self) -> Dict:
        """
        모든 소스에서 뉴스 수집 및 통합
        
        Returns:
            Dict: 수집된 통합 뉴스 데이터
        """
        all_articles = []
        
        # NewsAPI로부터 일반 뉴스 수집
        if self.api_key:
            print("\n=== NewsAPI에서 뉴스 수집 중... ===")
            general_news = self._collect_from_newsapi()
            if general_news.get('status') == 'success':
                all_articles.extend(general_news['articles'])
        
        # RSS 피드로부터 경제 뉴스 수집
        print("\n=== RSS 피드에서 경제 뉴스 수집 중... ===")
        economic_news = self._collect_from_rss()
        all_articles.extend(economic_news)
        
        # 전체 기사 처리 및 정렬
        processed_articles = self._process_all_articles(all_articles)
        
        result = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(processed_articles),
            'articles': processed_articles
        }
        
        # 결과 저장
        self._save_to_file(result)
        
        return result

    def _collect_from_newsapi(self) -> Dict:
        """NewsAPI를 통한 뉴스 수집"""
        try:
            # 어제 날짜 계산
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            
            url = f'{self.base_url}top-headlines'
            params = {
                'country': 'us',
                'pageSize': 20,
                'from': yesterday_str,
                'language': 'en',
                'apiKey': self.api_key
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return self._create_empty_result()
            
            data = response.json()
            if not data.get('articles'):
                return self._create_empty_result()
            
            return {
                'status': 'success',
                'articles': self._process_newsapi_articles(data['articles'])
            }
            
        except Exception as e:
            self.logger.error(f"NewsAPI 수집 실패: {str(e)}")
            return self._create_empty_result()

    def _collect_from_rss(self) -> List[Dict]:
        """RSS 피드를 통한 경제 뉴스 수집"""
        articles = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_source = {
                executor.submit(self._fetch_from_rss, source_info): source_id
                for source_id, source_info in self.economic_sources.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_source):
                source_id = future_to_source[future]
                try:
                    source_articles = future.result()
                    articles.extend(source_articles)
                except Exception as e:
                    self.logger.error(f"{source_id} RSS 수집 실패: {str(e)}")
        
        return articles

    def _fetch_from_rss(self, source_info: Dict) -> List[Dict]:
        """특정 RSS 소스에서 뉴스 수집"""
        articles = []
        try:
            feed = feedparser.parse(source_info['url'])
            
            for entry in feed.entries:
                article = {
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'publishedAt': entry.get('published', ''),
                    'source': {'name': source_info['name']},
                    'content': entry.get('summary', '')
                }
                
                # 전체 내용 가져오기
                full_content = self._get_full_content(article['url'])
                if full_content:
                    article['full_content'] = full_content
                
                articles.append(article)
                
            return articles
            
        except Exception as e:
            self.logger.error(f"RSS 피드 수집 실패 ({source_info['name']}): {str(e)}")
            return []

    def _get_full_content(self, url: str) -> Optional[str]:
        """기사 전체 내용 추출"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            self.logger.error(f"기사 내용 추출 실패 ({url}): {str(e)}")
            return None

    def _calculate_article_score(self, article: Dict) -> int:
        """기사 중요도 점수 계산"""
        score = 0
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()
        source = article.get('source', {}).get('name', '')
        
        # 일반 키워드 점수
        for keyword, points in self.general_keywords.items():
            if keyword in text:
                score += points
        
        # 경제 키워드 점수
        for keyword, points in self.economic_keywords.items():
            if keyword in text:
                score += points
        
        # 출처 신뢰도 점수
        score += self.trusted_sources.get(source, 0)
        
        # 전체 내용 존재 여부
        if article.get('full_content'):
            score += 5
        
        return score

    def _process_all_articles(self, articles: List[Dict]) -> List[Dict]:
        """전체 기사 처리 및 정렬"""
        scored_articles = [
            (self._calculate_article_score(article), article)
            for article in articles
        ]
        
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scored_articles]

    def _process_newsapi_articles(self, articles: List[Dict]) -> List[Dict]:
        """NewsAPI 기사 처리"""
        processed = []
        for article in articles:
            processed_article = {
                'title': article.get('title'),
                'url': article.get('url'),
                'publishedAt': article.get('publishedAt'),
                'source': article.get('source', {}),
                'content': article.get('content'),
                'full_content': self._get_full_content(article.get('url', ''))
            }
            processed.append(processed_article)
            time.sleep(1)  # API 부하 방지
        
        return processed

    def _save_to_file(self, data: Dict) -> str:
        """결과 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"collected_news_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"\n데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {str(e)}")
            return ""

    def _create_empty_result(self) -> Dict:
        """빈 결과 생성"""
        return {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'total_articles': 0,
            'articles': []
        }

def main():
    """테스트용 메인 함수"""
    load_dotenv()
    api_key = os.getenv('NEWS_API_KEY')
    
    collector = NewsCollector(api_key=api_key)
    result = collector.collect_all_news()
    
    if result['status'] == 'success':
        print("\n=== 수집된 뉴스 ===")
        for idx, article in enumerate(result['articles'][:10], 1):
            print(f"\n{idx}. {article['title']}")
            print(f"출처: {article['source']['name']}")
            print(f"시간: {article['publishedAt']}")
            print(f"URL: {article['url']}")
            
            if article.get('full_content'):
                preview = article['full_content'][:200] + "..."
                print(f"내용 미리보기: {preview}")
    else:
        print("뉴스 수집에 실패했습니다.")

if __name__ == "__main__":
    main()