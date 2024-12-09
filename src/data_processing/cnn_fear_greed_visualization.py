import sys
import os

# 현재 파일의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# src 디렉토리
src_dir = os.path.dirname(current_dir)
# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
if src_dir not in sys.path:
    sys.path.append(src_dir)

# 한글 폰트 설정
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json

# 한글 폰트 설정
def set_korean_font():
    if os.name == 'nt':  # Windows
        font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    elif os.name == 'posix':  # macOS 또는 Linux
        font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"  # macOS
        # Linux에서는 한글 폰트를 시스템 경로에서 찾아 지정
        if not os.path.exists(font_path): 
            font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    
    if os.path.exists(font_path):
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        print(f"폰트 설정 완료: {font_prop.get_name()}")
    else:
        print("한글 폰트를 찾을 수 없습니다. 기본 설정을 사용합니다.")

# 한글 폰트 설정 호출
set_korean_font()




import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict
from datetime import datetime
import seaborn as sns
from data_collection.cnn_fear_greed import CNNFearGreedIndex
from data_collection.yahoo_finance import YahooFinance
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import pprint

class ComprehensiveMarketVisualizer:
    """종합 시장 데이터 시각화 클래스"""
    
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
        self.cnn_collector = CNNFearGreedIndex()
        print("ComprehensiveMarketVisualizer 초기화 완료")

    def _get_mood_color(self, value: float) -> str:
        """지수값에 따른 색상 반환"""
        if value <= 25:
            return self.colors['extreme_fear']
        elif value <= 45:
            return self.colors['fear']
        elif value <= 55:
            return self.colors['neutral']
        elif value <= 75:
            return self.colors['greed']
        else:
            return self.colors['extreme_greed']

    def _get_mood_text(self, value: float) -> str:
        """지수값에 따른 시장 심리 텍스트 반환"""
        if value <= 25:
            return 'Extreme Fear (극도의 공포)'
        elif value <= 45:
            return 'Fear (공포)'
        elif value <= 55:
            return 'Neutral (중립)'
        elif value <= 75:
            return 'Greed (탐욕)'
        else:
            return 'Extreme Greed (극도의 탐욕)'

    def create_market_dashboard(self) -> go.Figure:
        """종합 시장 대시보드 생성"""
        market_data = self.yahoo_collector.get_market_summary()
        fig = go.Figure()
        names, changes, colors, hover_texts = [], [], [], []
        
        for symbol, info in market_data.items():
            names.append(info['name'])
            changes.append(info['change_percent'])
            colors.append(self.colors['positive'] if info['change_percent'] > 0 else self.colors['negative'])
            hover_texts.append(f"{info['name']}<br>가격: {info['formatted_price']}<br>변동: {info['change_percent']:+.2f}%")

        fig.add_trace(go.Bar(
            x=names, y=changes, marker_color=colors,
            text=[f"{x:+.2f}%" for x in changes], textposition='auto',
            hovertext=hover_texts, hoverinfo='text'
        ))

        fig.update_layout(
            title='Market Overview', title_x=0.5,
            xaxis_title='Asset', yaxis_title='Daily Change (%)',
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            height=800, width=1200, showlegend=False,
            xaxis_tickangle=-45, margin=dict(t=100, b=100),
            xaxis=dict(gridcolor='LightGrey'),
            yaxis=dict(gridcolor='LightGrey'),
            hoverlabel=dict(bgcolor='white'),
        )

        return fig



    def create_market_tables(self) -> Dict[str, go.Figure]:
        # 벡터스페이스 저장을 위한 코드
        embedding_model = HuggingFaceEmbeddings(
            model_name='jhgan/ko-sbert-nli',
            model_kwargs={'device':'cpu'},
            encode_kwargs={'normalize_embeddings':True},
        )
        
        """카테고리별 시장 데이터 테이블 생성"""
        market_data = self.yahoo_collector.get_market_summary()
        #pprint.pprint(market_data)
        tables = {}
        categorized_data = {
            '주요지수': {}, '국채수익률': {}, '원자재': {}, '기술주': {}
        }
        # 기존 인덱스 로드
        db = FAISS.load_local("./db/faiss", embedding_model, allow_dangerous_deserialization=True)

        # 새로운 문서 추가
        for symbol, data in market_data.items():
            if symbol in self.yahoo_collector.indices:
                categorized_data['주요지수'][symbol] = data
            elif symbol in self.yahoo_collector.treasuries:
                categorized_data['국채수익률'][symbol] = data
            elif symbol in self.yahoo_collector.commodities:
                categorized_data['원자재'][symbol] = data
            elif symbol in self.yahoo_collector.tech_stocks:
                categorized_data['기술주'][symbol] = data
            # vectorSpace 저장
            print(f"종목코드 : {symbol}, 종목 이름 : {data['name']}, 변동폭 : {data['change_percent']:+.2f}%, 가격 : {data['price']}{data['unit']}, 거래량 : {data['volume']}, 기준시각 : {data['timestamp']}")

            new_docs = [Document(
                page_content=f"다음은 주식 종목과 그에 대한 정보이다. 종목코드 : {symbol}, 종목 이름 : {data['name']}, 변동폭 : {data['change_percent']:+.2f}%, 주가 : {data['price']}{data['unit']}, 거래량 : {data['volume']} 기준시각 : {data['timestamp']}"
            )]
            db.add_documents(new_docs)
        db.save_local("./db/faiss")

        for category, data in categorized_data.items():
            if data:
                headers = ['자산', '현재가', '변동폭', '거래량']
                cells = [
                    [info['name'] for info in data.values()],
                    [info['formatted_price'] for info in data.values()],
                    [f"{info['change_percent']:+.2f}%" for info in data.values()],
                    [f"{int(info['volume']):,}" if info['volume'] > 0 else 'N/A' for info in data.values()]
                ]
                
                fig = go.Figure(data=[go.Table(
                    header=dict(values=headers, fill_color='grey', align='left', font=dict(color='white', size=12)),
                    cells=dict(values=cells, fill_color='white', align='left', font=dict(color='black', size=11), height=30)
                )])
                
                fig.update_layout(title=category, title_x=0.5, width=800, margin=dict(t=50, b=20, l=20, r=20))
                tables[category] = fig
                
        return tables

    def create_fear_greed_gauge(self, save_path: str = None):
        """Fear & Greed 게이지 차트 생성"""
        data = self.cnn_collector.get_fear_greed_data()
        if not data:
            print("데이터 수집 실패")
            return None

        value = float(data['value'])
        
        plt.figure(figsize=(12, 8))
        ax = plt.subplot(projection='polar')
        
        start_angle, end_angle = np.pi/2, -np.pi/2
        theta = np.linspace(start_angle, end_angle, 100)
        ax.plot(theta, [1]*100, color='lightgray', linewidth=20, alpha=0.5)
        
        value_normalized = value / 100.0
        value_angle = start_angle - value_normalized * np.pi
        theta_value = np.linspace(start_angle, value_angle, 100)
        ax.plot(theta_value, [1]*100, color=self._get_mood_color(value), linewidth=20)
        
        ax.set_xticks([])
        ax.set_yticks([])
        
        plt.title('CNN Fear & Greed Index', pad=20, size=16, weight='bold')
        
        mood_text = self._get_mood_text(value)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        status_text = f"현재 지수: {value:.1f}\n시장 심리: {mood_text}\n측정 시각: {timestamp}"
        plt.text(0, -0.5, status_text, ha='center', va='center', transform=ax.transAxes, size=12)
        
        legend_elements = [
            plt.Line2D([0], [0], color=self.colors['extreme_fear'], lw=4, label='극도의 공포 (0-25)'),
            plt.Line2D([0], [0], color=self.colors['fear'], lw=4, label='공포 (26-45)'),
            plt.Line2D([0], [0], color=self.colors['neutral'], lw=4, label='중립 (46-55)'),
            plt.Line2D([0], [0], color=self.colors['greed'], lw=4, label='탐욕 (56-75)'),
            plt.Line2D([0], [0], color=self.colors['extreme_greed'], lw=4, label='극도의 탐욕 (76-100)')
        ]
        ax.legend(handles=legend_elements, loc='lower left', bbox_to_anchor=(0.1, -0.5))
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"차트가 저장되었습니다: {save_path}")
        
        plt.close()

    def create_half_circle_gauge(self, save_path: str = None):
        """Fear & Greed 반원형 게이지 차트 생성"""
        data = self.cnn_collector.get_fear_greed_data()
        if not data:
            print("데이터 수집 실패")
            return None

        value = float(data['value'])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_aspect('equal')
        
        theta = np.linspace(0, np.pi, 100)
        ax.plot(np.cos(theta), np.sin(theta), color='lightgray', linewidth=30, alpha=0.5, solid_capstyle='round')
        
        normalized_value = value / 100.0
        theta_value = np.linspace(0, np.pi * normalized_value, 100)
        ax.plot(np.cos(theta_value), np.sin(theta_value), color=self._get_mood_color(value), linewidth=30, solid_capstyle='round')
        
        for i in range(0, 101, 25):
            angle = np.pi * (i / 100)
            x, y = np.cos(angle), np.sin(angle)
            ax.text(x * 1.2, y * 1.2, str(i), ha='center', va='center', fontsize=12, color='black')
        
        mood_text = self._get_mood_text(value)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        status_text = f"{value}\n{mood_text}"
        ax.text(0, 0.2, status_text, ha='center', va='center', fontsize=18, weight='bold', color='black')
        
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            print(f"반원형 차트가 저장되었습니다: {save_path}")
        
        plt.close()

