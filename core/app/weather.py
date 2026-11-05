"""
앙개봇 날씨 기능 모듈 — 제공 기능 및 기존 동작 보존
1. 무료 Open-Meteo 예보 API로 오늘의 현재 기온·체감온도·습도·풍속·날씨, 최고/최저 기온, 강수확률을 조회한다.
2. 내일 날씨와 향후 7일의 한국시간(Asia/Seoul) 일별 예보를 간결한 카카오톡 텍스트로 변환한다.
3. WMO 날씨 코드를 한국어 날씨 상태 및 이모지로 번역하고 응답에 모델 예보 출처를 표시한다.
4. 사용자가 명시적으로 지정한 지역만 Open-Meteo 지오코딩 API로 검색하며 기본 지역은 서울로 안내한다.
5. 채팅방·발신자별 지역 설정은 별도 SQLite weather_locations 테이블에 저장하여 서버 재시작 후에도 유지한다.
6. 지오코딩 검색 결과는 한국 내 좌표로 제한하고 입력 길이/문자 및 외부 URL을 검증한다.
7. 요청별 네트워크 타임아웃 및 공급자 JSON 검증을 적용하며 실패 시 예보 수치를 추측하지 않는다.
8. API 키·AI 모델·별도 바이너리·위치 권한을 사용하지 않으며 외부 서비스 호출은 조회 시에만 수행한다.
9. 기존 jobs/events/stock/records/ai 테이블과 로그, Android UI/배터리, 5분 메뉴·인증·중복제거를 변경하지 않는다.
10. 개인정보인 방·발신자 및 인증 토큰을 외부 API로 전달하지 않고 지역 이름 또는 좌표만 사용한다.
11. 테스트는 네트워크를 모의 처리하며 날씨 미확인 값은 대시(-)로 표기해 허위 정보를 만들지 않는다.
"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
KOREA_TIMEZONE = "Asia/Seoul"
DEFAULT_LOCATION = ("서울 (기본)", 37.5665, 126.9780)
CITY_COORDINATES = {
    "서울": (37.5665, 126.9780), "서울특별시": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756), "부산광역시": (35.1796, 129.0756),
    "인천": (37.4563, 126.7052), "대구": (35.8714, 128.6014),
    "대전": (36.3504, 127.3845), "광주": (35.1595, 126.8526),
    "울산": (35.5384, 129.3114), "세종": (36.4800, 127.2890),
    "제주": (33.4996, 126.5312), "제주시": (33.4996, 126.5312),
    "서귀포": (33.2541, 126.5601), "수원": (37.2636, 127.0286),
    "춘천": (37.8813, 127.7298), "강릉": (37.7519, 128.8761),
    "전주": (35.8242, 127.1480), "청주": (36.6424, 127.4890),
    "천안": (36.8151, 127.1139), "창원": (35.2279, 128.6811),
    "포항": (36.0190, 129.3435),
}
WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


class WeatherError(Exception):
    """정확한 날씨/지역 데이터가 없어 처리할 수 없는 요청."""


@dataclass(frozen=True)
class WeatherLocation:
    name: str
    latitude: float
    longitude: float


def init_weather_schema(db: sqlite3.Connection) -> None:
    """기존 테이블이나 로그를 변경하지 않고 날씨 지역 전용 테이블만 생성."""
    db.execute("""CREATE TABLE IF NOT EXISTS weather_locations (
        room TEXT NOT NULL, sender TEXT NOT NULL, name TEXT NOT NULL,
        latitude REAL NOT NULL, longitude REAL NOT NULL, updated_at INTEGER NOT NULL,
        PRIMARY KEY (room, sender))""")


def get_location(db: sqlite3.Connection, room: str, sender: str) -> WeatherLocation:
    if not room.strip() or not sender.strip():
        raise WeatherError("채팅방과 발신자가 확인된 경우에만 날씨를 조회할 수 있습니다.")
    row = db.execute(
        "SELECT name, latitude, longitude FROM weather_locations WHERE room=? AND sender=?",
        (room, sender),
    ).fetchone()
    return WeatherLocation(*row) if row else WeatherLocation(*DEFAULT_LOCATION)


def save_location(db: sqlite3.Connection, room: str, sender: str, loc: WeatherLocation) -> None:
    if not room.strip() or not sender.strip():
        raise WeatherError("지역 저장에는 채팅방과 발신자 정보가 필요합니다.")
    db.execute("""INSERT INTO weather_locations(room, sender, name, latitude, longitude, updated_at)
        VALUES(?,?,?,?,?,strftime('%s','now'))
        ON CONFLICT(room, sender) DO UPDATE SET
        name=excluded.name, latitude=excluded.latitude,
        longitude=excluded.longitude, updated_at=excluded.updated_at""",
        (room, sender, loc.name, loc.latitude, loc.longitude))


def _get_json(endpoint: str, params: dict) -> dict:
    url = endpoint + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "AngaeBotBridge-weather/1.0"})
    try:
        with urlopen(request, timeout=4.0) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        raise WeatherError("날씨 제공 서버에 연결할 수 없습니다. 잠시 후 다시 조회하세요.") from error
    if not isinstance(result, dict) or result.get("error"):
        raise WeatherError("날씨 제공 서버가 요청을 처리하지 못했습니다.")
    return result


def resolve_location(query: str) -> WeatherLocation:
    """서울 등 주요 도시를 바로 처리하고 그 밖의 한국 지역은 지오코딩으로 확인."""
    name = " ".join(query.split())
    if not (2 <= len(name) <= 40) or not re.fullmatch(r"[가-힣A-Za-z0-9\s·.,-]+", name):
        raise WeatherError("지역은 2~40자 지명으로 입력하세요. 예: 날 지역 서울, 날 지역 강남구")
    if name in CITY_COORDINATES:
        lat, lon = CITY_COORDINATES[name]
        return WeatherLocation(name, lat, lon)
    # '서울 강남구'처럼 행정구역을 함께 쓴 경우 마지막 지명을 우선 검색한다.
    search = name.split()[-1]
    result = _get_json(GEO_URL, {
        "name": search, "count": 10, "language": "ko", "countryCode": "KR"
    })
    places = result.get("results") or []
    if not isinstance(places, list):
        raise WeatherError("지역 검색 결과를 확인할 수 없습니다.")
    for row in places:
        if not isinstance(row, dict) or row.get("country_code") != "KR":
            continue
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
        except (ValueError, KeyError, TypeError):
            continue
        if 32.0 <= lat <= 39.5 and 124.0 <= lon <= 132.0:
            return WeatherLocation(name, lat, lon)
    raise WeatherError("해당 국내 지역을 찾지 못했습니다. 시·군·구 이름을 확인하세요.")


def _weather_label(value) -> str:
    try:
        code = int(value)
    except (ValueError, TypeError):
        return "정보 없음"
    if code == 0:
        return "☀️ 맑음"
    if code in (1, 2):
        return "🌤 대체로 맑음"
    if code == 3:
        return "☁️ 흐림"
    if code in (45, 48):
        return "🌫 안개"
    if code in (51, 53, 55, 56, 57):
        return "🌦 이슬비"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "🌧 비"
    if code in (71, 73, 75, 77, 85, 86):
        return "❄️ 눈"
    if code in (95, 96, 99):
        return "⛈ 뇌우"
    return "정보 없음"


def _value(value, suffix: str = "", digits: int = 0) -> str:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return "-"
    return f"{value:.{digits}f}{suffix}"


def _day(dates: list, index: int) -> str:
    if index >= len(dates):
        raise WeatherError("예보 날짜 데이터가 부족합니다.")
    try:
        date = datetime.strptime(dates[index], "%Y-%m-%d")
    except (ValueError, TypeError) as error:
        raise WeatherError("예보 날짜를 해석할 수 없습니다.") from error
    return date.strftime("%m/%d") + f"({WEEKDAYS[date.weekday()]})"


def _at(data: dict, key: str, index: int):
    values = data.get(key, [])
    return values[index] if isinstance(values, list) and index < len(values) else None


def forecast_text(location: WeatherLocation, period: str) -> str:
    """오늘/내일/7일 공통 API 요청을 1회만 수행하고 측정값을 있는 그대로 표기."""
    if period not in {"오늘", "내일", "주간"}:
        raise WeatherError("날씨 조회는 오늘·내일·주간 중 선택하세요.")
    result = _get_json(FORECAST_URL, {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": KOREA_TIMEZONE, "forecast_days": 7,
    })
    daily = result.get("daily")
    if not isinstance(daily, dict) or not isinstance(daily.get("time"), list):
        raise WeatherError("일별 예보 데이터가 비어 있습니다. 잠시 후 재조회하세요.")
    dates = daily["time"]
    if len(dates) < (7 if period == "주간" else 2 if period == "내일" else 1):
        raise WeatherError("요청한 날짜의 예보가 아직 제공되지 않습니다.")
    source = "📡 Open-Meteo 예보 · 무료 모델 데이터 / 변동 가능"
    if period == "주간":
        lines = [f"🗓 {location.name} 7일 예보"]
        for i in range(7):
            lines.append(
                f"{_day(dates, i)} {_weather_label(_at(daily, 'weather_code', i))} "
                f"{_value(_at(daily, 'temperature_2m_min', i), '℃')}~"
                f"{_value(_at(daily, 'temperature_2m_max', i), '℃')} "
                f"· 비 {_value(_at(daily, 'precipitation_probability_max', i), '%')}"
            )
        return "\n".join(lines + [source])
    index = 0 if period == "오늘" else 1
    lines = [f"{'🌤' if index == 0 else '🌦'} {location.name} {period} 날씨 · {_day(dates, index)}"]
    if index == 0:
        current = result.get("current")
        if isinstance(current, dict):
            lines.extend((
                f"🌡 현재 {_value(current.get('temperature_2m'), '℃', 1)}"
                f" · 체감 {_value(current.get('apparent_temperature'), '℃', 1)}",
                f"{_weather_label(current.get('weather_code'))}"
                f" · 습도 {_value(current.get('relative_humidity_2m'), '%')}"
                f" · 바람 {_value(current.get('wind_speed_10m'), 'km/h', 1)}",
            ))
    lines.extend((
        f"🌡 최저 {_value(_at(daily, 'temperature_2m_min', index), '℃', 1)}"
        f" · 최고 {_value(_at(daily, 'temperature_2m_max', index), '℃', 1)}",
        f"🌂 강수확률 최대 {_value(_at(daily, 'precipitation_probability_max', index), '%')}"
        f" · {_weather_label(_at(daily, 'weather_code', index))}",
        source,
    ))
    return "\n".join(lines)


def location_help(db: sqlite3.Connection, room: str, sender: str) -> str:
    selected = get_location(db, room, sender)
    return (f"📍 날씨 지역 설정\n현재 지역: {selected.name}\n"
            "변경: 날 지역 부산 / 날 지역 강남구\n"
            "또는 앙개야 날씨 지역 부산\n"
            "※ GPS 위치는 읽지 않으며 대화방·발신자별로 저장됩니다.")
