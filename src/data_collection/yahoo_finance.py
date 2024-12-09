import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional
import requests.exceptions

class YahooFinance:
    def __init__(self):
        """초기화 함수"""
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 주요 글로벌 지수 심볼과 단위
        self.indices = {
            '^GSPC': {'name': 'S&P 500', 'unit': 'points'},           # 미국 S&P 500
            '^DJI': {'name': 'Dow Jones', 'unit': 'points'},          # 미국 다우존스
            '^IXIC': {'name': 'NASDAQ', 'unit': 'points'},            # 미국 나스닥
            '^RUT': {'name': 'Russell 2000', 'unit': 'points'},       # 미국 소형주
            '^VIX': {'name': 'VIX', 'unit': 'points'},                # 변동성 지수
            '^N225': {'name': 'Nikkei 225', 'unit': 'points'},        # 일본 닛케이
            '^HSI': {'name': 'Hang Seng', 'unit': 'points'},          # 홍콩 항생
            '^FTSE': {'name': 'FTSE 100', 'unit': 'points'},          # 영국 FTSE
            '^GDAXI': {'name': 'DAX', 'unit': 'points'},              # 독일 DAX
            '^FCHI': {'name': 'CAC 40', 'unit': 'points'}             # 프랑스 CAC
        }
        
        # 국채 심볼과 단위
        self.treasuries = {
            '^IRX': {'name': '13 Week Treasury', 'unit': '%'},
            '^FVX': {'name': '5 Year Treasury', 'unit': '%'},
            '^TNX': {'name': '10 Year Treasury', 'unit': '%'},
            '^TYX': {'name': '30 Year Treasury', 'unit': '%'}
        }
        
        # 원자재 심볼과 단위
        self.commodities = {
            'GC=F': {'name': 'Gold', 'unit': '$/oz'},
            'SI=F': {'name': 'Silver', 'unit': '$/oz'},
            'PL=F': {'name': 'Platinum', 'unit': '$/oz'},
            'CL=F': {'name': 'WTI Oil', 'unit': '$/bbl'},
            'BZ=F': {'name': 'Brent Oil', 'unit': '$/bbl'},
            'NG=F': {'name': 'Natural Gas', 'unit': '$/MMBtu'},
            'HG=F': {'name': 'Copper', 'unit': '$/lb'},
            'ZC=F': {'name': 'Corn', 'unit': '￠/bu'},
            'ZW=F': {'name': 'Wheat', 'unit': '￠/bu'},
            'ZS=F': {'name': 'Soybean', 'unit': '￠/bu'}
        }
        
        # 기술주 (Technology) - 30개로 확장
        self.tech_stocks = {
            # 대형 기술주
            'AAPL': {'name': 'Apple', 'unit': '$'},              # 소비자 기술
            'MSFT': {'name': 'Microsoft', 'unit': '$'},          # 소프트웨어/클라우드
            'GOOGL': {'name': 'Alphabet', 'unit': '$'},          # 검색/광고
            'AMZN': {'name': 'Amazon', 'unit': '$'},             # 전자상거래/클라우드
            'META': {'name': 'Meta', 'unit': '$'},               # 소셜미디어
            'TSLA': {'name': 'Tesla', 'unit': '$'},               #전기차/인공지능
            # 반도체
            
            'NVDA': {'name': 'NVIDIA', 'unit': '$'},             # GPU/AI칩
            'AMD': {'name': 'AMD', 'unit': '$'},                 # CPU/GPU
            'AVGO': {'name': 'Broadcom', 'unit': '$'},           # 통신칩
            'QCOM': {'name': 'Qualcomm', 'unit': '$'},           # 모바일칩
            'INTC': {'name': 'Intel', 'unit': '$'},              # CPU
            'MU': {'name': 'Micron', 'unit': '$'},               # 메모리
            'ADI': {'name': 'Analog Devices', 'unit': '$'},      # 아날로그반도체
            'TSM': {'name': 'TSMC', 'unit': '$'},                # 파운드리
            'AMAT': {'name': 'Applied Materials', 'unit': '$'},   # 반도체장비
            'LRCX': {'name': 'Lam Research', 'unit': '$'},       # 반도체장비
            
            # 소프트웨어/클라우드
            'CRM': {'name': 'Salesforce', 'unit': '$'},          # CRM솔루션
            'ADBE': {'name': 'Adobe', 'unit': '$'},              # 창작소프트웨어
            'ORCL': {'name': 'Oracle', 'unit': '$'},             # 기업솔루션
            'NOW': {'name': 'ServiceNow', 'unit': '$'},          # 워크플로우
            'INTU': {'name': 'Intuit', 'unit': '$'},             # 금융소프트웨어
            'SNPS': {'name': 'Synopsys', 'unit': '$'},           # 설계소프트웨어
            
            # 네트워크/보안
            'CSCO': {'name': 'Cisco', 'unit': '$'},              # 네트워크장비
            'ANET': {'name': 'Arista Networks', 'unit': '$'},    # 클라우드네트워킹
            'PANW': {'name': 'Palo Alto Networks', 'unit': '$'}, # 사이버보안
            'CRWD': {'name': 'CrowdStrike', 'unit': '$'},        # 엔드포인트보안
            'ZS': {'name': 'Zscaler', 'unit': '$'},              # 클라우드보안
            
            # 기타 기술
            'IBM': {'name': 'IBM', 'unit': '$'},                 # IT서비스/AI
            'ACN': {'name': 'Accenture', 'unit': '$'},           # IT컨설팅
            'UBER': {'name': 'Uber', 'unit': '$'},               # 공유경제
            'ABNB': {'name': 'Airbnb', 'unit': '$'},             # 공유숙박
            'PYPL': {'name': 'PayPal', 'unit': '$'}              # 핀테크
        }

        # 금융주 (Financial)
        self.financial_stocks = {
            'JPM': {'name': 'JPMorgan Chase', 'unit': '$'},
            'BAC': {'name': 'Bank of America', 'unit': '$'},
            'WFC': {'name': 'Wells Fargo', 'unit': '$'},
            'GS': {'name': 'Goldman Sachs', 'unit': '$'},
            'MS': {'name': 'Morgan Stanley', 'unit': '$'},
            'BLK': {'name': 'BlackRock', 'unit': '$'},
            'C': {'name': 'Citigroup', 'unit': '$'},
            'AXP': {'name': 'American Express', 'unit': '$'}
        }

        # 헬스케어 (Healthcare)
        self.healthcare_stocks = {
            'JNJ': {'name': 'Johnson & Johnson', 'unit': '$'},
            'UNH': {'name': 'UnitedHealth', 'unit': '$'},
            'LLY': {'name': 'Eli Lilly', 'unit': '$'},
            'PFE': {'name': 'Pfizer', 'unit': '$'},
            'MRK': {'name': 'Merck', 'unit': '$'},
            'TMO': {'name': 'Thermo Fisher', 'unit': '$'},
            'ABT': {'name': 'Abbott Labs', 'unit': '$'},
            'DHR': {'name': 'Danaher', 'unit': '$'}
        }

        # 소비재 (Consumer)
        self.consumer_stocks = {
            'PG': {'name': 'Procter & Gamble', 'unit': '$'},
            'KO': {'name': 'Coca-Cola', 'unit': '$'},
            'PEP': {'name': 'PepsiCo', 'unit': '$'},
            'COST': {'name': 'Costco', 'unit': '$'},
            'WMT': {'name': 'Walmart', 'unit': '$'},
            'MCD': {'name': "McDonald's", 'unit': '$'},
            'NKE': {'name': 'Nike', 'unit': '$'},
            'SBUX': {'name': 'Starbucks', 'unit': '$'}
        }

        # 산업재 (Industrial)
        self.industrial_stocks = {
            'CAT': {'name': 'Caterpillar', 'unit': '$'},
            'BA': {'name': 'Boeing', 'unit': '$'},
            'GE': {'name': 'General Electric', 'unit': '$'},
            'HON': {'name': 'Honeywell', 'unit': '$'},
            'UPS': {'name': 'UPS', 'unit': '$'},
            'RTX': {'name': 'Raytheon', 'unit': '$'},
            'DE': {'name': 'John Deere', 'unit': '$'},
            'MMM': {'name': '3M', 'unit': '$'}
        }
        
        print("YahooFinance 초기화 완료")

    def _format_value(self, value: float, unit: str) -> str:
        """단위에 따른 값 포맷팅"""
        if unit == '%':
            return f"{value:.2f}%"
        elif unit == '$/oz':
            return f"${value:.2f}/oz"
        elif unit == '$/bbl':
            return f"${value:.2f}/bbl"
        elif unit == '$/MMBtu':
            return f"${value:.2f}/MMBtu"
        elif unit == '$/lb':
            return f"${value:.2f}/lb"
        elif unit == '￠/bu':
            return f"{value:.2f}￠/bu"
        elif unit == 'points':
            return f"{value:,.2f} pts"
        else:  # 달러 단위 기본값
            return f"${value:.2f}"

    def get_market_summary(self, symbols: Optional[List[str]] = None) -> Dict:
        """여러 종목의 현재 시장 데이터 조회"""
        if symbols is None:
            # 기본값으로 모든 심볼 사용
            all_symbols = {}
            all_symbols.update(self.indices)         # 글로벌 지수
            all_symbols.update(self.treasuries)      # 미국 국채
            all_symbols.update(self.commodities)     # 원자재
            all_symbols.update(self.tech_stocks)     # 기술주
            all_symbols.update(self.financial_stocks) # 금융주
            all_symbols.update(self.healthcare_stocks) # 헬스케어
            all_symbols.update(self.consumer_stocks)  # 소비재
            all_symbols.update(self.industrial_stocks) # 산업재
            symbols = list(all_symbols.keys())

        print("\n=== 시장 데이터 수집 시작 ===")
        data = {}
        
        # 각 카테고리별로 데이터 수집
        categories = [
            ("글로벌 지수", self.indices),
            ("미국 국채", self.treasuries),
            ("원자재", self.commodities),
            ("기술주", self.tech_stocks),
            ("금융주", self.financial_stocks),
            ("헬스케어", self.healthcare_stocks),
            ("소비재", self.consumer_stocks),
            ("산업재", self.industrial_stocks)
        ]
        
        for category_name, category_symbols in categories:
            print(f"\n{category_name}")
            for symbol, info in category_symbols.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='1d')
                    
                    if hist.empty:
                        continue
                    
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Open'].iloc[-1]
                    
                    # 변동폭 계산
                    price_change = current_price - previous_close
                    change_percent = (price_change / previous_close * 100)
                    
                    # 국채의 경우 직접 수익률 값 사용
                    if symbol in self.treasuries:
                        current_price = current_price  # 이미 퍼센트 값임
                    
                    formatted_price = self._format_value(current_price, info['unit'])
                    
                    data[symbol] = {
                        'name': info['name'],
                        'price': current_price,
                        'formatted_price': formatted_price,
                        'unit': info['unit'],
                        'change': price_change,
                        'change_percent': change_percent,
                        'volume': hist['Volume'].iloc[-1],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    print(f"{info['name']}: {formatted_price} ({change_percent:+.2f}%)")
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"{symbol} 네트워크 오류: {str(e)}")
                    continue
                except ValueError as e:
                    self.logger.error(f"{symbol} 데이터 오류: {str(e)}")
                    continue
                except Exception as e:
                    self.logger.error(f"{symbol} 예상치 못한 오류: {str(e)}")
                    continue

        return data

def main():
    """테스트 실행"""
    print("=== 시장 데이터 수집 테스트 ===")
    collector = YahooFinance()
    
    # 전체 시장 데이터 수집
    market_data = collector.get_market_summary()
    
    if market_data:
        print("\n=== 요약 ===")
        for symbol, data in market_data.items():
            print(f"{data['name']}: {data['formatted_price']} ({data['change_percent']:+.2f}%)")
    else:
        print("데이터 수집 실패")

if __name__ == "__main__":
    main()