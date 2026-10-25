# 🦆 SmrodoBot v0.5.1

**SmrodoBot** to bot Telegram monitorujący modelową prognozę ryzyka uciążliwości zapachowych w Krakowie (okolice oczyszczalni Płaszów). Pobiera dane z API Zapach Krakowa i wysyła raporty oraz ostrzeżenia.

> **Ważne:** prognoza przedstawia ryzyko modelowe, a nie pomiar zapachu ani gwarancję jego wystąpienia. Pole `riskiest_hours` zawiera **wybrane** godziny wyróżnione przez model, a nie pełną prognozę godzina po godzinie. Brak godziny na liście nie oznacza braku ryzyka.

## Jak działa

- **Raport poranny:** jeden raport dziennie w oknie **07:00–08:59** czasu `Europe/Warsaw`, jeśli prognoza jest dostępna i aktualna. Pokazuje wyróżnione godziny z pozostałej części dnia.
- **Alert dzienny:** w godzinach **08:00–20:59**, gdy wśród wyróżnionych godzin w ciągu najbliższych **2 godzin** pojawi się ryzyko co najmniej **65%**. Historia ogranicza duplikaty.
- **Ostrzeżenie nocne:** w oknie **21:00–22:59** sprawdza godziny nocne **22:00–08:00** i ostrzega przy ryzyku co najmniej **65%**. Historia pozwala wykrywać nowe ryzykowne godziny zgodnie z logiką `alert.py`.
- **Aktualność danych:** gdy API nie udostępnia prognozy albo jej wiek przekracza **6 godzin**, bot nie wysyła raportów ani ostrzeżeń.

Kolory w raporcie porannym służą prezentacji poziomu ryzyka; próg wysyłania alertów wynosi **65%**.

## Instalacja własnego SmrodoBota — krok po kroku

Instrukcja jest przeznaczona dla osoby, która chce uruchomić własną kopię bota bez serwera, korzystając z GitHub Actions i Telegrama. Potrzebne są bezpłatne konta GitHub i Telegram; obowiązują limity GitHub Actions oraz warunki korzystania z zewnętrznego API.

### 1. Utwórz własne repozytorium z szablonu

