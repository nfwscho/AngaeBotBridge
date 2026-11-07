"""
앙개봇 Python Core 주식 차트 PNG 렌더러 — 전체 기능과 안전 설명
1. 기존 검증된 history.fetch_history(stock)의 일별 종가만 받아 720x420 RGB PNG를 생성한다.
2. 거래일/정규장 데이터가 불충분하면 차트를 만들어내지 않고 ChartPngError를 반환한다.
3. 외부 Pillow/Matplotlib/폰트 패키지 없이 표준 라이브러리 zlib/struct만 사용해 Termux에 배포한다.
4. ASCII 5x7 픽셀 폰트로 종목 티커, 가격/기간 및 마지막 거래일을 PNG 자체에 렌더링한다.
5. 이미지 크기/데이터 길이/압축 크기를 제한하고 검증되지 않은 텍스트나 파일 경로를 입력받지 않는다.
6. 사용자 개인정보·토큰·외부 이미지를 PNG에 넣지 않으며 파일은 저장하지 않고 바이트로 반환한다.
7. 원래 주식 시세/거래 세션/캐시/기존 차트 데이터 조회, Python DB/이벤트/HTTP 명령 기능을 보존한다.
8. 인증 HTTP 응답에서만 사용할 수 있게 별도 독립 모듈로 제공하며 저장소 변경은 없다.
9. 음수/NaN/무한대, 중복/역순 날짜, 비정상 종가 등은 해당 차트만 거부한다.
"""
from __future__ import annotations

import math
import struct
import zlib

from .history import HistoryResult

WIDTH, HEIGHT = 720, 420
_FONT = {
    "A": ("01110","10001","10001","11111","10001","10001","10001"),
    "B": ("11110","10001","10001","11110","10001","10001","11110"),
    "C": ("01111","10000","10000","10000","10000","10000","01111"),
    "D": ("11110","10001","10001","10001","10001","10001","11110"),
    "E": ("11111","10000","10000","11110","10000","10000","11111"),
    "F": ("11111","10000","10000","11110","10000","10000","10000"),
    "G": ("01111","10000","10000","10111","10001","10001","01110"),
    "H": ("10001","10001","10001","11111","10001","10001","10001"),
    "I": ("11111","00100","00100","00100","00100","00100","11111"),
    "J": ("00111","00010","00010","00010","10010","10010","01100"),
    "K": ("10001","10010","10100","11000","10100","10010","10001"),
    "L": ("10000","10000","10000","10000","10000","10000","11111"),
    "M": ("10001","11011","10101","10101","10001","10001","10001"),
    "N": ("10001","11001","10101","10011","10001","10001","10001"),
    "O": ("01110","10001","10001","10001","10001","10001","01110"),
    "P": ("11110","10001","10001","11110","10000","10000","10000"),
    "Q": ("01110","10001","10001","10001","10101","10010","01101"),
    "R": ("11110","10001","10001","11110","10100","10010","10001"),
    "S": ("01111","10000","10000","01110","00001","00001","11110"),
    "T": ("11111","00100","00100","00100","00100","00100","00100"),
    "U": ("10001","10001","10001","10001","10001","10001","01110"),
    "V": ("10001","10001","10001","10001","10001","01010","00100"),
    "W": ("10001","10001","10001","10101","10101","10101","01010"),
    "X": ("10001","10001","01010","00100","01010","10001","10001"),
    "Y": ("10001","10001","01010","00100","00100","00100","00100"),
    "Z": ("11111","00001","00010","00100","01000","10000","11111"),
    "0": ("01110","10001","10011","10101","11001","10001","01110"),
    "1": ("00100","01100","00100","00100","00100","00100","01110"),
    "2": ("01110","10001","00001","00010","00100","01000","11111"),
    "3": ("11110","00001","00001","01110","00001","00001","11110"),
    "4": ("00010","00110","01010","10010","11111","00010","00010"),
    "5": ("11111","10000","10000","11110","00001","00001","11110"),
    "6": ("00111","01000","10000","11110","10001","10001","01110"),
    "7": ("11111","00001","00010","00100","01000","01000","01000"),
    "8": ("01110","10001","10001","01110","10001","10001","01110"),
    "9": ("01110","10001","10001","01111","00001","00010","11100"),
    ".": ("00000","00000","00000","00000","00000","01100","01100"),
    "-": ("00000","00000","00000","11111","00000","00000","00000"),
    ":": ("00000","01100","01100","00000","01100","01100","00000"),
    "+": ("00000","00100","00100","11111","00100","00100","00000"),
    "/": ("00001","00001","00010","00100","01000","10000","10000"),
    " ": ("00000",)*7,
}


