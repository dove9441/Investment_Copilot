
"""
News Collector for LLM Processing
-------------------------------
미국의 주요 뉴스를 수집하고 전체 내용을 포함하여 LLM 처리를 위해 최적화된 형태로 제공

Author: Junyoung Kwon
Last Modified: 2024-11-21
"""

import requests
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from newspaper import Article
import nltk

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class NewsCollector:
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

    def _fetch_top_headlines(self) -> Optional[Dict]:
        """Top Headlines API를 통해 주요 뉴스 가져오기"""
        try:
            # 어제 날짜 계산
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            
            url = f'{self.base_url}top-headlines'
            params = {
                'country': 'us',  # 미국 뉴스로 한정
                'pageSize': 100,  # 최대한 많은 기사 수집
                'from': yesterday_str,
                'language': 'en',
                'apiKey': self.api_key
            }

            print("  - API 요청 중...")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"  - API 오류: {response.status_code}")
                return None

            data = response.json()
            print(f"  - {len(data.get('articles', []))}개의 기사 발견")
            return data

        except Exception as e:
            print(f"  - 데이터 수집 실패: {str(e)}")
            return None

    def _process_and_score_articles(self, articles: List[Dict]) -> List[Dict]:
        """기사 처리 및 점수화"""
        scored_articles = []
        print(f"  - {len(articles)}개 기사 분석 중...")
        
        for idx, article in enumerate(articles, 1):
            if idx % 10 == 0:
                print(f"  - {idx}/{len(articles)} 기사 처리됨...")
            
            score = self._calculate_article_score(article)
            scored_articles.append((score, article))

        # 점수 기준 정렬
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scored_articles]

    def _calculate_article_score(self, article: Dict) -> int:
        """기사 중요도 점수 계산"""
        score = 0
        title = article.get('title', '').lower()
        source = article.get('source', {}).get('name', '')

        # 중요 키워드 점수
        priority_keywords = {
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

        for keyword, points in priority_keywords.items():
            if keyword in title:
                score += points

        # 신뢰도 높은 출처 점수
        trusted_sources = {
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
        score += trusted_sources.get(source, 0)

        # 콘텐츠 존재 여부
        if article.get('content'):
            score += 5

        # URL 존재 여부
        if article.get('url'):
            score += 3

        return score

    def _get_full_article_content(self, url: str) -> Optional[str]:
        """기사 URL에서 전체 내용 추출"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            self.logger.error(f"기사 내용 추출 실패 ({url}): {str(e)}")
            return None

    def _prepare_result(self, articles: List[Dict]) -> Dict:
        """LLM 처리를 위한 결과 준비 (전체 내용 포함)"""
        processed_articles = []
        total_articles = len(articles)
        
        print("\n전체 기사 내용 수집 중...")
        for idx, article in enumerate(articles, 1):
            print(f"  - 진행률: {idx}/{total_articles} 기사 처리 중...")
            
            # 전체 내용 가져오기
            full_content = self._get_full_article_content(article.get('url', ''))
            
            processed_article = {
                'title': article.get('title'),
                'source': article.get('source', {}).get('name'),
                'url': article.get('url'),
                'publishedAt': article.get('publishedAt'),
                'summary': article.get('content'),  # API에서 제공하는 요약 보존
                'full_content': full_content  # 전체 내용 추가
            }
            processed_articles.append(processed_article)
            
            # API 부하 방지
            time.sleep(1)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(processed_articles),
            'articles': processed_articles
        }

    def _save_to_file(self, data: Dict) -> str:
        """수집된 뉴스 데이터 저장 및 파일 경로 반환"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"collected_news_{timestamp}.json"
            filepath = os.path.join(self.data_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  - 데이터 저장 완료: {filepath}")
            return filepath

        except Exception as e:
            print(f"  - 데이터 저장 실패: {str(e)}")
            return ""

    def _create_empty_result(self) -> Dict:
        """빈 결과 생성"""
        return {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'total_articles': 0,
            'articles': []
        }

    def main_display(self, result: Dict, filepath: str):
        """결과 상세 출력"""
        if result['total_articles'] > 0:
            print("\n=== 수집된 주요 뉴스 ===")
            for idx, article in enumerate(result['articles'], 1):
                print(f"\n{idx}. {article['title']}")
                print(f"출처: {article['source']}")
                print(f"시간: {article['publishedAt']}")
                print(f"URL: {article['url']}")
                
                # 전체 내용 일부 출력
                if article.get('full_content'):
                    preview = article['full_content'][:200] + "..." if len(article['full_content']) > 200 else article['full_content']
                    print(f"내용 미리보기: {preview}")
                
                if idx >= 10:  # 상위 10개만 출력
                    remaining = len(result['articles']) - 10
                    print(f"\n... 외 {remaining}개 기사")
                    break
                    
            print(f"\n전체 뉴스 데이터가 다음 파일에 저장되었습니다: {filepath}")
        else:
            print("\n수집된 뉴스가 없습니다.")

def main():
    """메인 실행 함수"""
    load_dotenv()
    api_key = os.getenv('NEWS_API_KEY')

    if not api_key:
        print("Error: API 키가 설정되지 않았습니다. .env 파일에 NEWS_API_KEY를 추가하세요.")
        return

    # 뉴스 수집 실행
    collector = NewsCollector(api_key)
    result = collector.collect_news()
    
    # 데이터 저장 및 결과 출력
    if result['status'] == 'success':
        filepath = collector._save_to_file(result)
        collector.main_display(result, filepath)
    else:
        print("뉴스 수집에 실패했습니다.")

if __name__ == "__main__":
    main()