# src/data_processing/market_data_visualization.py

import os
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# 상위 디렉토리를 파이썬 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from src.data_collection.yahoo_finance import YahooFinance

class MarketVisualizer:
    def __init__(self, output_dir: str = "market_data"):
        self.colors = {
            'positive': '#34C759',
            'negative': '#FF3B30',
            'neutral': '#8E8E93',
            'background': '#FFFFFF'
        }
        self.collector = YahooFinance()
        self.output_dir = output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        # matplotlib 기본 설정
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = [12, 8]
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 12
        plt.rcParams['ytick.labelsize'] = 12
        plt.rcParams['grid.alpha'] = 0.3
        
        print("MarketVisualizer 초기화 완료")

    def _save_figure(self, name: str) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        plt.savefig(filepath, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close()
        print(f"차트가 저장되었습니다: {filepath}")
        return filepath

    def create_market_dashboard(self, save: bool = True) -> str:
        market_data = self.collector.get_market_summary()
        
        names = []
        changes = []
        colors = []
        
        for symbol, info in market_data.items():
            names.append(info['name'])
            changes.append(info['change_percent'])
            colors.append(self.colors['positive'] if info['change_percent'] > 0 
                        else self.colors['negative'])

        plt.figure(figsize=(16, 10))
        bars = plt.bar(names, changes, color=colors, width=0.6)
        
        # 데이터 레이블 추가
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:+.2f}%',
                    ha='center', va='bottom' if height >= 0 else 'top',
                    fontsize=11,
                    weight='bold')

        plt.title('시장 개요 (Market Overview)', pad=20, size=16, weight='bold')
        plt.xlabel('자산 종류', labelpad=15, size=12)
        plt.ylabel('일간 변동률 (%)', labelpad=15, size=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        filepath = ""
        if save:
            filepath = self._save_figure("market_dashboard")
        
        return filepath

    def create_correlation_matrix(self, save: bool = True) -> str:
        print("상관관계 매트릭스 생성 시작...")
        
        symbols = [
            {'^GSPC': 'S&P 500'}, 
            {'^DJI': 'Dow Jones'}, 
            {'^IXIC': 'NASDAQ'},
            {'AAPL': 'Apple'},
            {'MSFT': 'Microsoft'},
            {'GOOGL': 'Alphabet'},
            {'NVDA': 'NVIDIA'},
            {'META': 'Meta'}
        ]
        
        data_dict = {}
        for symbol_dict in symbols:
            symbol = list(symbol_dict.keys())[0]
            name = list(symbol_dict.values())[0]
            try:
                print(f"{name} 데이터 수집 중...")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1mo')['Close']
                if not hist.empty:
                    returns = hist.pct_change().dropna()
                    if len(returns) > 0:
                        data_dict[name] = returns
                        print(f"{name} 데이터 수집 성공 (데이터 포인트: {len(returns)}개)")
                    else:
                        print(f"Warning: {name}의 수익률 데이터가 비어있습니다.")
                else:
                    print(f"Warning: {name}의 히스토리 데이터가 비어있습니다.")
            except Exception as e:
                print(f"Error: {name} 데이터 수집 실패 - {str(e)}")
                continue

        if len(data_dict) < 2:
            print("Error: 충분한 데이터를 수집하지 못했습니다.")
            return ""

        print("상관관계 계산 중...")
        df = pd.DataFrame(data_dict)
        corr_matrix = df.corr()
        print("상관관계 계산 완료")

        # 히트맵 생성
        plt.figure(figsize=(12, 10))
        
        # 메인 히트맵
        im = plt.imshow(corr_matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
        
        # 컬러바 추가
        cbar = plt.colorbar(im)
        cbar.set_label('상관계수', rotation=270, labelpad=15)

        # 상관계수 값 표시
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                color = 'black'
                value = corr_matrix.iloc[i, j]
                plt.text(j, i, f'{value:.2f}',
                        ha='center', va='center',
                        color=color, fontsize=10,
                        weight='bold')

        # 축 레이블 설정
        plt.xticks(range(len(corr_matrix)), corr_matrix.columns, rotation=45, ha='right')
        plt.yticks(range(len(corr_matrix)), corr_matrix.index)
        
        # 제목 설정
        plt.title('자산 상관관계 매트릭스 (1개월 수익률 기준)', 
                 pad=20, size=16, weight='bold')
        
        plt.tight_layout()
        
        filepath = ""
        if save:
            filepath = self._save_figure("correlation_matrix")
        
        return filepath

    def generate_market_report(self) -> Dict[str, str]:
        print("=== 시장 데이터 시각화 및 저장 시작 ===")
        
        dashboard_path = self.create_market_dashboard(save=True)
        matrix_path = self.create_correlation_matrix(save=True)
        
        report_paths = {
            "market_dashboard": dashboard_path,
            "correlation_matrix": matrix_path
        }
        
        print("=== 시각화 및 저장 완료 ===")
        return report_paths

def main():
    print("=== 시장 데이터 시각화 시작 ===")
    
    visualizer = MarketVisualizer(output_dir="market_data")
    report_paths = visualizer.generate_market_report()
    
    print("\n저장된 차트 파일:")
    for chart_name, filepath in report_paths.items():
        print(f"- {chart_name}: {filepath}")
    
    print("시각화 완료!")

if __name__ == "__main__":
    main()