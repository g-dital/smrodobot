import json
import os
import urllib.parse
import urllib.request


def main():
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    payload = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': '🦆 SmrodoBot: test GitHub Actions zakończony sukcesem! Powiadomienia Telegram działają.'
    }).encode('utf-8')
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=payload,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError('Telegram did not accept the message')
    print('Test notification sent successfully')


if __name__ == '__main__':
    main()
