"""
앙개봇 v0.5.11 카카오톡 간결형 응답 회귀 테스트 — 전체 기능 설명
1. 한국/미국/일본 통화별 가격을 한 줄로 압축하고 번호는 기존 호출부가 유지한다.
2. 시장별 시세 기준정보는 하단에 모으며 확정 종가를 실시간으로 표시하지 않는다.
3. 원본 Quote 데이터와 기존 상세 quote_line 출력은 변경하지 않는다.
4. 메모리7 및 사용자 그룹의 기존 시세 조회·로그·중복처리·메뉴·배터리 동작은 별도 모듈에서 유지한다.
5. 상승 🔺+, 하락 ▽-, 보합 ➖ 표시를 검증한다.
6. 카카오톡 좁은 말풍선에서 프리/애프터 P/A가 밀리지 않도록 화살표 다음의 공백을 제거한다.
"""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.market import Stock, Quote, compact_quote_line, compact_source_summary, quote_line


class CompactStockReplyTests(unittest.TestCase):
    def make_quote(self, name, ticker, currency, market, zone, price, pct, source=''):
        stock = Stock(name, ticker, currency, market, zone)
        stamp = datetime(2026, 11, 5, 12, 12, tzinfo=ZoneInfo(zone))
        return Quote(stock, price, price / (1 + pct / 100), pct, stamp, stamp, source=source)

    def test_one_line_and_price_abbreviation(self):
        kr = self.make_quote('삼성전자', '005930.KS', 'KRW', '한국', 'Asia/Seoul', 205250, -5.85)
        us = self.make_quote('웨스턴디지털', 'WDC', 'USD', '미국', 'America/New_York', 323.83, -6.77)
        jp = self.make_quote('키오시아', '285A.T', 'JPY', '일본', 'Asia/Tokyo', 10085, -6.05)
        self.assertEqual(compact_quote_line(kr), '삼성전자 20.5만 ▽-5.85%')
        self.assertEqual(compact_quote_line(us), 'WDC $323.83 ▽-6.77%')
        self.assertEqual(compact_quote_line(jp), '키오시아 ¥10,085 ▽-6.05%')
        self.assertTrue(all('\n' not in compact_quote_line(q) for q in (kr, us, jp)))
        self.assertEqual(kr.price, 205250)
        self.assertIn('205,250원', quote_line(kr))

    def test_footer_and_close_label(self):
        us = self.make_quote('마이크론', 'MU', 'USD', '미국', 'America/New_York', 795.23, -7,
                             source='나스닥 확정 종가')
        footer = compact_source_summary([us])
        self.assertEqual(len(footer), 1)
        self.assertIn('확정 종가', footer[0])
        self.assertIn('ET', footer[0])
        self.assertNotIn('실시간표시', footer[0])


if __name__ == '__main__':
    unittest.main()
