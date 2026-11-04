# 앙개봇 v0.4.3 업그레이드 (Python Core만)

1. Windows PowerShell: `cd D:\stockproj\AngaeBotBridge`
2. `git status` 후 미커밋 변경 사항이 없으면 `git pull --ff-only origin main`
3. `powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.4.3.ps1"`
4. 기대 결과: Python 전체 테스트 `OK`, `[OK] AngaeBot Python Core v0.4.3 installed successfully`.
5. S25+ 카카오톡: `앙개야 서버상태` → Python `v0.4.3`; `앙개야 주식 메모리7` → 8종목 출력.
6. 키오시아만 여전히 조회 불가라면 S20+에서 `cd ~/angaebot/core && .venv/bin/python scripts/diagnose-market.py`로 Yahoo Global/Yahoo Japan/Rakuten 원인을 구분하여 확인.

본 업데이트는 Android APK 수정 없이 SSH/S20+ Python Core만 수정합니다. 기존 `.env`, `.venv`, data/SQLite, logs, Android 앱·UI·로그·허용목록, SSH/watchdog 서비스는 보존됩니다.

무료 제공처의 접속·파싱 문제는 실기기 네트워크에서만 최종 확인할 수 있습니다. 가격을 임의로 채우지 않습니다. OpenAI API는 OFF를 유지합니다.
