# AngaeBot v0.5.3 — 한글 종목명 분석 업데이트

1. Windows PowerShell: `cd D:\stockproj\AngaeBotBridge`.
2. `git status`로 변경 사항을 확인하고 깨끗한 상태이면 `git pull --ff-only origin main`.
3. `powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.3.ps1"` 실행.
4. Termux가 시장 시간대를 확인하고 누락 시에만 tzdata를 설치. 실패하면 Core 소스 적용/재시작 전에 중단.
5. Python 전체 128건 회귀 테스트와 API health v0.5.3 확인. 문제 생기면 이전 소스 자동 복원.
6. 카카오톡: `앙개야 서버상태`, `앙개야 주식 분석 마이크론`, `앙개야 주식 분석 삼성전자`, `앙개야 주식 분석 하이닉스`.
7. 미국 이름도 가능: `앙개야 주식 분석 엔비디아`, `앙개야 주식 분석 애플`, `앙개야 주식 분석 구글`.
8. 등록 별칭 `앙개야 주식 추가 투자 NVDA 내GPU`는 `앙개야 주식 분석 내GPU`로 조회 가능.
9. 원래 티커 입력·메모리7/반도체/미국시총10은 그대로 지원하며 Android APK를 다시 설치할 필요 없음.
10. DB·로그·토큰·AI OFF는 유지. 주식 알림·자동 발송·스케줄러는 생성하지 않음.

## v0.5.3 배포 검증 핫픽스
- 2026-11-05 재시작 직후 구버전 `0.5.2`를 요구하던 검사를 `0.5.3`으로 수정했다.
- Windows에서 `git pull --ff-only origin main`으로 핫픽스를 받고 기존 `scripts/deploy-v0.5.3.ps1`을 다시 실행한다.
- Python 회귀 테스트 통과 후 `[OK] AngaeBot Python Core v0.5.3 installed successfully`가 출력되는지 확인한다.
- 기존 DB·로그·고객별 그룹은 삭제하지 않는다. `ResourceWarning`만 발생할 때는 별도 정리 대상으로 분류한다.
