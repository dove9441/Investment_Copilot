#!/usr/bin/env bash

# 1. uvicorn 서버 종료
echo "Uvicorn 서버 종료 중..."
pkill -f "uvicorn server.main:app --reload"

# 2. daliyReporter.py 실행
echo "daliyReporter.py 실행 중..."
python daliyReporter.py

# 3. uvicorn 서버 재시작
echo "Uvicorn 서버 재시작 중..."
uvicorn server.main:app --reload