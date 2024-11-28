# src/data_processing/market_data_visualization.py

import sys
import os
# src 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        
        for symbol, info in market_data.items():
            names.append(info['name'])
            changes.append(info['change_percent'])
            colors.append(self.colors['positive'] if info['change_percent'] > 0 
                        else self.colors['negative'])

        # 바 차트 추가
        fig.add_trace(go.Bar(
            x=names,
            y=changes,
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in changes],
            textposition='auto',
        ))

        # 레이아웃 설정
        fig.update_layout(
            title='Market Overview',
            xaxis_title='Asset',
            yaxis_title='Daily Change (%)',
            plot_bgcolor=self.colors['background'],
            height=800,
            showlegend=False,
            xaxis_tickangle=-45
        )

        return fig

    def create_indices_comparison(self) -> go.Figure:
        """주요 지수 비교 차트"""
        # 주요 지수 데이터 수집
        indices_data = self.collector.get_market_summary(['^GSPC', '^DJI', '^IXIC'])
        
        names = []
        values = []
        changes = []
        colors = []
        
        for symbol, info in indices_data.items():
            names.append(info['name'])
            values.append(info['price'])
            changes.append(info['change_percent'])
            colors.append(self.colors['positive'] if info['change_percent'] > 0 
                        else self.colors['negative'])

        # 차트 생성
        fig = go.Figure()
        
        # 가격 바 차트
        fig.add_trace(go.Bar(
            name='Index Value',
            x=names,
            y=values,
            marker_color=colors,
            opacity=0.7,
            text=[f"${x:,.2f}" for x in values],
            textposition='auto',
        ))
        
        # 변동률 오버레이
        fig.add_trace(go.Scatter(
            name='Change %',
            x=names,
            y=changes,
            mode='markers+text',
            marker=dict(size=12, color=colors),
            text=[f"{x:+.2f}%" for x in changes],
            textposition='top center',
            yaxis='y2'
        ))

        # 레이아웃 설정
        fig.update_layout(
            title='Major Market Indices',
            yaxis=dict(title='Index Value'),
            yaxis2=dict(title='Change %', overlaying='y', side='right'),
            plot_bgcolor=self.colors['background'],
            height=600,
            showlegend=True
        )

        return fig

    def create_correlation_matrix(self) -> go.Figure:
        """자산 간 상관관계 히트맵"""
        # 데이터 수집
        market_data = self.collector.get_market_summary()
        
        # 상관관계 계산을 위한 데이터프레임 생성
        changes_dict = {}
        for symbol, info in market_data.items():
            changes_dict[info['name']] = info['change_percent']
        
        df = pd.DataFrame([changes_dict])
        corr_matrix = df.corr()

        # 히트맵 생성
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmin=-1,
            zmax=1,
            text=np.around(corr_matrix, decimals=2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))

        # 레이아웃 설정
        fig.update_layout(
            title='Asset Correlation Matrix',
            height=800,
            width=1000,
            xaxis_tickangle=-45
        )

        return fig

def main():
    """메인 실행 함수"""
    print("=== 시장 데이터 시각화 시작 ===")
    visualizer = MarketVisualizer()
    
    # 전체 시장 대시보드
    print("1. 시장 대시보드 생성 중...")
    dashboard = visualizer.create_market_dashboard()
    dashboard.show()
    
    # 주요 지수 비교
    print("2. 주요 지수 비교 차트 생성 중...")
    indices_chart = visualizer.create_indices_comparison()
    indices_chart.show()
    
    # 상관관계 매트릭스
    print("3. 상관관계 매트릭스 생성 중...")
    corr_matrix = visualizer.create_correlation_matrix()
    corr_matrix.show()
    
    print("시각화 완료!")

if __name__ == "__main__":
    main()