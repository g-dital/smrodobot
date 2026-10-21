"""Offline regression tests for SmrodoBot v0.4. Run: python -m unittest -v test_alert.py"""
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import alert

TZ = ZoneInfo('Europe/Warsaw')


class SmrodoBotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_path = Path(self.tmp.name) / 'alert_state.json'
        self.state_patch = patch.object(alert, 'STATE_FILE', self.state_path)
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)
        self.sent = []
        send_patch = patch.object(alert, 'send_message', side_effect=self.sent.append)
        send_patch.start()
        self.addCleanup(send_patch.stop)
        self.forecast = []
        api_patch = patch.object(alert, 'request_json', side_effect=self.fake_api)
        api_patch.start()
        self.addCleanup(api_patch.stop)

    def fake_api(self, url, data=None):
        return {
            'status': {'available': True, 'age_hours': 1},
            'location': 'Testowa lokalizacja',
            'riskiest_hours': [
                {'time': when.strftime('%a %d %b %H:%M'), 'p_elevated': probability, 'wind': 'SW'}
                for when, probability in self.forecast
            ],
        }

    def run_at(self, day, hour, minute=0):
        fixed = datetime(2026, 10, day, hour, minute, tzinfo=TZ)
        real_datetime = datetime

        class FixedDatetime(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed if tz is None else fixed.astimezone(tz)

        with patch.object(alert, 'datetime', FixedDatetime):
            alert.main()

    def test_morning_report_once(self):
        self.run_at(22, 7, 30)
        self.run_at(22, 8, 0)
        self.assertEqual(len(self.sent), 1)
        self.assertIn('raport poranny', self.sent[0])

    def test_no_morning_report_after_window(self):
        self.run_at(22, 9, 0)
        self.assertEqual(self.sent, [])

    def test_daytime_alert_not_repeated(self):
        self.forecast = [(datetime(2026, 10, 22, 15, 0, tzinfo=TZ), 0.7)]
        self.run_at(22, 14, 0)
        self.run_at(22, 14, 30)
        self.assertEqual(len(self.sent), 1)
        self.assertIn('ciągu 2 godzin', self.sent[0])

    def test_daytime_outside_two_hour_horizon(self):
        self.forecast = [(datetime(2026, 10, 22, 17, 0, tzinfo=TZ), 0.7)]
        self.run_at(22, 14, 0)
        self.assertEqual(self.sent, [])

    def test_night_new_risk_after_clear_check_and_no_duplicates(self):
        self.run_at(22, 21, 0)  # no risk yet
        self.forecast = [(datetime(2026, 10, 23, 2, 0, tzinfo=TZ), 0.65)]
        self.run_at(22, 21, 30)  # new risk
        self.run_at(22, 22, 0)  # same risk
        self.assertEqual(len(self.sent), 1)
        self.assertIn('ostrzeżenie na noc', self.sent[0])
        self.assertIn('02:00', self.sent[0])

    def test_night_new_hour_triggers_update(self):
        first = datetime(2026, 10, 23, 2, 0, tzinfo=TZ)
        second = datetime(2026, 10, 23, 4, 0, tzinfo=TZ)
        self.forecast = [(first, 0.65)]
        self.run_at(22, 21, 30)
        self.forecast = [(first, 0.65), (second, 0.8)]
        self.run_at(22, 22, 30)
        self.assertEqual(len(self.sent), 2)
        self.assertIn('04:00', self.sent[1])
        self.assertNotIn('02:00', self.sent[1])

    def test_night_silent_outside_window(self):
        self.forecast = [(datetime(2026, 10, 23, 2, 0, tzinfo=TZ), 0.9)]
        self.run_at(22, 23, 0)
        self.assertEqual(self.sent, [])

    def test_stale_forecast_never_sends(self):
        with patch.object(alert, 'request_json', return_value={
            'status': {'available': True, 'age_hours': 7}, 'riskiest_hours': []
        }):
            self.run_at(22, 7, 30)
        self.assertEqual(self.sent, [])


if __name__ == '__main__':
    unittest.main()
