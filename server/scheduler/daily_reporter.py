#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from datetime import datetime

# 현재 파일의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))

# 로그 설정
log_dir = os.path.join(current_dir, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"daily_report_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("==== Daily Reporter 시작 ====")

scripts_to_run = [
    "./src/data_processing/market_data_visualization.py",
    "./src/data_processing/cnn_fear_greed_visualization.py",
    "./src/data_collection/news_api.py",
    "./server/components/summerize/pick_and_summerize.py"
]

for script in scripts_to_run:
    script_path = os.path.join(current_dir, script)
    if not os.path.exists(script_path):
        logging.error(f"파일을 찾을 수 없습니다: {script_path}")
        continue

    logging.info(f"스크립트 실행 시작: {script_path}")
    try:
        # python 실행 경로 파악
        # 필요하다면 sys.executable 대신 특정 파이썬 경로를 지정할 수 있음
        subprocess.run([sys.executable, script_path], check=True)
        logging.info(f"스크립트 실행 완료: {script_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"스크립트 실행 실패: {script_path}, 오류: {str(e)}")

logging.info("==== Daily Reporter 종료 ====")

# crontab -e 0 8 * * * /usr/bin/python3 /path/to/daliyReporter.py  으로 설정해줘야함