def main():
    """메인 실행 함수"""
    print("=== 종합 시장 데이터 시각화 시작 ===")
    visualizer = ComprehensiveMarketVisualizer()
    
    # 결과물을 저장할 디렉토리
    save_dir = "market_data"
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")

    print("\n1. 시장 대시보드 생성 중...")
    dashboard = visualizer.create_market_dashboard()
    #dashboard.show()
    # 대시보드 이미지 저장
    dashboard_path = os.path.join(save_dir, f"dashboard_{timestamp}.png")
    dashboard.write_image(dashboard_path)
    print(f"대시보드 이미지 저장 완료: {dashboard_path}")

    print("\n2. 카테고리별 테이블 생성 중...")
    tables = visualizer.create_market_tables()
    for category, table in tables.items():
        print(f"\n{category} 테이블 표시 중...")
        #table.show()
        # 테이블 이미지 저장
        table_path = os.path.join(save_dir, f"table_{category}_{timestamp}.png")
        table.write_image(table_path)
        print(f"{category} 테이블 이미지 저장 완료: {table_path}")

    print("\n3. Fear & Greed 게이지 차트 생성 중...")
    # 게이지 차트는 이미 코드 내에서 save_path를 통해 저장 중
    # 추가적으로 다른 이름으로 저장하고 싶다면 아래와 같이 가능
    save_path_gauge = os.path.join(save_dir, f"fear_greed_gauge_{timestamp}.png")
    visualizer.create_fear_greed_gauge(save_path_gauge)

    print("\n4. Fear & Greed 반원형 게이지 차트 생성 중...")
    save_path_half_circle = os.path.join(save_dir, f"half_circle_gauge_{timestamp}.png")
    visualizer.create_half_circle_gauge(save_path_half_circle)

    print("\n시각화 완료!")
    print(f"모든 이미지가 '{save_dir}' 디렉토리에 저장되었습니다.")

if __name__ == "__main__":
    main()