# AngaeBot 미국 시세 복구 v0.5.10 설치·검증

Windows CMD에서 실행:

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.10.ps1"
```

`[OK] AngaeBot Python Core v0.5.10 installed successfully`와 `deployment completed`를 확인하세요. 이전 앱이나 DB를 삭제하지 마세요. Android APK는 v0.4.5 그대로 사용합니다.

카카오톡에서 `주 반도체`, `주 메모리7` 실행; 미국 시세가 재개되면 가격·등락률이 표시되며 출처 하단에 `나스닥 확정 종가` 또는 `네이버 해외 확정 종가`가 나올 수 있습니다. **이 수치는 실시간 호가가 아니라 확정 정규장 종가입니다.**

모든 미국 제공처가 실패하면 다음 명령으로 서버 진단을 확인하세요. 원본 응답/토큰은 로그에 기록하지 않습니다.

```bat
ssh -p 8022 u0_a435@10.1.1.202 "grep 'US_QUOTE_' ~/angaebot/core/logs/server.log | tail -12"
```

기존 서버 소스 백업은 `~/angaebot/backups/core_pre_v0510_*`에 보관되며 오류가 나면 자동 복원합니다. `.env`, 데이터베이스, jobs/events, Android 앱의 허용목록과 로그는 수정하지 않습니다.
