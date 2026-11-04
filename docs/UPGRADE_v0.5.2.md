# AngaeBot v0.5.2 업데이트 가이드

1. Windows PowerShell에서 `cd D:\stockproj\AngaeBotBridge`.
2. `git status`로 기존 미커밋 변경 확인. 변경이 없으면 `git pull --ff-only origin main`.
3. `git log -1 --oneline` 출력에서 v0.5.2 커밋 확인.
4. `powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.2.ps1"` 실행.
5. 성공 시 Python 전체 회귀 테스트 `OK`, `AngaeBot Python Core v0.5.2 installed successfully` 확인.
6. 카카오톡에서 `앙개야 서버상태`, `앙개야 주식 메모리7`, `앙개야 주식 분석 MU`, `앙개야 주식 분석 005930`, `앙개야 주식 분석 메모리7`, `앙개야 주식 분석 미국시총10` 테스트.
7. Android APK는 그대로 사용, OpenAI API OFF 유지. 과거 시세는 장마감 기준/5분 캐시/무료 지연 정보.
8. 실패 시 배포기가 이전 소스 자동 복원. 기존 .env/SQLite/logs/그룹 데이터는 변경하지 않음.
9. 1개월/3개월 지표는 21/63거래일의 수익률과 연율화 실현변동성으로 구성. 데이터를 확보하지 못한 기간은 `데이터 부족`.
10. 임의 알림·스케줄러·카카오톡 자동 선제 발송·주식 거래 기능은 구현하지 않음.
