# src/data_collection/yahoo_finance.py

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
        
        # 주요 지수 심볼과 단위
        self.indices = {
            '^GSPC': {'name': 'S&P 500', 'unit': 'points'},
            '^DJI': {'name': 'Dow Jones', 'unit': 'points'},
            '^IXIC': {'name': 'NASDAQ', 'unit': 'points'}
        }
        
        # 국채 심볼과 단위
        self.treasuries = {
            '^IRX': {'name': '13 Week Treasury', 'unit': '%'},
            '^FVX': {'name': '5 Year Treasury', 'unit': '%'},
            '^TNX': {'name': '10 Year Treasury', 'unit': '%'}
        }
        
        # 상품 심볼과 단위
        self.commodities = {
            'GC=F': {'name': 'Gold', 'unit': '$/oz'},
            'CL=F': {'name': 'WTI Oil', 'unit': '$/bbl'},
            'NG=F': {'name': 'Natural Gas', 'unit': '$/MMBtu'},
            'HG=F': {'name': 'Copper', 'unit': '$/lb'}
        }
        
        # 주요 기술주 심볼과 단위
        self.tech_stocks = {
            'NVDA': {'name': 'NVIDIA', 'unit': '$'},
            'AAPL': {'name': 'Apple', 'unit': '$'},
            'MSFT': {'name': 'Microsoft', 'unit': '$'},
            'GOOGL': {'name': 'Alphabet', 'unit': '$'},
            'META': {'name': 'Meta', 'unit': '$'}
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
        elif unit == 'points':
            return f"{value:,.2f} pts"
        else:  # 달러 단위 기본값
            return f"${value:.2f}"

    def get_market_summary(self, symbols: Optional[List[str]] = None) -> Dict:
        """여러 종목의 현재 시장 데이터 조회"""
        if symbols is None:
            # 기본값으로 모든 심볼 사용
            all_symbols = {}
            all_symbols.update(self.indices)
            all_symbols.update(self.treasuries)
            all_symbols.update(self.commodities)
            all_symbols.update(self.tech_stocks)
            symbols = list(all_symbols.keys())

        print("\n=== 시장 데이터 수집 시작 ===")
        data = {}
        
        # 각 카테고리별로 데이터 수집
        categories = [
            ("주요 지수", self.indices),
            ("국채 수익률", self.treasuries),
            ("원자재", self.commodities),
            ("기술주", self.tech_stocks)
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