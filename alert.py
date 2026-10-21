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
    req = urllib.request.Request(
        url,
        data=data,
        headers={'User-Agent': 'SmrodoBot/0.4', 'Accept': 'application/json'},
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


def hour_key(hour):
    # Include UTC offset to distinguish repeated local hours at DST transitions.
    return hour.isoformat(timespec='minutes')


def recent_notified(values, now):
    cutoff = now - timedelta(days=2)
    result = set()
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, str):
            continue
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is not None and parsed >= cutoff:
                result.add(value)
        except ValueError:
            # Accept legacy keys from v0.3 until they naturally expire.
            try:
                legacy = datetime.strptime(value, '%Y-%m-%dT%H').replace(tzinfo=TZ)
                if legacy >= cutoff:
                    result.add(value)
            except ValueError:
                continue
    return result


def already_notified(hour, notified):
    return hour_key(hour) in notified or hour.strftime('%Y-%m-%dT%H') in notified


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

    # Morning report, sent once between 07:00 and 08:59 local time.
    if 7 <= now.hour < 9 and state.get('last_daily_report') != today:
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

    # Check repeatedly from 21:00 to 22:59, notify only newly risky hours.
    if 21 <= now.hour < 23:
        start = datetime.combine(now.date(), time(22), tzinfo=TZ)
        end = datetime.combine(now.date() + timedelta(days=1), time(8), tzinfo=TZ)
        overnight = [r for r in rows if start <= r[0] < end and r[1] >= 0.5]
        notified_night = recent_notified(state.get('notified_night_hours', []), now)
        new_night = [r for r in overnight if not already_notified(r[0], notified_night)]
        if new_night:
            peak = max(new_night, key=lambda r: r[1])
            hours = ', '.join(f'{r[0]:%H:%M}' for r in new_night)
            send_message(
                f'🌙 SmrodoBot — ostrzeżenie na noc!\n📍 {place}\n'
                f'🔴 Nowe godziny wysokiego modelowanego ryzyka: {hours}\n'
                f'📈 Maksymalny udział scenariuszy: {peak[1]:.0%}\n'
                '🪟 Rozważ zamknięcie okien przed snem.\n'
                'Prognoza modelowa, nie pomiar. Pokazano wybrane godziny z API.'
            )
            notified_night.update(hour_key(r[0]) for r in new_night)
            state['notified_night_hours'] = sorted(notified_night)
            save_state(state)
            print(f'Night warning sent for {len(new_night)} new hours')
        else:
            state['notified_night_hours'] = sorted(notified_night)
            save_state(state)
            print('No new high-risk overnight hours')

    # Daytime alerts only, looking two hours ahead.
    if not (8 <= now.hour < 21):
        print('Outside daytime alert window')
        return

    horizon = now + timedelta(hours=2)
    risky = [r for r in rows if now <= r[0] <= horizon and r[1] >= 0.5]
    notified = recent_notified(state.get('notified_hours', []), now)
    new = [r for r in risky if not already_notified(r[0], notified)]
    if new:
        first = new[0][0]
        peak = max(new, key=lambda r: r[1])
        send_message(
            f'⚠️ SmrodoBot — wysokie ryzyko w ciągu 2 godzin!\n📍 {place}\n'
            f'🕒 Najbliższa nowa godzina: {first:%d.%m %H:%M}\n'
            f'📈 Najwyższy udział scenariuszy: {peak[1]:.0%}\n'
            f'🌬️ Wiatr: {peak[2].get("wind", "brak danych")}\n'
            'Prognoza modelowa, nie pomiar.'
        )
        notified.update(hour_key(r[0]) for r in risky)
        print('Daytime alert sent')
    else:
        print('No new high-risk daytime hours')
    state['notified_hours'] = sorted(notified)
    save_state(state)


if __name__ == '__main__':
    main()
