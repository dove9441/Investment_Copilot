import requests
import logging
import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import trafilatura
from typing import Dict, List, Optional, Union
import nltk
from nltk.tokenize import sent_tokenize
import hashlib

class EnhancedNewsAPIClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required. Please set NEWS_API_KEY in your .env file")
            
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/'
        self.logger = logging.getLogger(__name__)
        self.data_dir = 'data/raw/news'
        self.processed_dir = 'data/processed/news'
        
        # 디버그를 위한 로깅 추가
        self.logger.info(f"Initializing with API key: {api_key[:5]}...")
        
        # 필요한 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # NLTK 데이터 다운로드
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        # User-Agent 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_news(self, category: str = 'business', country: str = 'us') -> Dict:
        """
        뉴스를 가져오고 전처리, 요약까지 수행하는 메인 메서드
        """
        try:
            # 1. 뉴스 데이터 가져오기
            raw_news = self._fetch_news(category, country)
            if not raw_news or raw_news.get('status') != 'ok':
                error_msg = raw_news.get('message', 'Unknown error') if raw_news else 'Failed to fetch news'
                self.logger.error(f"API Error: {error_msg}")
                return {
                    'status': 'error',
                    'message': error_msg,
                    'data': None
                }

            # 2. 각 기사 전문 가져오기 및 처리
            processed_articles = []
            for article in raw_news['articles'][:10]:  # 상위 10개 기사만 처리
                processed_article = self._process_article(article)
                if processed_article:
                    processed_articles.append(processed_article)
                time.sleep(1)  # 웹사이트 부하 방지

            # 3. 결과 저장
            result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'country': country,
                'total_processed': len(processed_articles),
                'articles': processed_articles
            }

            # 4. 파일로 저장
            self._save_processed_news(result)

            return result

        except Exception as e:
            self.logger.error(f"Error in get_news: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'data': None
            }

    def _fetch_news(self, category: str, country: str) -> Dict:
        """NewsAPI에서 뉴스 가져오기"""
        try:
            url = f'{self.base_url}top-headlines'
            params = {
                'country': country,
                'category': category,
                'pageSize': 10,
                'apiKey': self.api_key
            }
            
            self.logger.info(f"Fetching news from {url}")
            response = requests.get(url, params=params)
            
            self.logger.info(f"Response status code: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"Successfully fetched {len(data.get('articles', []))} articles")
            
            return data

        except Exception as e:
            self.logger.error(f"Error fetching news: {str(e)}")
            return None

    def _process_article(self, article: Dict) -> Optional[Dict]:
        """개별 기사 처리"""
        try:
            url = article['url']
            if not url:
                return None

            # 1. 전문 가져오기
            full_content = self._get_full_content(url)
            if not full_content:
                return None

            # 2. 텍스트 전처리
            processed_content = self._preprocess_text(full_content['content'])

            # 3. 요약 생성
            summary = self._generate_summary(processed_content)

            # 4. 결과 조합
            return {
                'title': article['title'],
                'source': article['source']['name'],
                'author': article.get('author'),
                'published_at': article['publishedAt'],
                'url': url,
                'original_description': article.get('description'),
                'processed_content': processed_content,
                'summary': summary,
                'content_length': len(processed_content),
                'extraction_method': full_content['method'],
                'processed_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error processing article: {str(e)}")
            return None

    def _get_full_content(self, url: str) -> Optional[Dict]:
        """기사 전문 추출"""
        try:
            # 1. newspaper3k 시도
            article = Article(url)
            article.download()
            article.parse()
            
            if article.text:
                return {
                    'content': article.text,
                    'method': 'newspaper3k'
                }

            # 2. trafilatura 시도
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded)
                if content:
                    return {
                        'content': content,
                        'method': 'trafilatura'
                    }

            # 3. BeautifulSoup 시도
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            article_body = (
                soup.find('article') or 
                soup.find('div', {'class': ['article-body', 'story-body']}) or
                soup.find('div', {'itemprop': 'articleBody'})
            )
            
            if article_body:
                for tag in article_body.find_all(['script', 'style', 'nav', 'aside']):
                    tag.decompose()
                
                return {
                    'content': article_body.get_text(strip=True),
                    'method': 'beautifulsoup'
                }

            return None

        except Exception as e:
            self.logger.error(f"Error getting full content from {url}: {str(e)}")
            return None

    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        try:
            text = ' '.join(text.split())
            sentences = sent_tokenize(text)
            text = ' '.join(sentences)
            text = text.replace('"', '"').replace('"', '"')
            return text
        except Exception as e:
            self.logger.error(f"Error in text preprocessing: {str(e)}")
            return text

    def _generate_summary(self, text: str, max_sentences: int = 5) -> str:
        """텍스트 요약 생성"""
        try:
            sentences = sent_tokenize(text)
            
            if len(sentences) <= max_sentences:
                return text
            
            important_sentences = [sentences[0]]  # 첫 문장은 항상 포함
            
            other_sentences = sorted(
                sentences[1:],
                key=len,
                reverse=True
            )[:max_sentences-1]
            
            important_sentences.extend(other_sentences)
            
            summary_sentences = sorted(
                important_sentences,
                key=lambda s: sentences.index(s)
            )
            
            return ' '.join(summary_sentences)

        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return text[:500] + "..."

    def _save_processed_news(self, data: Dict) -> bool:
        """처리된 뉴스 데이터 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"processed_news_{data['category']}_{timestamp}.json"
            filepath = os.path.join(self.processed_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully saved processed news to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving processed news: {str(e)}")
            return False

# 메인 실행 부분
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
            
        logger.info("API key loaded successfully")
        
        client = EnhancedNewsAPIClient(api_key)
        result = client.get_news(category='technology')
        
        if result['status'] == 'success':
            print(f"\nProcessed {result['total_processed']} articles")
            
            for idx, article in enumerate(result['articles'], 1):
                print(f"\n{idx}. {article['title']}")
                print(f"Source: {article['source']}")
                print(f"Summary ({len(article['summary'])} chars):")
                print(article['summary'])
                print("-" * 80)
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
"""
# NewsAPI 응답 데이터 구조 및 활용 가이드

## 1. 기본 응답 구조

```
성공시
{
    "status": "success",
    "timestamp": "2024-11-19T20:15:30.123456",
    "category": "technology",
    "country": "us",
    "total_processed": 10,
    "articles": [
        {
            "title": "Article Title Here",
            "source": "News Source Name",
            "author": "Author Name",
            "published_at": "2024-11-19T20:00:00Z",
            "url": "https://example.com/article",
            "original_description": "Original article description from API",
            "processed_content": "Full processed article content...",
            "summary": "Generated summary of the article...",
            "content_length": 1500,
            "extraction_method": "newspaper3k",
            "processed_at": "2024-11-19T20:15:30.123456"
        },
        // ... 더 많은 기사들 (최대 10개)
    ]
}

실패시

{
    "status": "error",
    "message": "Error message describing what went wrong",
    "data": null
}

```

## 2. 주요 필드 설명

### 메타데이터
- `status`: API 응답 상태 ("success" 또는 "error")
- `total_results`: 검색된 총 기사 수
- `request_time`: API 요청 시간

### 기사 정보 (`articles` 배열의 각 항목)
1. **출처 정보** (`source`)
   - `id`: 뉴스 제공자 고유 ID
   - `name`: 뉴스 제공자 이름

2. **기사 메타데이터**
   - `author`: 기사 작성자
   - `title`: 기사 제목
   - `description`: 기사 요약/설명
   - `url`: 원본 기사 링크
   - `image_url`: 관련 이미지 URL
   - `published_at`: 발행 일시 (ISO 8601 형식)
   - `content`: 기사 본문 일부



"""