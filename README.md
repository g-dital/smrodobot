# 🦆 SmrodoBot v0.3

**Telegramowe powiadomienia o modelowanym ryzyku uciążliwych zapachów w Krakowie**, oparte na prognozie serwisu [Zapach Krakowa](https://zapachkrakowa.pl/).

SmrodoBot działa automatycznie w **GitHub Actions** — bez własnego serwera, włączonego komputera i lokalnej instalacji Pythona. Projekt jest niezależnym, eksperymentalnym narzędziem, a **nie oficjalnym systemem ostrzegania**.

> [!IMPORTANT]
> Bot korzysta z **prognozy modelowej**, a nie z pomiaru zapachu. API może zwracać tylko wybrane godziny o najwyższym modelowanym ryzyku (`riskiest_hours`), a nie kompletną prognozę godzinową. **Brak godziny na liście lub brak wiadomości od bota nie oznacza braku zagrożenia.**

## 🔔 Jakie powiadomienia wysyła bot?

| Powiadomienie | Kiedy bot je sprawdza (czas polski) | Kiedy wysyła wiadomość |
| --- | --- | --- |
| ☀️ **Raport poranny** | **07:00–08:59** | Raz dziennie, przy pierwszym udanym uruchomieniu w tym oknie, jeśli prognoza jest dostępna i aktualna; pokazuje wyróżnione przez model godziny do końca dnia |
| ⚠️ **Alert dzienny** | **08:00–20:59** | Jeśli wśród godzin zwróconych przez API pojawi się nowa godzina z `p_elevated >= 0.5` w ciągu najbliższych **2 godzin** |
| 🌙 **Ostrzeżenie nocne** | **21:00–22:59** | Jeśli wśród godzin zwróconych przez API występuje `p_elevated >= 0.5` między **22:00 a 08:00 następnego dnia** |

**Jak to działa w praktyce?**

- Raport poranny pokazuje godziny wyróżnione przez model (🔴 od 50%, 🟡 od 25% do poniżej 50%, 🟢 poniżej 25%). To **nie jest pełna lista wszystkich godzin dnia**.
- Alert dzienny jest wysyłany tylko dla godzin ryzyka, których bot nie zapisał wcześniej jako zgłoszone.
- Jeśli wieczorna kontrola nie wykryje godzin spełniających próg, bot **nie wysyła** wiadomości nocnej.
- **Ważne ograniczenie v0.3:** po pierwszej udanej kontroli nocnej bot zapisuje datę jej wykonania, również gdy nie wykryje ryzyka. Jeśli prognoza zmieni się później tego samego wieczoru, bot może **nie wysłać kolejnego ostrzeżenia nocnego**.
- Bot nie wysyła alertów dziennych po 21:00.

Harmonogram jest uruchamiany nominalnie **co 30 minut**. GitHub Actions może opóźnić lub pominąć uruchomienie — podane przedziały są oknami działania kodu, **nie gwarantowanymi godzinami dostarczenia wiadomości**.

## 🧰 Czego potrzebujesz?

- Konta [GitHub](https://github.com/).
- Konta Telegram.
- Około 10–15 minut na konfigurację.

Nie musisz instalować Pythona na komputerze ani kupować serwera.

## 🚀 Uruchom własnego SmrodoBota

### 1. Utwórz repozytorium z szablonu

1. Otwórz [repozytorium SmrodoBot](https://github.com/g-dital/smrodobot).
2. Kliknij **Use this template → Create a new repository**.
3. Wybierz nazwę i widoczność swojego repozytorium, a następnie kliknij **Create repository**.

Szablon zawiera `alert.py` i `.github/workflows/alert.yml`. **Sekrety Telegrama nie są kopiowane** — skonfigurujesz je osobno.

### 2. Utwórz bota w Telegramie

1. Otwórz oficjalne konto [@BotFather](https://t.me/BotFather).
2. Wyślij `/newbot` i wykonaj instrukcje.
3. Zachowaj otrzymany **token API**.
4. Otwórz nowego bota i wyślij `/start`.

**Nie publikuj tokenu** w kodzie, README, issue ani na zrzutach ekranu.

### 3. Odczytaj Telegram Chat ID

Po wysłaniu `/start` otwórz w przeglądarce (wstaw swój token):

```text
https://api.telegram.org/bot<TWOJ_TOKEN>/getUpdates
```

W odpowiedzi JSON znajdź `message.chat.id` — to identyfikator czatu, do którego bot ma wysyłać wiadomości. Jeśli `result` jest pusty, napisz do bota kolejną wiadomość i odśwież stronę. Przy aktywnym webhooku metoda `getUpdates` może nie zadziałać.

> [!CAUTION]
> Adres powyżej zawiera Twój tajny token. Nie udostępniaj pełnego adresu ani odpowiedzi zawierającej wrażliwe dane.

### 4. Dodaj sekrety w GitHub

W **swoim** repozytorium otwórz:

**Settings → Secrets and variables → Actions → New repository secret**

Utwórz dwa sekrety:

| Nazwa sekretu | Wartość |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token otrzymany od BotFather |
| `TELEGRAM_CHAT_ID` | Wartość `chat.id` z Telegrama |

Użyj **Repository secrets**, a nie publicznych zmiennych repozytorium.

### 5. Wybierz lokalizację (opcjonalnie)

Domyślnie skrypt odpytuje API dla adresu **`Gliniana, Podgórze`**.

Aby zmienić adres, edytuj `.github/workflows/alert.yml`. W kroku **Run SmrodoBot** dodaj `WATCH_ADDRESS`:

```yaml
- name: Run SmrodoBot
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
    WATCH_ADDRESS: 'Twoja ulica, Kraków'
  run: python alert.py
```

Sprawdź, czy API obsługuje wybrany adres i czy zwrócona lokalizacja jest prawidłowa. Nie wpisuj dokładnego prywatnego adresu do publicznego repozytorium, jeśli nie chcesz go ujawniać.

### 6. Uruchom test

1. Otwórz **Actions → SmrodoBot Alerts**.
2. Jeśli GitHub poprosi o włączenie workflow, zatwierdź.
3. Kliknij **Run workflow → Run workflow**.
4. Otwórz nowe uruchomienie, a następnie **check-forecast → Run SmrodoBot**.
5. Sprawdź komunikaty w logach oraz wiadomości w Telegramie.

**Przykładowe komunikaty:**

| Log | Znaczenie |
| --- | --- |
| `Morning report sent` | Wysłano raport poranny |
| `Daytime alert sent` | Wysłano alert dzienny |
| `Night warning sent` | Wysłano ostrzeżenie nocne |
| `No new high-risk daytime hours` | Nie ma nowych godzin do zgłoszenia w dziennym oknie |
| `No high-risk hours in overnight forecast subset` | Wieczorna kontrola nie znalazła godzin powyżej progu w zwróconym zestawie |
| `Outside daytime alert window` | Uruchomienie odbyło się poza godzinami alertów dziennych |
| `Forecast unavailable or stale; no messages sent` | Brak dostępnej prognozy lub dane starsze niż 6 godzin |

**Zielony status GitHub Actions nie oznacza, że Telegram musi otrzymać wiadomość.** Bot może zakończyć działanie prawidłowo, nie wysyłając niczego — np. poza oknem raportu lub bez nowych godzin ryzyka.

### 7. Zostaw harmonogram włączony

Workflow zawiera:

```yaml
schedule:
  - cron: '*/30 * * * *'
```

GitHub interpretuje `cron` w **UTC**, a Python stosuje strefę **`Europe/Warsaw`** do ustalania okien powiadomień (uwzględniając zmianę czasu zimowego i letniego).

GitHub może opóźniać lub pomijać zaplanowane uruchomienia. W nieaktywnych publicznych repozytoriach zaplanowane workflow mogą zostać automatycznie wyłączone — warto co jakiś czas zajrzeć do zakładki **Actions**.

## 🧠 Jak bot zapamiętuje wcześniejsze powiadomienia?

Skrypt zapisuje lokalny plik `alert_state.json`, m.in. z polami:

- `last_daily_report` — data ostatniego raportu porannego;
- `last_night_check` — data wykonania kontroli nocnej;
- `notified_hours` — zgłoszone wcześniej godziny alertów dziennych.

GitHub Actions przywraca i zapisuje ten plik za pomocą **Actions Cache**. W logach możesz zobaczyć `Cache restored successfully`.

> [!WARNING]
> **GitHub Actions Cache nie jest trwałą bazą danych.** Zapis może wygasnąć, zostać usunięty albo przywrócić starszy stan. Możliwe są powtórne wiadomości lub utrata informacji o poprzednich alertach. Mechanizm jest wystarczający do eksperymentu, ale nie gwarantuje dostarczenia dokładnie jednej wiadomości.

## 🔒 Bezpieczeństwo i ograniczenia

- Źródło prognozy: [`https://zapachkrakowa.pl/api/v1/forecast`](https://zapachkrakowa.pl/api/v1/forecast); [dokumentacja API](https://zapachkrakowa.pl/api/docs).
- Bot prosi o prognozę do **72 godzin**, ale do wiadomości wykorzystuje wybrane pozycje `riskiest_hours`.
- Próg `p_elevated >= 0.5` odnosi się do **udziału scenariuszy modelowych**, nie do potwierdzonego pomiarem prawdopodobieństwa wystąpienia zapachu.
- Skrypt pomija prognozę, gdy API oznacza ją jako niedostępną albo gdy jej wiek przekracza **6 godzin**.
- Obecna wersja obsługuje **jeden adres i jeden Telegram Chat ID na uruchomienie**. Nie prowadzi rejestracji subskrybentów.
- Nie ma gwarancji, że prognoza wykryje każdy epizod lub że GitHub uruchomi bota na czas.
- Trzymaj token w GitHub Secrets. Jeśli wycieknie, unieważnij go w BotFather i ustaw nowy sekret.

## 🛠️ Rozwiązywanie problemów

**Raport pojawił się później niż 07:00**  
GitHub Actions może opóźniać zaplanowane uruchomienia. SmrodoBot wysyła raport przy pierwszym udanym uruchomieniu w oknie **07:00–08:59 czasu polskiego**, o ile prognoza jest dostępna i aktualna oraz raport nie został już zapisany jako wysłany. Jeśli w tym oknie nie dojdzie do odpowiedniego uruchomienia, raport zostanie pominięty — bot nie nadrabia go po 09:00.

**Workflow jest zielony, ale nie ma wiadomości**  
Sprawdź log kroku **Run SmrodoBot**. Brak wiadomości może być prawidłowy: poza oknem raportu, bez nowego ryzyka lub po wcześniejszym wysłaniu powiadomienia.

**Workflow jest czerwony (`Failure`)**  
Otwórz nieudane uruchomienie → **check-forecast → Run SmrodoBot**. Znajdź `Traceback`, `Error` lub `IndentationError`. W przypadku błędu wcięć sprawdź spacje w `alert.py`. Same ostrzeżenia o przestarzałej wersji Node.js nie muszą być przyczyną niepowodzenia.

**`Cache not found`**  
Przy pierwszym uruchomieniu jest to normalne. Jeśli pojawia się stale, sprawdź kroki **Restore alert history** i **Save alert history**.

**Przychodzą duplikaty**  
Sprawdź kroki cache. Historia nie jest przechowywana w trwałej bazie danych.

**Nie przychodzi żadna wiadomość**  
Upewnij się, że wysłano `/start` do bota, oba sekrety są poprawne, Chat ID wskazuje właściwy czat, a prognoza jest aktualna.

**Nie przychodzi ostrzeżenie nocne**  
W obecnej wersji wiadomość nocna jest warunkowa. Bot może nie wykryć godzin powyżej progu w zestawie `riskiest_hours`; ponadto po zapisaniu wieczornej kontroli nie sprawdza ponownie tej samej nocy. Brak ostrzeżenia **nie oznacza bezpieczeństwa**.

## 🤝 Udostępnianie projektu

Najprościej: udostępnij link do [szablonu SmrodoBot](https://github.com/g-dital/smrodobot). Każda osoba wybiera **Use this template**, tworzy własnego bota przez BotFather i dodaje swoje GitHub Secrets. Nie przekazuj nikomu własnego tokenu ani prywatnego Chat ID.

---

**SmrodoBot v0.3** · Python 3.12 · GitHub Actions · Telegram Bot API · Zapach Krakowa  
Projekt eksperymentalny — nie zastępuje oficjalnych informacji ani pomiarów środowiskowych.
