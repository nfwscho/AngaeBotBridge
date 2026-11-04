# 앙개봇 Android Bridge v0.4.4 — 모든 명령 답장에 S20+ 배터리 상태 표시

- 카카오톡에서 정상 처리된 명령(주식, `주`/`주 분`, 숫자 메뉴, 일반 로컬 명령, Python 처리 실패 등)에 대한 답장의 마지막 줄에 현재 S20+ 배터리 잔량과 충전 상태를 표시한다.
- 예시: `🔋 S20+ 배터리 68% · 충전 중`, 20% 이하이며 충전 중이 아닐 때 `⚠️ 충전 권장` 안내.
- Android `ACTION_BATTERY_CHANGED` sticky 브로드캐스트에서 `BatteryManager.EXTRA_LEVEL`, `EXTRA_SCALE`, `EXTRA_STATUS`를 답장 직전에 직접 조회한다.
- 배터리 정보가 유효하지 않거나 조회에 실패하면 원래 응답을 취소하지 않고 `🔋 S20+ 배터리 확인 불가`를 표시한다.
- 백그라운드 상주 측정/주기적 조회/인터넷 요청/새 Android 권한은 추가하지 않는다.
- 기존 카톡 알림/허용 방·발신자/자동응답 OFF/메뉴 5분 제한/숫자 입력/중복 방지/SQLite 로그/인증/RemoteInput/Python Core v0.5.5/AI OFF/주식 분석과 시세 기능을 그대로 보존한다.
- `REPLY_ATTEMPT` 이벤트에는 실제 전송할 배터리 포함 답장을 저장하며, 기존 `PYTHON_RESULT`의 원래 응답 내용은 보존한다.
- `versionCode=8`, `versionName=0.4.4`; 같은 서명으로 기존 앱에 `adb install -r` 가능. 앱 삭제·데이터 초기화 불필요.
- Kotlin BatteryStatusFormatter 순수 단위 테스트 6개 추가; 실제 Android 배터리 API/카카오톡 답장 작동은 S20+에서 확인 필요.
