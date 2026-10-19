import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo

API = 'https://zapachkrakowa.pl/api/v1/forecast'
TZ = ZoneInfo('Europe/Warsaw')
STATE_FILE = Path('alert_state.json')


def request_json(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'SmrodoBot/0.3', 'Accept': 'application/json'}, method='POST' if data is not None else 'GET')
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


def load_state():
    try:
        value = json.loads(STATE_FILE.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def forecast_rows(data, now):
    rows = []
    for item in data.get('riskiest_hours', []):
        try:
            hour = parse_hour(item['time'], now)
            probability = float(item['p_elevated'])
        except (KeyError, ValueError, TypeError):
            continue
        if 0 <= probability <= 1:
            rows.append((hour, probability, item))
    return sorted(rows, key=lambda row: row[0])


def main():
    now = datetime.now(TZ)
    today = now.date().isoformat()
    location = os.environ.get('WATCH_ADDRESS', 'Gliniana, Podgórze')
    state = load_state()
    params = urllib.parse.urlencode({'address': location, 'hours': 72})
    data = request_json(f'{API}?{params}')
    status = data.get('status', {})
    if not status.get('available') or float(status.get('age_hours', 999)) > 6:
        print('Forecast unavailable or stale; no messages sent')
        return

    rows = forecast_rows(data, now)
    place = data.get('location', location)

    # Morning report, sent once between 08:00 and 09:59 local time.
    if 8 <= now.hour < 10 and state.get('last_daily_report') != today:
        remaining = [r for r in rows if r[0].date() == now.date() and r[0] >= now]
        lines = [f'🦆 SmrodoBot — raport poranny ({now:%d.%m})', f'📍 {place}', '📅 Dzisiaj, do końca dnia', '']
        if remaining:
            lines.append('Godziny wyróżnione przez model:')
            for hour, p, _ in remaining:
                icon = '🔴' if p >= 0.5 else '🟡' if p >= 0.25 else '🟢'
                lines.append(f'{icon} {hour:%H:%M} — {p:.0%}')
        else:
            lines.append('API nie wskazuje godzin z pozostałej części dzisiejszego dnia na liście najbardziej ryzykownych.')
        lines += ['', '⚠️ To wybrane godziny, nie pełna prognoza godzinowa.', 'Brak godziny na liście nie oznacza braku ryzyka.', 'Prognoza modelowa, nie pomiar.']
        send_message('\n'.join(lines))
        state['last_daily_report'] = today
        save_state(state)
        print('Morning report sent')

    # Evening warning for the upcoming night (22:00 to 08:00).
    if 21 <= now.hour < 23 and state.get('last_night_check') != today:
        start = datetime.combine(now.date(), time(22), tzinfo=TZ)
        end = datetime.combine(now.date() + timedelta(days=1), time(8), tzinfo=TZ)
        overnight = [r for r in rows if start <= r[0] < end and r[1] >= 0.5]
        if overnight:
            peak = max(overnight, key=lambda r: r[1])
            hours = ', '.join(f'{r[0]:%H:%M}' for r in overnight)
            send_message(f'🌙 SmrodoBot — ostrzeżenie na noc!\n📍 {place}\n🔴 Godziny wysokiego modelowanego ryzyka: {hours}\n📈 Maksymalny udział scenariuszy: {peak[1]:.0%}\n🪟 Rozważ zamknięcie okien przed snem.\nPrognoza modelowa, nie pomiar.')
            print('Night warning sent')
        else:
            print('No high-risk hours in overnight forecast subset')
        # Store check date even if no warning; avoids repeated warnings on same evening.
        state['last_night_check'] = today
        save_state(state)

    # Daytime alerts only, looking two hours ahead.
    if not (8 <= now.hour < 21):
        print('Outside daytime alert window')
        return

    horizon = now + timedelta(hours=2)
    risky = [r for r in rows if now <= r[0] <= horizon and r[1] >= 0.5]
    cutoff = (now - timedelta(days=2)).strftime('%Y-%m-%dT%H')
    notified = {h for h in state.get('notified_hours', []) if isinstance(h, str) and h >= cutoff}
    new = [r for r in risky if r[0].strftime('%Y-%m-%dT%H') not in notified]
    if new:
        first = new[0][0]
        peak = max(new, key=lambda r: r[1])
        send_message(f'⚠️ SmrodoBot — wysokie ryzyko w ciągu 2 godzin!\n📍 {place}\n🕒 Najbliższa nowa godzina: {first:%d.%m %H:%M}\n📈 Najwyższy udział scenariuszy: {peak[1]:.0%}\n🌬️ Wiatr: {peak[2].get("wind", "brak danych")}\nPrognoza modelowa, nie pomiar.')
        notified.update(r[0].strftime('%Y-%m-%dT%H') for r in risky)
        print('Daytime alert sent')
    else:
        print('No new high-risk daytime hours')
    state['notified_hours'] = sorted(notified)
    save_state(state)


if __name__ == '__main__':
    main()
