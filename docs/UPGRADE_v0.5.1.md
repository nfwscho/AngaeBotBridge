# AngaeBot v0.5.1 — Galaxy S20+ update instructions

Existing v0.5.0 server and app must be operational. Python Core update only; no new APK, pip packages, OpenAI key or paid quote subscription.

On Windows PowerShell:

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.1.ps1"
```

The deployer uses SSH `u0_a435@10.1.1.202` port `8022`; it uploads selected source/test files, backs up originals on Termux, runs syntax and complete unittest, restarts only the FastAPI runit service after successful tests and checks authenticated health `version=0.5.1`. Source changes are rolled back when validation fails. Existing `.env`, `.venv`, SQLite DB, all logs, boot script, SSH, watchdog and Android data remain intact.

In KakaoTalk send:

```
앙개야 서버상태
앙개야 주식 프리셋 미국시총10
앙개야 주식 미국시총10
앙개야 주식 목록
```

This preset registers **ten US-incorporated companies** as of the November 4, 2026 ranking snapshot. Alphabet is a single issuer represented by GOOGL. It includes the publicly listed SpaceX ticker `SPCX`; no foreign ADR such as TSM. The group is an editable static snapshot, not a daily auto-rebalanced market-cap ranking. Each quote is still from a public, potentially delayed and unofficial service; unavailable stocks remain `조회 불가`, never invented.

A previously created group named `미국시총10` will **not** be overwritten: delete it deliberately (only if desired), or use manual add/remove. The built-in original `메모리7` always retains exactly 8 positions. Existing `반도체` and other groups persist.

For manual registration, use `앙개야 주식 그룹생성 미국시총10` followed by ten separate `앙개야 주식 추가 미국시총10 TICKER 별칭` messages **instead of** running the preset. This is not necessary when using the one-command preset.
