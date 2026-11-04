# AngaeBot Python Core v0.5.4 배포 안내

Windows PowerShell:
1. cd D:\stockproj\AngaeBotBridge
2. git status
3. git pull --ff-only origin main
4. git log -1 --oneline
5. powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.4.ps1"

성공 기준: Ran 129 tests / OK / AngaeBot Python Core v0.5.4 installed successfully.
배포 전 시간대 데이터 검증, 원본 백업, 전체 회귀 테스트 및 인증된 /v1/health의 버전 확인.
오류 시 안전 복원. Android APK, 모든 서버 로그, SQLite 작업 기록, stock_groups, 사용자 그룹과 AI OFF 유지.
카카오톡 확인: 앙개야 서버상태 / 앙개야 주식 목록 / 앙개야 주식 분석 마이크론 / 앙개야 주식 분석 하이닉스.
가격 알림·자동 발신·자동 매매·OpenAI API 추가 없음.
