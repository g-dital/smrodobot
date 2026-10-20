# 🦆 SmrodoBot v0.3

**Telegramowe powiadomienia o modelowanym ryzyku uciążliwych zapachów w Krakowie**, na podstawie prognozy serwisu [Zapach Krakowa](https://zapachkrakowa.pl/).

Bot działa w chmurze przez **GitHub Actions** — nie trzeba mieć włączonego komputera ani własnego serwera. To projekt społecznościowy / prywatny, nie oficjalny system ostrzegania.

> **Ważne:** to prognoza modelowa, nie pomiar jakości powietrza ani gwarancja wystąpienia lub braku zapachu. API może zwracać tylko wybrane najbardziej ryzykowne godziny. Brak godziny na liście **nie oznacza**, że jest bezpiecznie.

## Jakie wiadomości otrzymasz?

| Rodzaj | Kiedy | Warunek |
| --- | --- | --- |
| ☀️ Raport poranny | Przy uruchomieniu bota między **08:00 a 08:59**, czasu polskiego | Codziennie, jeśli prognoza jest dostępna i aktualna; maksymalnie raz na dzień według zapisanej historii |
| ⚠️ Alert dzienny | Podczas sprawdzania między **08:00 a 20:59** | Nowa godzina z `p_elevated >= 0.5` w ciągu kolejnych **2 godzin** |
| 🌙 Ostrzeżenie nocne | Podczas sprawdzania między **21:00 a 22:59** | Co najmniej jedna godzina z `p_elevated >= 0.5` w przedziale **22:00–08:00** następnego dnia |

Jeśli nie ma wysokiego ryzyka na noc, bot nie wysyła wiadomości wieczornej. Nocą nadal uruchamia się harmonogram, ale bieżąca wersja nie wysyła nowych alertów dziennych po 21:00 ani nie ponawia nocnej kontroli po zapisaniu jej wyniku.

**Uwaga o dokładności czasu:** harmonogram GitHub Actions działa co 30 minut, ale wykonania mogą być opóźnione lub pominięte. Godziny 08:00 i 21:00 oznaczają okna czasowe, nie gwarantowany moment doręczenia.

## Co jest potrzebne?

- Konto [GitHub](https://github.com/).
- Konto Telegram.
- Pliki projektu: `alert.py` oraz `.github/workflows/alert.yml`.
- Około 10–15 minut na konfigurację.
- Nie potrzeba instalować Pythona na własnym komputerze.

## Instrukcja: uruchom własnego SmrodoBota

### 1. Utwórz własne repozytorium

Najprościej: otwórz repozytorium projektu na GitHubie i użyj **Fork** (jeśli właściciel udostępnił repozytorium). Alternatywnie utwórz nowe repozytorium i wgraj do niego:

```text
smrodobot/
├── alert.py
└── .github/
    └── workflows/
        └── alert.yml
```

**Ważne:** plik workflow musi być dokładnie pod ścieżką `.github/workflows/alert.yml`, a nie obok `alert.py`.

### 2. Utwórz bota na Telegramie

1. W Telegramie otwórz oficjalnego **[@BotFather](https://t.me/BotFather)**.
2. Wyślij `/newbot` i wykonaj instrukcje.
3. Skopiuj otrzymany **token API** — będzie potrzebny w GitHub Secrets.
4. Otwórz swojego nowego bota i kliknij **Start** albo wyślij `/start`. Bot nie może rozpocząć prywatnej rozmowy, zanim sam do niego nie napiszesz.

**Nigdy nie umieszczaj tokenu w `alert.py`, README, zrzutach ekranu ani publicznym repozytorium.**

### 3. Znajdź swój Telegram Chat ID

Po wysłaniu `/start` otwórz w przeglądarce adres (wstaw swój token):

```text
https://api.telegram.org/bot<TWOJ_TOKEN>/getUpdates
```

W odpowiedzi JSON znajdź pole `message.chat.id` (lub `chat.id` w odpowiedniej aktualizacji). To Twój **Chat ID**, zwykle liczba. Jeśli lista `result` jest pusta, napisz do bota jeszcze jedną wiadomość i odśwież stronę.

**Uwaga:** URL zawiera tajny token — nie udostępniaj go i nie wklejaj do publicznych zgłoszeń. Jeśli bot używa webhooka lub aktualizacje zostały już pobrane przez inny proces, `getUpdates` może nie pokazać oczekiwanej wiadomości.

### 4. Dodaj sekrety w GitHubie

W swoim repozytorium przejdź do:

**Settings → Secrets and variables → Actions → New repository secret**

Dodaj dokładnie dwa sekrety:

| Nazwa | Wartość |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token od BotFather |
| `TELEGRAM_CHAT_ID` | Twój numer `chat.id` |

Nie dodawaj ich jako zwykłych zmiennych ani bezpośrednio do plików.

### 5. Wybierz lokalizację (opcjonalnie)

Domyślnie bot sprawdza **`Gliniana, Podgórze`**.

Aby używać innego adresu, edytuj `.github/workflows/alert.yml` i w kroku `Run SmrodoBot` dodaj `WATCH_ADDRESS`:

```yaml
env:
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  WATCH_ADDRESS: 'Twoja ulica, Kraków'
run: python alert.py
```

Adres musi być obsługiwany przez API. Sprawdź, czy odpowiedź rzeczywiście odpowiada wybranej lokalizacji.

### 6. Włącz i przetestuj GitHub Actions

1. Otwórz **Actions → SmrodoBot Alerts**.
2. Jeśli GitHub o to poprosi, włącz workflows w repozytorium.
3. Wybierz **Run workflow → Run workflow**.
4. Wejdź do zakończonego uruchomienia → **check-forecast → Run SmrodoBot**.
5. Sprawdź logi oraz Telegram.

Przykładowe logi:

| Log | Znaczenie |
| --- | --- |
| `Morning report sent` | Wysłano raport poranny |
| `Daytime alert sent` | Wysłano alert dzienny |
| `Night warning sent` | Wysłano ostrzeżenie nocne |
| `No new high-risk daytime hours` | Nie ma nowych godzin do zgłoszenia w dziennym oknie |
| `Outside daytime alert window` | Uruchomienie poza godzinami alertów dziennych |
| `Forecast unavailable or stale` | API niedostępne lub prognoza starsza niż 6 godzin; wiadomości nie wysłano |

Ręczny test poza porannym lub wieczornym oknem czasowym **może nie wysłać żadnej wiadomości**. To normalne i nie musi oznaczać błędu.

### 7. Zostaw bota włączonego

Workflow zawiera harmonogram:

```yaml
schedule:
  - cron: '*/30 * * * *'
```

GitHub interpretuje `cron` w UTC. Ponieważ skrypt sam odczytuje czas `Europe/Warsaw`, poprawnie rozpoznaje polskie godziny zimą i latem. Harmonogram uruchamia się nominalnie o pełnej godzinie i o wpół (UTC), ale nie gwarantuje dokładności. GitHub może także automatycznie wyłączyć zaplanowane workflows w nieaktywnych repozytoriach publicznych; warto okresowo kontrolować zakładkę Actions.

## Jak bot pamięta wcześniejsze powiadomienia?

Bot zapisuje `alert_state.json` z polami takimi jak:

- `last_daily_report` — data ostatniego raportu porannego;
- `last_night_check` — data wykonanej kontroli nocnej;
- `notified_hours` — godziny zgłoszone w alertach dziennych.

Plik jest przenoszony między uruchomieniami za pomocą **GitHub Actions Cache**. W logach szukaj `Cache restored successfully` oraz informacji o zapisie cache.

**Ograniczenie:** GitHub Actions Cache nie jest trwałą bazą danych. Cache może zostać usunięty, wygasnąć lub zostać przywrócony w starszej wersji. W takim przypadku mogą pojawić się duplikaty. Jest to rozwiązanie wygodne do prywatnego eksperymentu, ale nie daje ścisłej gwarancji dostarczenia dokładnie jednej wiadomości. Jeśli bot ma działać niezawodnie dla wielu osób, warto przenieść stan do trwałego magazynu danych.

## Jak udostępnić to innym?

**Najprostszy i najbezpieczniejszy wariant: każda osoba uruchamia własną kopię repozytorium i tworzy własnego bota Telegram.** Każdy ustawia własne sekrety i opcjonalny adres. Wtedy nie udostępniasz nikomu swojego tokenu ani prywatnego Chat ID.

Bieżąca wersja obsługuje **jeden `TELEGRAM_CHAT_ID` i jeden adres na uruchomienie**. Samo udostępnienie komuś linku do Twojego bota nie zapisze tej osoby jako odbiorcy powiadomień. Wspólny bot dla wielu użytkowników wymaga rozbudowy o rejestrację subskrybentów, ich lokalizacje i osobne preferencje.

## Ograniczenia i bezpieczeństwo

- API: `https://zapachkrakowa.pl/api/v1/forecast`; dokumentacja: [zapachkrakowa.pl/api/docs](https://zapachkrakowa.pl/api/docs).
- Skrypt pobiera prognozę z parametrem `hours=72`, ale do wiadomości wykorzystuje przede wszystkim pole `riskiest_hours`, które nie musi zawierać pełnej osi czasu.
- Próg alertu: `p_elevated >= 0.5` (udział scenariuszy modelowych; nie należy go automatycznie interpretować jako zweryfikowanego prawdopodobieństwa wystąpienia odoru).
- Nie ma gwarancji, że prognoza wykryje wszystkie epizody zapachowe lub że zdąży ostrzec przed ich początkiem.
- Jeśli zagrożenie pojawi się w prognozie dopiero po wykonaniu wieczornej kontroli, obecna wersja może nie wysłać kolejnego ostrzeżenia przed nocą.
- Jeśli nie ma świeżej prognozy, bot nie wysyła raportu ani alertu — brak wiadomości nie jest sygnałem bezpieczeństwa.
- Trzymaj token w GitHub Secrets. Jeśli token wycieknie, unieważnij go przez BotFather i zaktualizuj sekret.

## Rozwiązywanie problemów

**Nie przychodzi żadna wiadomość:** sprawdź, czy uruchomiłeś rozmowę z botem (`/start`), czy sekrety mają poprawne nazwy, czy Chat ID jest prawidłowy oraz czy log nie pokazuje braku ryzyka lub nieaktualnej prognozy.

**`Cache not found`:** przy pierwszym uruchomieniu to normalne. Jeśli powtarza się po wcześniejszym zapisie, sprawdź krok `Save alert history`.

**Raport pojawił się później niż 08:00:** GitHub Actions może opóźniać uruchomienia; skrypt dopuszcza poranny raport w oknie 08:00–09:59.

**Pojawiają się duplikaty:** sprawdź `Restore alert history` i `Save alert history`; pamięć oparta na cache nie jest niezawodnym mechanizmem dokładnie-jednokrotnego wysyłania.

**Nie ma raportu nocnego:** to zamierzone, jeśli w danych zwróconych przez API nie wykryto godzin spełniających próg. Nie oznacza to gwarantowanego braku zapachu.

---

**Projekt:** SmrodoBot v0.3 · Python 3.12 · GitHub Actions · Telegram Bot API · Zapach Krakowa.
