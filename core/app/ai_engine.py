"""
앙개봇 Python Core v0.3.0 — AI 제공자 통합 모듈 전체 기능 상세 설명
1. 기존 계산·시간·서버상태 FastAPI 요청과 SQLite DB 구조를 변경하지 않는 독립 AI 계층이다.
2. AI는 ANGAE_AI_ENABLED=1로 명시적으로 활성화한 경우에만 외부로 요청을 전송한다.
3. OpenAI 또는 Ollama의 공통 /v1/chat/completions HTTP 인터페이스를 사용한다.
4. OpenAI API 인증키는 환경변수로만 전달하고 응답·로그·SQLite에 저장하지 않는다.
5. Ollama 로컬/LAN 연결은 사설 IP/loopback HTTP만 허용하고 외부 공개 API는 HTTPS만 허용한다.
6. 사용자 질문과 제한된 최근 대화 문맥을 전송하고, 결과 길이를 카카오톡 답장에 맞춰 제한한다.
7. AI 응답 지연/429/인증 실패/연결 실패는 구분된 안전한 오류로 돌려주고 다른 명령은 유지한다.
8. 임의 셸 실행·파일 조작·개인정보 조회·도구 호출/함수 실행 권한은 제공하지 않는다.
9. Python 표준 라이브러리 urllib만 사용하므로 Termux에 새 바이너리 의존성이 필요 없다.
10. 제공자 설정값과 타임아웃을 검증하며 테스트용 HTTP 전송 함수를 주입할 수 있다.
"""
from __future__ import annotations

import ipaddress
import json
import os
import socket
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


class AIError(ValueError):
    """사용자에게 비밀정보 없이 노출 가능한 AI 처리 실패."""


