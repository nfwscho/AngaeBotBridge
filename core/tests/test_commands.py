"""앙개봇 Python v0.2.0: 허용 계산식, 예외, 날짜/상태 명령 단위 시험."""
import unittest
from app.commands import safe_calculate, execute_command, CommandError

class CommandTests(unittest.TestCase):
    def test_multiplication(self):
        self.assertEqual(safe_calculate('123*456'), '🧮 56,088')

    def test_parentheses(self):
        self.assertEqual(safe_calculate('(10 + 2) * 3'), '🧮 36')

    def test_division(self):
        self.assertIn('2.5', safe_calculate('5/2'))

    def test_zero_division(self):
        with self.assertRaises(CommandError): safe_calculate('10/0')

    def test_disallows_eval(self):
        for bad in ('__import__("os")', 'open("/tmp/a")', '1<<100', 'True+1', '2**100'):
            with self.subTest(bad=bad), self.assertRaises(CommandError): safe_calculate(bad)

    def test_excessive(self):
        for bad in ('9'*200, '1000000000000000**8'):
            with self.subTest(bad=bad), self.assertRaises(CommandError): safe_calculate(bad)

    def test_time(self):
        self.assertIn('KST', execute_command('시간', '', 2))

    def test_server_status(self):
        self.assertIn('2초', execute_command('서버상태', '', 2))

    def test_no_unknown(self):
        with self.assertRaises(CommandError): execute_command('cmd', 'ls', 1)

if __name__ == '__main__': unittest.main()
