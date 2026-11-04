# v0.5.1 US top-ten stock group verification

1. Check previous `앙개야 계산 344*454` = 156,176, `서버상태` = v0.5.1, `주식 메모리7` still lists eight symbols.
2. Use `주식 프리셋 미국시총10` and confirm exactly ten symbols NVDA/AAPL/MSFT/GOOGL/AMZN/SPCX/AVGO/META/TSLA/LLY, and `주식 목록` shows ten.
3. Use `주식 미국시총10`, and confirm price/date source, exchange timezone, no fabricated quote when provider fails, and reply time within Android's stock 23s read timeout.
4. Try duplicate preset and confirm it fails safely and does not overwrite existing ten members.
5. Try adding eleventh stock and confirm explicit maximum-ten rejection.
6. Verify previously created `반도체` group and immutable `메모리7` are intact.
7. Verify API authentication, duplicate request-id semantics, room/sender isolation and logs via unit/integration tests.
8. Verify `.env` token/SQLite data/Android UI/runit SSH-watchdog/previous logs unaffected by deployment.
9. No AI API call, automated trading, or autonomous sending of KakaoTalk messages.
10. Live remote quote responses and Google Play Termux reboot recovery must be verified on user device separately.
