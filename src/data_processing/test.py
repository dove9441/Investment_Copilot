
from data_collection.yahoo_finance import YahooFinance
import pprint

class A:
    def __init__(self):
            """시각화를 위한 기본 설정"""
            self.colors = {
                'positive': '#34C759',  # 초록
                'negative': '#FF3B30',  # 빨강
                'neutral': '#8E8E93',   # 회색
                'background': '#FFFFFF',  # 흰색
                'extreme_fear': '#FF3B30',    # 빨강 (극도의 공포)
                'fear': '#FF9500',            # 주황 (공포)
                'neutral': '#FFCC00',         # 노랑 (중립)
                'greed': '#34C759',           # 초록 (탐욕)
                'extreme_greed': '#007AFF'    # 파랑 (극도의 탐욕)
            }
            self.yahoo_collector = YahooFinance()
    def main(self):
        market_data = self.yahoo_collector.get_market_summary()
        pprint.pprint(market_data)


if __name__ == "__main__":
    main()