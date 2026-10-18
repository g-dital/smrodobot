import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

API = 'https://zapachkrakowa.pl/api/v1/forecast'
TZ = ZoneInfo('Europe/Warsaw')
STATE_FILE = Path('alert_state.json')


def request_json(url, data=None):
    req = urllib.request.Request(
        url, data=data,
        headers={'User-Agent': 'SmrodoBot/0.2', 'Accept': 'application/json'},
        method='POST' if data is not None else 'GET',
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def send_message(message):
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    body = urllib.parse.urlencode({'chat_id': chat_id, 'text': message}).encode()
    result = request_json(f'https://api.telegram.org/bot{token}/sendMessage', body)
    if not result.get('ok'):
        raise RuntimeError('Telegram rejected message')


def parse_hour(value, now):
    parsed = datetime.strptime(value, '%a %d %b %H:%M')
    options = [parsed.replace(year=y, tzinfo=TZ) for y in (now.year - 1, now.year, now.year + 1)]
    return min(options, key=lambda d: abs((d - now).total_seconds()))


def main():
    location = os.environ.get('WATCH_ADDRESS', 'Gliniana, Podgórze')
    params = urllib.parse.urlencode({'address': location, 'hours': 72})
    data = request_json(f'{API}?{params}')
    status = data.get('status', {})
    if not status.get('available'):
        print('Forecast unavailable; no alert sent')
        return
    if float(status.get('age_hours', 999)) > 6:
        print('Forecast stale (>6 hours); no alert sent')
        return

    now = datetime.now(TZ)
    horizon = now + timedelta(hours=12)
    risky = []
    for item in data.get('riskiest_hours', []):
        try:
            hour = parse_hour(item['time'], now)
            probability = float(item['p_elevated'])
        except (KeyError, ValueError, TypeError):
            continue
        if now <= hour <= horizon and probability >= 0.5:
            risky.append((hour, probability, item))

    if not risky:
        print('No high-risk hours within next 12 hours')
        return

    try:
        state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    # Each modelled risky hour can be notified at most once, even if forecasts shift.
    notified = set(state.get('notified_hours', []))
    # Keep the history bounded; timestamps are local ISO hours.
    cutoff = (now - timedelta(days=2)).strftime('%Y-%m-%dT%H')
    notified = {hour for hour in notified if isinstance(hour, str) and hour >= cutoff}
    new_hours = [(hour, probability, item) for hour, probability, item in risky
                 if hour.strftime('%Y-%m-%dT%H') not in notified]

    if not new_hours:
        print('All risky hours already notified')
        return

    new_hours.sort(key=lambda x: x[0])
    peak = max(new_hours, key=lambda x: x[1])
    first = new_hours[0][0]
    message = (
        '⚠️ SmrodoBot: wysokie modelowane ryzyko zapachu!\n'
        f'📍 {data.get("location", location)}\n'
        f'🕒 Najbliższa nowa godzina ryzyka: {first:%d.%m %H:%M}\n'
        f'📈 Najwyższy udział scenariuszy: {peak[1]:.0%} ({peak[0]:%d.%m %H:%M})\n'
        f'🌬️ Wiatr: {peak[2].get("wind", "brak danych")}\n'
        'Prognoza modelowa, nie pomiar ani gwarancja wystąpienia zapachu.'
    )
    send_message(message)
    notified.update(hour.strftime('%Y-%m-%dT%H') for hour, _, _ in risky)
    STATE_FILE.write_text(json.dumps({'notified_hours': sorted(notified)}, indent=2), encoding='utf-8')
    print(f'Alert sent; recorded {len(risky)} forecast hours')


if __name__ == '__main__':
    main()