class ChartPngError(ValueError):
    """이미지 생성/데이터 품질 문제만 해당 요청에서 거부한다."""


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
        ">I", zlib.crc32(kind + payload) & 0xffffffff)


def _set_pixel(canvas: bytearray, x: int, y: int, rgb: tuple[int, int, int]) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        canvas[i:i+3] = bytes(rgb)


def _line(canvas: bytearray, x1: int, y1: int, x2: int, y2: int,
          rgb: tuple[int, int, int]) -> None:
    dx, dy = abs(x2-x1), -abs(y2-y1)
    sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
    err = dx+dy
    while True:
        _set_pixel(canvas, x1, y1, rgb)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2*err
        if e2 >= dy:
            err += dy
            x1 += sx
        if e2 <= dx:
            err += dx
            y1 += sy


def _text(canvas: bytearray, x: int, y: int, value: str, color: tuple[int, int, int],
          scale: int = 2) -> None:
    for char in value.upper()[:80]:
        glyph = _FONT.get(char, _FONT[" "])
        for yy, row in enumerate(glyph):
            for xx, bit in enumerate(row):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            _set_pixel(canvas, x + xx*scale + sx, y + yy*scale + sy, color)
        x += 6*scale


def render_history_png(history: HistoryResult) -> bytes:
    """실제 마감 일봉 종가의 최근 최대 30거래일을 그려 PNG RGB 바이트로 반환."""
    bars = tuple(history.bars[-30:])
    if len(bars) < 2:
        raise ChartPngError("차트를 그릴 마감 일봉이 두 개 이상 필요합니다.")
    if any(not math.isfinite(b.close) or b.close <= 0 for b in bars):
        raise ChartPngError("검증되지 않은 종가가 포함되어 있습니다.")
    if any(a.date >= b.date for a, b in zip(bars, bars[1:])):
        raise ChartPngError("거래일 날짜 순서가 잘못되었습니다.")
    ticker = history.stock.ticker.upper()
    if len(ticker) > 16 or any(c not in _FONT or c == " " for c in ticker):
        raise ChartPngError("차트 제목에 사용할 종목코드가 올바르지 않습니다.")
    navy, panel, grid, white, cyan, gold = (
        (17, 38, 57), (25, 53, 75), (52, 80, 99),
        (239, 247, 251), (69, 212, 224), (255, 209, 101))
    pixels = bytearray(bytes(navy) * WIDTH * HEIGHT)
    for y in range(100, 351):
        a=(y*WIDTH+52)*3
        pixels[a:a+(WIDTH-100)*3] = bytes(panel)*(WIDTH-100)
    _text(pixels, 45, 27, "ANGAE STOCK CHART", white, 3)
    _text(pixels, 45, 72, ticker, gold, 2)
    prices = [b.close for b in bars]
    lo, hi = min(prices), max(prices)
    margin = max((hi-lo)*0.12, hi*0.012)
    lo=max(0.,lo-margin)
    hi+=margin
    left, right, top, bottom=68, 630, 116, 329
    for k in range(5):
        y=top+round((bottom-top)*k/4)
        _line(pixels,left,y,right,y,grid)
    _line(pixels,left,top,left,bottom,white)
    _line(pixels,left,bottom,right,bottom,white)
    def pt(i:int,p:float)->tuple[int,int]:
        return (left+round((right-left)*i/(len(prices)-1)),
                bottom-round((p-lo)/(hi-lo)*(bottom-top)))
    last=pt(0, prices[0])
    for i,p in enumerate(prices[1:],start=1):
        now=pt(i,p)
        _line(pixels,*last,*now,cyan)
        last=now
    for dx in range(-3,4):
        for dy in range(-3,4):
            if dx*dx+dy*dy<=9:
                _set_pixel(pixels,last[0]+dx,last[1]+dy,gold)
    _text(pixels,75,351,"FROM "+bars[0].date.isoformat(),white,2)
    _text(pixels,425,351,"TO "+bars[-1].date.isoformat(),white,2)
    _text(pixels,75,384,"LAST "+format(prices[-1],".2f"),gold,2)
    _text(pixels,430,384,"DAILY CLOSE",white,2)
    raw=b"".join(b"\x00"+pixels[y*WIDTH*3:(y+1)*WIDTH*3]
                 for y in range(HEIGHT))
    compressed=zlib.compress(raw,6)
    ihdr=struct.pack(">IIBBBBB",WIDTH,HEIGHT,8,2,0,0,0)
    result=b"\x89PNG\r\n\x1a\n"+_chunk(b"IHDR",ihdr)+_chunk(b"IDAT",compressed)+_chunk(b"IEND",b"")
    if len(result)>1_200_000:
        raise ChartPngError("차트 이미지가 크기 제한을 넘었습니다.")
    return result
