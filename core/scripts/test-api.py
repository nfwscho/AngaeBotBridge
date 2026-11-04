"""앙개봇 v0.2.0 Core: S20+ 내부 loopback 서버 /v1/health 와 계산 명령을 확인하는 도구."""
import json
import os
import secrets
from urllib.request import Request, urlopen

TOKEN = os.environ.get('ANGAE_TOKEN', '')
if not TOKEN:
    from pathlib import Path
    content = Path('.env').read_text().strip().split('=', 1)
    TOKEN = content[1]

base = 'http://127.0.0.1:8765'
for path, data in (
    ('/v1/health', None),
    ('/v1/commands', {'request_id': secrets.token_hex(16), 'command': '계산', 'argument': '123*456'}),
):
    payload = json.dumps(data).encode() if data else None
    req = Request(base + path, data=payload, headers={'X-AngaeBot-Token': TOKEN, 'Content-Type': 'application/json'})
    with urlopen(req, timeout=4) as result:
        print(path, result.read().decode())
