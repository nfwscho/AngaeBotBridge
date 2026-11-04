"""
앙개봇 v0.4.3 Python 명령 엔진 — 전체 기능 상세 안내
1. Galaxy S20+의 Termux에서 FastAPI로 전달된 허용 명령만 실행한다.
2. '계산': Python eval 없이 제한된 AST로 +,-,*,/,//,%,** 및 괄호를 계산한다.
3. 과도한 입력, 큰 숫자, 깊은 트리, 지수 폭증, 0으로 나누기를 거부한다.
4. '시간': 서울 시간(UTC+09:00)을 반환한다. 외부 네트워크가 필요 없다.
5. '서버상태': Python 엔진이 정상 실행 중인지 간략히 답한다.
6. 파일/PC 제어, 임의 명령 실행, 외부 접속, 주식 주문은 지원하지 않는다.
7. 기존 Android의 테스트/상태/도움말 및 카카오톡 응답/SQLite 로그는 변경하지 않는다.
8. AI 질문/요약/AI상태/대화초기화는 별도 ai_engine 및 FastAPI에서 처리한다.
9. 임의 셸/원격 PC 접근 없이 기존 수치 제한 및 시간 명령을 유지한다.
10. v0.3.1 운영 업데이트에서도 계산 결과/오류 메시지/로그 구조는 변경하지 않고 서버 상태 버전만 변경한다.
11. v0.4.0 운영 명령은 별도 ops.py에서 처리하며 계산·시간의 모든 동작은 유지한다.
12. v0.4.1 시세 명령은 별도 market.py로 추가하고 기존 계산/시간 응답을 유지한다.
13. v0.4.3 메모리7 국내·일본 공급자 보완 및 기존 계산/시간 명령 결과를 유지한다.
"""
from __future__ import annotations

import ast
import math
import operator
from datetime import datetime, timezone, timedelta

MAX_ABS = 1_000_000_000_000_000  # intermediate and final numeric bound
MAX_LENGTH = 100
MAX_DEPTH = 18
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


class CommandError(ValueError):
    pass


def safe_calculate(expression: str) -> str:
    expr = expression.strip()
    if not expr or len(expr) > MAX_LENGTH:
        raise CommandError("계산식은 1~100자로 입력하세요.")
    try:
        root = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise CommandError("계산식 문법이 올바르지 않습니다.") from exc

    def walk(node: ast.AST, depth: int = 0) -> int | float:
        if depth > MAX_DEPTH:
            raise CommandError("계산식이 너무 복잡합니다.")
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            x = walk(node.operand, depth + 1)
            value = -x if isinstance(node.op, ast.USub) else +x
        elif isinstance(node, ast.BinOp):
            left = walk(node.left, depth + 1)
            right = walk(node.right, depth + 1)
            if isinstance(node.op, ast.Pow):
                if abs(right) > 8 or abs(left) > 1_000_000:
                    raise CommandError("지수 계산 범위를 초과했습니다.")
                if left == 0 and right < 0:
                    raise CommandError("0을 음수 지수로 계산할 수 없습니다.")
                value = left ** right
            elif type(node.op) in OPS:
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
                    raise CommandError("0으로 나눌 수 없습니다.")
                value = OPS[type(node.op)](left, right)
            else:
                raise CommandError("지원하지 않는 연산자입니다.")
        else:
            raise CommandError("숫자와 기본 산술 연산자만 사용할 수 있습니다.")
        if isinstance(value, complex) or not math.isfinite(value) or abs(value) > MAX_ABS:
            raise CommandError("계산 허용 범위를 초과했습니다.")
        return value

    try:
        val = walk(root)
    except (OverflowError, ZeroDivisionError, ValueError) as exc:
        if isinstance(exc, CommandError):
            raise
        raise CommandError("계산 허용 범위를 초과했습니다.") from exc
    if isinstance(val, float):
        formatted = str(int(val)) if val.is_integer() else f"{val:,.10g}"
    else:
        formatted = f"{val:,}"
    return f"🧮 계산 결과: {formatted}"


def execute_command(name: str, argument: str, uptime_seconds: int) -> str:
    if name == "계산":
        return safe_calculate(argument)
    if name == "시간":
        now = datetime.now(timezone(timedelta(hours=9)))
        return "🕐 서울 현재 시각: " + now.strftime("%Y-%m-%d %H:%M:%S KST")
    if name == "서버상태":
        return f"🐍 앙개봇 Python v0.4.3 정상 실행 중\n실행 위치: Galaxy S20+ / Termux\n가동 시간: {uptime_seconds}초"
    raise CommandError("허용되지 않은 Python 명령입니다.")
