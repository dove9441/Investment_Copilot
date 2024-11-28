# src/data_processing/cnn_fear_greed_visualization.py

import sys
import os

# 현재 파일의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# src 디렉토리
src_dir = os.path.dirname(current_dir)
# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
if src_dir not in sys.path:
    sys.path.append(src_dir)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from data_collection.cnn_fear_greed import CNNFearGreedIndex  # 수정된 import

# 나머지 코드는 그대로 유지...
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List
from data_collection.yahoo_finance import YahooFinance

class MarketVisualizer:
    """시장 데이터 시각화 클래스"""
    
    def __init__(self):
        """시각화를 위한 기본 설정"""
        self.colors = {
            'positive': '#34C759',  # 초록
            'negative': '#FF3B30',  # 빨강
            'neutral': '#8E8E93',   # 회색
            'background': '#FFFFFF'  # 흰색
        }
        self.collector = YahooFinance()
        print("MarketVisualizer 초기화 완료")

    def create_market_dashboard(self) -> go.Figure:
        """종합 시장 대시보드 생성"""
        # 데이터 수집
        market_data = self.collector.get_market_summary()
        
        # 서브플롯 생성
        fig = go.Figure()
        
        # 데이터 준비
        names = []
        changes = []
        colors = []
        hover_texts = []
        
        for symbol, info in market_data.items():
            names.append(info['name'])
            changes.append(info['change_percent'])
            colors.append(self.colors['positive'] if info['change_percent'] > 0 
                        else self.colors['negative'])
            hover_texts.append(
                f"{info['name']}<br>" +
                f"가격: {info['formatted_price']}<br>" +
                f"변동: {info['change_percent']:+.2f}%"
            )

        # 바 차트 추가
        fig.add_trace(go.Bar(
            x=names,
            y=changes,
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in changes],
            textposition='auto',
            hovertext=hover_texts,
            hoverinfo='text'
        ))

        # 레이아웃 설정
        fig.update_layout(
            title='Market Overview',
            title_x=0.5,
            xaxis_title='Asset',
            yaxis_title='Daily Change (%)',
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            height=800,
            width=1200,
            showlegend=False,
            xaxis_tickangle=-45,
            margin=dict(t=100, b=100),
            xaxis=dict(gridcolor='LightGrey'),
            yaxis=dict(gridcolor='LightGrey'),
            hoverlabel=dict(bgcolor='white'),
        )

        return fig

    def create_market_tables(self) -> Dict[str, go.Figure]:
        """카테고리별 시장 데이터 테이블 생성"""
        market_data = self.collector.get_market_summary()
        tables = {}
        
        # 카테고리별로 데이터 분류
        categorized_data = {
            '주요 지수': {},
            '국채 수익률': {},
            '원자재': {},
            '기술주': {}
        }
        
        for symbol, data in market_data.items():
            if symbol in self.collector.indices:
                categorized_data['주요 지수'][symbol] = data
            elif symbol in self.collector.treasuries:
                categorized_data['국채 수익률'][symbol] = data
            elif symbol in self.collector.commodities:
                categorized_data['원자재'][symbol] = data
            elif symbol in self.collector.tech_stocks:
                categorized_data['기술주'][symbol] = data

        # 각 카테고리별 테이블 생성
        for category, data in categorized_data.items():
            if data:
                headers = ['자산', '현재가', '변동폭', '거래량']
                cells = [
                    [info['name'] for info in data.values()],
                    [info['formatted_price'] for info in data.values()],
                    [f"{info['change_percent']:+.2f}%" for info in data.values()],
                    [f"{int(info['volume']):,}" if info['volume'] > 0 else 'N/A' 
                     for info in data.values()]
                ]
                
                fig = go.Figure(data=[go.Table(
                    header=dict(
                        values=headers,
                        fill_color='grey',
                        align='left',
                        font=dict(color='white', size=12)
                    ),
                    cells=dict(
                        values=cells,
                        fill_color='white',
                        align='left',
                        font=dict(color='black', size=11),
                        height=30
                    )
                )])
                
                fig.update_layout(
                    title=category,
                    title_x=0.5,
                    width=800,
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                
                tables[category] = fig
                
        return tables

def main():
    """메인 실행 함수"""
    print("=== 시장 데이터 시각화 시작 ===")
    visualizer = MarketVisualizer()
    
    print("\n1. 시장 대시보드 생성 중...")
    dashboard = visualizer.create_market_dashboard()
    dashboard.show()
    
    print("\n2. 카테고리별 테이블 생성 중...")
    tables = visualizer.create_market_tables()
    for category, table in tables.items():
        print(f"\n{category} 테이블 표시 중...")
        table.show()
    
    print("\n시각화 완료!")

if __name__ == "__main__":
    main()