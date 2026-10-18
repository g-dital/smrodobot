import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API = 'https://zapachkrakowa.pl/api/v1/forecast'
TZ = ZoneInfo('Europe/Warsaw')
STATE_FILE = 'alert_state.json'


def request_json(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'SmrodoBot/0.1', 'Accept': 'application/json'}, method='POST' if data else 'GET')
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def send_message(message):
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    body = urllib.parse.urlencode({'chat_id': chat_id, 'text': message}).encode()
    result = request_json(f'https://api.telegram.org/bot{token}/sendMessage', body)
    if not result.get('ok'):
        raise RuntimeError('Telegram rejected message')


def parse_hour(value):
    # API example: 'Wed 21 Oct 00:00'; infer year from forecast generation date.
    current = datetime.now(TZ)
    parsed = datetime.strptime(value, '%a %d %b %H:%M')
    options = [parsed.replace(year=y, tzinfo=TZ) for y in (current.year - 1, current.year, current.year + 1)]
    return min(options, key=lambda d: abs((d - current).total_seconds()))


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
            hour = parse_hour(item['time'])
            probability = float(item['p_elevated'])
        except (KeyError, ValueError, TypeError):
            continue
        if now <= hour <= horizon and probability >= 0.5:
            risky.append((hour, probability, item))
    if not risky:
        print('No high-risk hours within next 12 hours')
        return

    risky.sort(key=lambda x: x[0])
    # Notify once per predicted high-risk episode, represented by earliest hour.
    episode_key = risky[0][0].strftime('%Y-%m-%dT%H')
    try:
        with open(STATE_FILE, encoding='utf-8') as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    if state.get('last_episode') == episode_key:
        print('Already notified for this episode')
        return

    peak = max(risky, key=lambda x: x[1])
    first = risky[0][0]
    message = (f'⚠️ SmrodoBot: wysokie modelowane ryzyko zapachu!\n'
               f'📍 {data.get("location", location)}\n'
               f'🕒 Pierwsza godzina: {first:%d.%m %H:%M}\n'
               f'📈 Najwyższy udział scenariuszy: {peak[1]:.0%} ({peak[0]:%d.%m %H:%M})\n'
               f'🌬️ Wiatr: {peak[2].get("wind", "brak danych")}\n'
               f'Prognoza modelowa, nie pomiar ani gwarancja wystąpienia zapachu.')
    send_message(message)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_episode': episode_key}, f)
    print('Alert sent')


if __name__ == '__main__':
    main()
