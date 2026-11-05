# 앙개봇 미국 주식 시세 장애 보완 v0.5.8 — 설치 및 점검

## 1. Windows CMD 실행
```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.8.ps1"
```
배포 성공: `[OK] AngaeBot Python Core v0.5.8 installed successfully` / `deployment completed`.
기존 Termux 서버·.env·DB·로그/Android APK는 유지된다. **APK 재빌드/삭제/재설치는 금지**.

## 2. 카카오톡 시험
- `주 메모리7` → 미국 5종목 중 적어도 일부의 가격 및 공급자 확인
- `주 반도체` → 마이크론·샌디스크·웬디·씨게이트 확인
- `주 메모리7` → `3` → 마이크론 분석(단 과거 시세 공급자도 별도 장애 가능)
- `앙개야 상태`, `주`, `주 분 삼성전자` → 기존 기능 정상 여부
- `🔋 S20+` 잔량 표시 유지

미국 Yahoo가 정상인 경우 종전 미국 시세 한 줄을 유지한다. Yahoo가 실패하고 나스닥 웹 시세가 검증을 통과한 경우 다음과 같은 별도 정보를 표시한다.
```text
3. 마이크론 : $... (...%)
   └ 미국 11/04 16:00 ET · 나스닥 공개 시세(지연 여부 미확인)
```
이 문구가 보이면 Nasdaq 보조 데이터가 사용된 것이다. 실제 숫자·시각은 공급자가 제공해야 하며, 임의로 보충하지 않는다.

## 3. 계속 조회 불가일 때
Yahoo와 Nasdaq 웹이 모두 S20+ Termux에서 HTTP 403/429를 반환하거나 데이터 형식/거래시각이 불완전하면 안전하게 `조회 불가`가 유지된다.
이때 Termux 서버 콘솔/로그의 `US_QUOTE_FAILED` 진단 행에서 미국 티커별 `Yahoo HTTP 429`, `나스닥 HTTP 403` 등 응답 분류를 확인해 추가 공급자를 선택한다. 해당 로그에는 계정 인증키가 없다.
개인 테스트 이외의 재배포/상업적 사용 시 각 공급자의 시세 라이선스를 확인해야 한다.