@dataclass(frozen=True)
class AISettings:
    enabled: bool
    provider: str
    base_url: str
    model: str
    api_key: str
    timeout: int
    memory_enabled: bool
    context_turns: int

    @classmethod
    def from_env(cls) -> "AISettings":
        provider = os.environ.get("ANGAE_AI_PROVIDER", "openai").strip().lower()
        default_base = "https://api.openai.com/v1" if provider == "openai" else "http://127.0.0.1:11434/v1"
        return cls(
            enabled=os.environ.get("ANGAE_AI_ENABLED", "0") == "1",
            provider=provider,
            base_url=os.environ.get("ANGAE_AI_BASE_URL", default_base).strip(),
            model=os.environ.get("ANGAE_AI_MODEL", "").strip(),
            api_key=os.environ.get("ANGAE_AI_API_KEY", "").strip(),
            timeout=int(os.environ.get("ANGAE_AI_TIMEOUT", "15")),
            memory_enabled=os.environ.get("ANGAE_AI_MEMORY_ENABLED", "1") == "1",
            context_turns=int(os.environ.get("ANGAE_AI_CONTEXT_TURNS", "6")),
        )

    def status_text(self) -> str:
        if not self.enabled:
            return "🤖 AI 대화 기능: OFF\nTermux에서 scripts/configure-ai.py로 활성화하세요.\n기존 계산·시간 명령은 계속 사용 가능합니다."
        return (f"🤖 AI 대화 기능: ON\n제공자: {self.provider}\n"
                f"모델: {self.model or '(미설정)'}\n대화 문맥: {'ON' if self.memory_enabled else 'OFF'}")

    def endpoint(self) -> str:
        if self.provider not in {"openai", "ollama"}:
            raise AIError("AI 제공자는 openai 또는 ollama만 사용할 수 있습니다.")
        if not self.model or len(self.model) > 120:
            raise AIError("AI 모델명이 설정되지 않았습니다.")
        if self.provider == "openai" and not self.api_key:
            raise AIError("OpenAI API 키가 없습니다. Termux AI 설정을 확인하세요.")
        if not 3 <= self.timeout <= 23:
            raise AIError("AI 응답 제한 시간은 3~23초로 설정하세요.")
        if not 0 <= self.context_turns <= 10:
            raise AIError("AI 대화 문맥은 0~10회로 설정하세요.")
        parts = urlsplit(self.base_url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise AIError("AI 서버 주소가 올바르지 않습니다.")
        if parts.scheme == "http":
            host = parts.hostname
            try:
                address = ipaddress.ip_address(host)
                local = address.is_loopback or (isinstance(address, ipaddress.IPv4Address) and any(
                    address in network for network in (ipaddress.ip_network("10.0.0.0/8"),
                    ipaddress.ip_network("172.16.0.0/12"), ipaddress.ip_network("192.168.0.0/16"))))
            except ValueError:
                local = host == "localhost"
            if not local or self.provider != "ollama":
                raise AIError("HTTP 주소는 Ollama의 사설 네트워크에서만 허용합니다. 외부 API는 HTTPS를 사용하세요.")
        # 공급자 URL은 운영자가 정하는 고정 설정이며 입력 메시지로 변경할 수 없다.
        path = parts.path.rstrip("/")
        if not path.endswith("/v1"):
            raise AIError("AI 서버 주소는 /v1로 끝나야 합니다.")
        return urlunsplit((parts.scheme, parts.netloc, path + "/chat/completions", "", ""))


SYSTEM_PROMPT = (
    "당신은 개인용 카카오톡 비서 앙개봇입니다. 한국어로 정확하고 간결하게 답하세요. "
    "확인하지 못한 최신 뉴스·주가·사실은 실시간 조회가 없다고 명시하세요. "
    "외부 기기를 조작하거나 메시지를 별도로 전송할 수 있다고 주장하지 마세요. "
    "답변은 가능한 900자 이내로 작성하고, 민감정보를 요청하지 마세요."
)


def get_ai_reply(settings: AISettings, question: str, *, history: list[tuple[str, str]] | None = None,
                 summarize: bool = False,
                 sender: Callable[..., object] | None = None) -> str:
    """호환 HTTP 서버에 요청. 테스트 시 sender(request, timeout=)를 주입한다."""
    if not settings.enabled:
        raise AIError("AI 기능이 OFF입니다. Termux에서 AI를 설정하고 활성화하세요.")
    prompt = question.strip()
    if not prompt or len(prompt) > 1000:
        raise AIError("질문·요약할 내용을 1~1000자로 입력하세요.")
    endpoint = settings.endpoint()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if not summarize:
        for user_text, assistant_text in (history or [])[-settings.context_turns:] if settings.context_turns else []:
            messages.extend([{"role": "user", "content": user_text[:1000]},
                             {"role": "assistant", "content": assistant_text[:1200]}])
    if summarize:
        prompt = "다음 문장을 핵심 내용 중심으로 요약해 주세요. 원문의 사실을 추가하지 마세요.\n\n" + prompt
    messages.append({"role": "user", "content": prompt})
    body = {"model": settings.model, "messages": messages, "stream": False}
    if settings.provider == "openai":
        # OpenAI API는 max_completion_tokens를 권장하며 Luna는 reasoning_effort=none을 지원한다.
        body["max_completion_tokens"] = 650
        if settings.model == "gpt-6-luna":
            body["reasoning_effort"] = "none"  # 빠른 카카오톡 회신에 적합한 설정
    else:
        # Ollama의 Chat Completions 호환 API에서 널리 지원하는 필드.
        body["max_tokens"] = 650
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"}
    if settings.provider == "openai":
        headers["Authorization"] = "Bearer " + settings.api_key
    req = Request(endpoint, data=payload, headers=headers, method="POST")
    send = sender or urlopen
    try:
        with send(req, timeout=settings.timeout) as resp:
            raw = resp.read(128_001)
        if len(raw) > 128_000:
            raise AIError("AI 서버 응답 크기가 너무 큽니다.")
        obj = json.loads(raw)
        answer = obj["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise AIError("AI 서버가 답변을 반환하지 않았습니다.")
        return answer.strip()[:1200]
    except HTTPError as error:
        if error.code in (401, 403):
            raise AIError("AI 인증 또는 모델 접근 권한을 확인하세요.") from error
        if error.code == 429:
            raise AIError("AI 서비스 요청 한도에 도달했습니다. 잠시 후 다시 시도하세요.") from error
        raise AIError(f"AI 서비스 HTTP 오류: {error.code}") from error
    except (TimeoutError, socket.timeout) as error:
        raise AIError("AI 응답 시간 초과. 나중에 다시 시도하세요.") from error
    except (URLError, OSError) as error:
        raise AIError("AI 서버 연결 실패. 네트워크와 모델 실행 상태를 확인하세요.") from error
    except (ValueError, KeyError, IndexError, TypeError) as error:
        if isinstance(error, AIError):
            raise
        raise AIError("AI 서버 응답 형식이 올바르지 않습니다.") from error
