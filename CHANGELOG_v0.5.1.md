# AngaeBot v0.5.1 — US market-cap Top 10 watchlist group preset

## Preserved functionality
- All original KakaoTalk notification listening, sender/room authorization, RemoteInput, app UI, Android SQLite logs remain unchanged.
- Python FastAPI local-only binding `127.0.0.1:8765`, authentication, request-id idempotency, jobs/events logs and AI disabled-by-default are unchanged.
- Memory7's eight original symbols and their Naver/Yahoo/Yahoo Japan/Rakuten quote fallbacks remain unchanged.
- All user-created existing groups and items remain in `stock_groups`/`stock_items`; .env, database, logs and backup files are never deleted.
- Existing manual group CRUD, group lookup, and operations commands continue to work.

## New function
- Maximum stocks per user-managed group changed from 8 to **10** (maximum 10 groups per room/sender unchanged).
- `앙개야 주식 프리셋 미국시총10`: creates `미국시총10` with NVDA, AAPL, MSFT, GOOGL, AMZN, SPCX, AVGO, META, TSLA, LLY in one request.
- `앙개야 주식 미국시총10`: retrieves existing group quotes using the existing public/unofficial quote provider, with no OpenAI or paid API.
- Fixed constituent snapshot **2026-11-04** of U.S.-incorporated public companies; one share class per company (Alphabet represented by GOOGL). The stock list **does not automatically rebalance** as market-cap rankings change.
- An existing group is never overwritten by the preset. Users can still add/remove tickers manually up to 10.
- At most 5 workers for existing group quote lookup to keep 10-stock response within the Android's established stock timeout; failures continue to show `조회 불가` without fabricated values.
- Existing `CORE_START` log marker is now correctly marked v0.5.1 (other logs unchanged).

## Ranking reference
- `https://www.finhacker.cz/en/largest-us-companies-by-market-cap/` (Nov 3, 2026 US companies)
- `https://stockanalysis.com/list/largest-us-companies/` (2026-11-04 nearby ranking)
- Market caps can fluctuate daily; this is a watchlist snapshot, not an up-to-the-minute ranking.

## Verification
- Python unittest suite: 111 tests pass locally (real Galaxy S20+ deployment pending).
- No Android build needed: existing Android Bridge already forwards the `주식` command and supports stock read timeout.
- Use `scripts/deploy-v0.5.1.ps1` after `git pull`. Never run the old `deploy-v0.5.0.ps1` for the new version.
