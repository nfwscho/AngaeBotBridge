# AngaeBot v0.5.7 설치 안내 — Android APK 재설치 불필요

Windows CMD(`D:\stockproj\AngaeBotBridge`)에서 다음 순서로 실행하세요.

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.7.ps1"
```

정상 설치되면 `[OK] AngaeBot Python Core v0.5.7 installed successfully`를 확인합니다.

카카오톡에서 `앙개야 서버상태` (0.5.7), `주 메모리7` (한국 KRX 시각/지연·장전/장후), `3` (마이크론 기존 분석 유지), `주 분 삼성전자`를 시험하세요.

기존 Android Bridge v0.4.5/배터리 표시/숫자 선택에는 변화가 없습니다. APK 삭제·재설치·데이터 초기화 금지.
실제 한국 본장 장중에 KRX 체결시각과 시세 갱신 여부를 확인해야 '실시간표시(지연 0분)'가 표시됩니다.
마감 후에는 `장마감 종가`가 정상이며, 시간외 세션은 API 응답에 시세가 있을 때만 별도 표시됩니다.
네이버 폴링 API의 문서화·서비스 수준 보장은 없습니다.
