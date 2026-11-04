#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.2.1 이전 명령 호환: 전체 기능 상세 안내
# 1. 기존 v0.2.0의 setup-boot.sh 실행 경로를 그대로 유지한다.
# 2. 별도 서비스 설치기를 실행하여 부팅 및 재시작 기능을 구성한다.
# 3. 기존 .env/SQLite DB/로그/Android UI와 설정은 보존한다.
set -euo pipefail
cd "$(dirname "$0")/.."
exec bash scripts/install-autostart.sh
