# update_report.sh#!/bin/bash

# 이 스크립트가 있는 디렉토리로 이동 (어디서 실행하든 경로 문제 방지)
cd "$(dirname "$0")"

# 1. 파이썬 가상환경 활성화 (만약 사용한다면)
# source /경로/to/your/venv/bin/activate

echo ">> (1/4) Generating new report..."
# 2. 파이썬 리포트 생성 스크립트 실행
# python3 대신 본인의 파이썬 실행 파일 경로를 명시하는 것이 더 안정적입니다.
python3 generate_report.py

# 3. Git에 변경사항 추가
echo ">> (2/4) Adding changes to Git..."
git add index.html

# 4. Git에 커밋 (현재 날짜와 시간으로 자동 커밋 메시지 생성)
echo ">> (3/4) Committing changes..."
git commit -m "Dashboard updated at $(date +'%Y-%m-%d %H:%M:%S')"

# 5. GitHub에 푸시
echo ">> (4/4) Pushing to GitHub..."
git push origin main

echo ">> All tasks completed successfully!"