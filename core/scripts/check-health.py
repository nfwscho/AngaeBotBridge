"""앙개봇 v0.2.1 인증 상태 조회: 로컬 health API만 호출. 기존 기능/로그/DB 변경 없음."""
from __future__ import annotations
from health_watchdog import token_from_env, health_ok
if __name__ == '__main__':
    print('HEALTH_OK' if health_ok(token_from_env()) else 'HEALTH_UNAVAILABLE')