1. Otwórz [repozytorium SmrodoBot](https://github.com/g-dital/smrodobot).
2. Kliknij **Use this template → Create a new repository**.
3. Wybierz właściciela, nazwę repozytorium i widoczność (może być **Private**).
4. Kliknij **Create repository**.

Nie używaj przycisku *Fork*, jeśli chcesz prostą, niezależną kopię projektu. Sekrety Telegrama nie są kopiowane z repozytorium źródłowego — skonfigurujesz własne.

### 2. Utwórz bota Telegram i pobierz token

1. W Telegramie znajdź oficjalne konto [@BotFather](https://t.me/BotFather).
2. Wyślij `/newbot` i wykonaj instrukcje: podaj nazwę oraz unikalny username kończący się na `bot`.
3. BotFather zwróci **token API**. Zachowaj go prywatnie — to wartość `TELEGRAM_BOT_TOKEN`.
4. Otwórz rozmowę ze swoim nowym botem i kliknij **Start** albo wyślij `/start`.

**Nigdy nie wklejaj tokena do plików repozytorium, README, Issue ani publicznych zrzutów ekranu.** Jeśli token wycieknie, unieważnij go w BotFather i wygeneruj nowy.

### 3. Ustal identyfikator czatu (`TELEGRAM_CHAT_ID`)

1. Po wysłaniu `/start` otwórz w przeglądarce adres `https://api.telegram.org/bot<TWOJ_TOKEN>/getUpdates`, zastępując `<TWOJ_TOKEN>` rzeczywistym tokenem.
2. W odpowiedzi JSON odszukaj `message` → `chat` → `id` i skopiuj tę liczbę. W rozmowie prywatnej jest to zazwyczaj dodatnia liczba; dla grup może być ujemna.
3. Jeśli lista `result` jest pusta, wyślij botowi nową wiadomość i odśwież stronę. Jeśli bot ma skonfigurowany webhook, `getUpdates` może nie działać — usuń webhook lub użyj innej metody pozyskania identyfikatora.
4. Zamknij kartę z tokenem; nie udostępniaj pełnego adresu URL.

### 4. Dodaj sekrety do własnego repozytorium

W swoim repozytorium przejdź do **Settings → Secrets and variables → Actions → New repository secret** i dodaj dwa osobne sekrety:

| Name | Secret |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token otrzymany od BotFather |
| `TELEGRAM_CHAT_ID` | Wartość `chat.id` z kroku 3 |

Zapisz oba sekrety. Nie umieszczaj ich w zwykłych *Variables* ani w kodzie.

### 5. Utwórz gałąź `bot-state`

Bot przechowuje historię wysłanych powiadomień na oddzielnej gałęzi Git, aby nie wysyłać wielokrotnie tych samych ostrzeżeń.

1. Wejdź w zakładkę **Code** swojego repozytorium.
2. Kliknij selektor gałęzi (domyślnie `main`).
3. Wpisz `bot-state` i wybierz **Create branch: bot-state from main**.
4. Wróć do `main`. **Nie scalaj `bot-state` z `main`.**

Nie musisz samodzielnie tworzyć `alert_state.json`: workflow przygotuje plik i zapisze go na gałęzi `bot-state` przy pierwszym prawidłowym uruchomieniu. Nie usuwaj tej gałęzi podczas późniejszych aktualizacji kodu.

### 6. Ustaw uprawnienia GitHub Actions

1. Otwórz **Settings → Actions → General**.
2. W sekcji **Workflow permissions** wybierz **Read and write permissions** i kliknij **Save**.
3. Jeśli GitHub poprosi o włączenie Actions dla nowego repozytorium, potwierdź to w zakładce **Actions**.
4. Sprawdź, czy plik `.github/workflows/alert.yml` zawiera dla zadania zapisującego historię uprawnienie `contents: write` — jest ono już przewidziane w wersji v0.5.

Jeśli repozytorium ma dodatkowe reguły ochrony gałęzi, muszą pozwalać workflow na aktualizowanie `bot-state`. Nie włączaj zapisu na wszystkich gałęziach, jeśli nie jest to potrzebne.

### 7. Skonfiguruj lokalizację

Domyślna lokalizacja jest zapisana w `alert.py` (parametr `WATCH_ADDRESS` z wartością zapasową). Jeśli chcesz monitorować inny adres obsługiwany przez API, ustaw zmienną środowiskową `WATCH_ADDRESS` w kroku **Run SmrodoBot** w `.github/workflows/alert.yml`, na przykład:

```yaml
env:
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  WATCH_ADDRESS: 'Gliniana, Podgórze'
run: python alert.py
```

Zmieniaj adres tylko wtedy, gdy API rozpoznaje wybraną lokalizację. Powyższy przykład pokazuje cały fragment kroku — nie dodawaj drugiego `env:` do tego samego kroku.

### 8. Uruchom bota po raz pierwszy

1. Otwórz **Actions → SmrodoBot Alerts**.
2. Kliknij **Run workflow**, wybierz gałąź **main** i potwierdź.
3. Otwórz nowe uruchomienie i sprawdź, czy wszystkie kroki są zielone, szczególnie **Run SmrodoBot** i **Save persistent alert history**.
4. Otwórz gałąź `bot-state` i sprawdź, czy pojawił się `alert_state.json`.

**Ważne:** poprawne uruchomienie nie musi wysłać wiadomości na Telegram. Bot wysyła raport w określonym oknie porannym, a alert tylko wtedy, gdy model wykryje odpowiednie ryzyko. Do osobnego sprawdzenia połączenia z Telegramem możesz wykorzystać `test_telegram.py`, pamiętając, że ten skrypt może wysłać wiadomość.

### 9. Sprawdź automatyczne działanie

Po konfiguracji workflow `SmrodoBot Alerts` sprawdza prognozę co **30 minut**. GitHub Actions może opóźnić lub pominąć zaplanowane uruchomienie. Godziny decyzji bota są interpretowane w `Europe/Warsaw`.

Po pierwszym uruchomieniu sprawdź także **kolejne** uruchomienie, aby potwierdzić odczyt wcześniej zapisanego `alert_state.json`. Historia ma ograniczać powtarzanie tych samych powiadomień, ale nie gwarantuje dostarczenia wiadomości dokładnie raz w razie błędu między wysłaniem Telegrama a zapisem stanu.

### 10. Aktualizowanie własnej kopii

Repozytorium utworzone z szablonu jest niezależne od oryginału i **nie aktualizuje się automatycznie**. Przed przeniesieniem zmian z kolejnych wersji wykonaj kopię swoich ustawień i porównaj zmienione pliki. Zachowaj gałąź `bot-state` oraz własne sekrety. Nie zastępuj historii powiadomień plikami z repozytorium źródłowego.

## Architektura

- `alert.py` — pobieranie prognozy, decyzje o powiadomieniach, wysyłanie wiadomości i aktualizacja historii.
- `test_alert.py` — testy jednostkowe logiki bota.
- `test_telegram.py` — pomocniczy skrypt testowania Telegrama (może wysłać wiadomość).
- `.github/workflows/alert.yml` — produkcyjne uruchomienia bota.
- `.github/workflows/tests.yml` — automatyczne testy.
- `.github/workflows/test_bot_state.yml` — test integracyjny odczytu i zapisu historii bez wysyłania Telegramów.

### Gałęzie

| Gałąź | Przeznaczenie |
| --- | --- |
| `main` | Produkcyjny kod i harmonogram powiadomień |
| `develop-v05` | Historyczna gałąź przygotowania v0.5; po scaleniu może zostać usunięta |
| `bot-state` | Trwała historia powiadomień w `alert_state.json` |

**Nie scalaj `bot-state` z `main`.** To gałąź przeznaczona na stan aplikacji, nie na rozwój kodu.

## Uruchamianie w GitHub Actions

Workflow `SmrodoBot Alerts` jest zaplanowany co **30 minut**:

```yaml
schedule:
  - cron: '*/30 * * * *'
```

Harmonogram GitHub Actions może się opóźniać, dlatego raport poranny dopuszcza okno 07:00–08:59, a nie jedną dokładną minutę. Godziny w logice bota są interpretowane w strefie `Europe/Warsaw`, z uwzględnieniem zmiany czasu.

Workflow produkcyjny działa na `main`. Pobiera historię z `bot-state`, uruchamia `alert.py`, a następnie zapisuje zmieniony stan z powrotem na `bot-state`.

### Sekrety

W **Settings → Secrets and variables → Actions** skonfiguruj `TELEGRAM_BOT_TOKEN` oraz `TELEGRAM_CHAT_ID` (szczegóły w instrukcji instalacji). Opcjonalnie możesz ustawić `WATCH_ADDRESS` jako zmienną środowiskową workflow; bez niej kod używa domyślnej lokalizacji zapisanej w `alert.py`.

**Nie umieszczaj tokenów, identyfikatorów prywatnych ani danych dostępowych w repozytorium.** Zadanie zapisujące historię wymaga `contents: write`.

## Testy

Testy jednostkowe uruchomisz lokalnie:

```bash
python -m unittest -v test_alert.py
```

Podczas przygotowania v0.5 **14 testów jednostkowych zakończyło się powodzeniem**. Osobny test integracyjny potwierdził, że GitHub Actions może zapisać znacznik na `bot-state` i odczytać go ponownie. Produkcyjny workflow potwierdził również utworzenie i wypchnięcie `alert_state.json` na `bot-state`. Nie gwarantuje to poprawności przyszłych danych API ani dostarczenia każdej wiadomości Telegram.

Test integracyjny tworzy plik `state_integration_test.json` na `bot-state` i nie modyfikuje `alert_state.json`.

## Ograniczenia

- GitHub Actions nie gwarantuje uruchomienia dokładnie o zaplanowanej godzinie; uruchomienie może zostać opóźnione lub pominięte.
- API zwraca wybrane godziny ryzyka, a nie kompletny szereg godzinowy.
- Gdy wysyłka wiadomości powiedzie się, lecz późniejszy zapis historii na `bot-state` zawiedzie, może wystąpić ponowne powiadomienie.
- Stan zapisany w Git jest trwalszy niż cache, ale jego dostępność nadal zależy od GitHuba, uprawnień i poprawnego działania workflow.

## Źródło prognozy

[Zapach Krakowa — API prognozy](https://zapachkrakowa.pl/api/v1/forecast)

## Wersje

- **v0.5.1** — przywrócona kompletna instrukcja instalacji własnej kopii (zmiana dokumentacji, bez zmian w logice bota).
- **v0.5** — próg alertów 65%, testy automatyczne oraz historia powiadomień przechowywana na `bot-state`.
- **v0.4** — wcześniejsza wersja z rozwiniętą logiką powiadomień.

Projekt hobbystyczny, niezależny od dostawcy danych. Korzystaj z prognoz jako wskazówki, nie jako pewnej informacji o warunkach w konkretnej lokalizacji.
