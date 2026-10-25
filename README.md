# 🦆 SmrodoBot v0.5

**SmrodoBot** to bot Telegram monitorujący modelową prognozę ryzyka uciążliwości zapachowych w Krakowie (okolice oczyszczalni Płaszów). Pobiera dane z API Zapach Krakowa i wysyła wybrane raporty oraz ostrzeżenia.

> **Ważne:** prognoza przedstawia ryzyko modelowe, a nie pomiar zapachu ani gwarancję jego wystąpienia. Pole `riskiest_hours` zawiera wybrane godziny wyróżnione przez model — **nie pełną prognozę godzina po godzinie**. Brak godziny na tej liście nie oznacza braku ryzyka.

## Jak działa

- **Raport poranny:** jeden raport dziennie w oknie **07:00–08:59** czasu `Europe/Warsaw`, o ile prognoza jest dostępna i aktualna. Raport pokazuje godziny wyróżnione przez model na pozostałą część dnia.
- **Alert dzienny:** w godzinach **08:00–20:59**, gdy wśród wyróżnionych godzin w ciągu najbliższych **2 godzin** pojawi się ryzyko co najmniej **65%**. Historia ogranicza ponowne powiadomienia o tej samej godzinie.
- **Ostrzeżenie nocne:** sprawdzenie w oknie **21:00–22:59** prognozy na noc **22:00–08:00**. Wiadomość jest wysyłana, gdy wyróżniona godzina osiąga co najmniej **65%**. Mechanizm historii ogranicza duplikaty i pozwala wykrywać nowe ryzykowne godziny zgodnie z logiką `alert.py`.
- **Aktualność danych:** jeśli API nie udostępnia prognozy albo jej wiek przekracza **6 godzin**, bot nie wysyła raportów ani ostrzeżeń.

Kolory w raporcie porannym służą prezentacji poziomu ryzyka; próg wysyłania alertów wynosi **65%**.

## Architektura

- `alert.py` — pobieranie prognozy, decyzje o powiadomieniach, wysyłanie wiadomości i aktualizacja historii.
- `test_alert.py` — testy jednostkowe logiki bota.
- `test_telegram.py` — pomocniczy skrypt do testowania Telegrama (używaj świadomie — może wysłać wiadomość).
- `.github/workflows/alert.yml` — produkcyjne uruchomienia bota.
- `.github/workflows/tests.yml` — automatyczne testy.
- `.github/workflows/test_bot_state.yml` — osobny test integracyjny odczytu i zapisu historii (bez wysyłania Telegramów).

### Gałęzie

| Gałąź | Przeznaczenie |
| --- | --- |
| `main` | Produkcyjny kod i harmonogram powiadomień |
| `develop-v05` | Przygotowanie i testowanie zmian v0.5 przed wdrożeniem |
| `bot-state` | Trwała historia powiadomień w pliku `alert_state.json` |

**Nie scalaj `bot-state` z `main`.** To gałąź przeznaczona na stan aplikacji, a nie na rozwój kodu.

## Uruchamianie w GitHub Actions

Workflow `SmrodoBot Alerts` jest zaplanowany co **30 minut**:

```yaml
schedule:
  - cron: '*/30 * * * *'
```

Harmonogram GitHub Actions może się opóźniać, dlatego raport poranny dopuszcza okno 07:00–08:59, a nie jedną dokładną minutę. Godziny w logice bota są interpretowane w strefie `Europe/Warsaw`, z uwzględnieniem zmiany czasu.

Workflow produkcyjny działa tylko na `main`. Pobiera historię z `bot-state`, uruchamia `alert.py`, a następnie zapisuje zmieniony stan z powrotem na `bot-state`.

### Sekrety

W **Settings → Secrets and variables → Actions** skonfiguruj:

- `TELEGRAM_BOT_TOKEN` — token własnego bota Telegram.
- `TELEGRAM_CHAT_ID` — identyfikator odbiorcy wiadomości.

Opcjonalnie możesz ustawić `WATCH_ADDRESS` jako zmienną środowiskową workflow; bez niej kod używa domyślnej lokalizacji zapisanej w `alert.py`.

**Nie umieszczaj tokenów, identyfikatorów prywatnych ani danych dostępowych w repozytorium.** Uprawnienia workflow muszą pozwalać na zapis zawartości gałęzi `bot-state` (`contents: write`).

## Testy

Testy jednostkowe uruchomisz lokalnie:

```bash
python -m unittest -v test_alert.py
```

Podczas przygotowania v0.5 **14 testów jednostkowych zakończyło się powodzeniem**. Osobny test integracyjny potwierdził, że GitHub Actions może zapisać znacznik na `bot-state` i odczytać go ponownie. Nie jest to jednak gwarancja poprawności przyszłych danych API ani dostarczenia każdej wiadomości Telegram.

Test integracyjny tworzy plik `state_integration_test.json` na `bot-state` i nie modyfikuje `alert_state.json`.

## Ograniczenia

- GitHub Actions nie gwarantuje uruchomienia dokładnie o zaplanowanej godzinie; uruchomienie może zostać opóźnione lub pominięte.
- API zwraca wybrane godziny ryzyka, a nie kompletny szereg godzinowy.
- Gdy wysyłka wiadomości powiedzie się, lecz późniejszy zapis historii na `bot-state` zawiedzie, może wystąpić ponowne powiadomienie.
- Stan zapisany w Git jest trwalszy niż cache, ale jego dostępność nadal zależy od GitHuba, uprawnień i poprawnego działania workflow.

## Źródło prognozy

[Zapach Krakowa — API prognozy](https://zapachkrakowa.pl/api/v1/forecast)

## Wersje

- **v0.5** — próg alertów 65%, testy automatyczne oraz historia powiadomień przechowywana na `bot-state`.
- **v0.4** — wcześniejsza wersja z rozwiniętą logiką powiadomień.

Projekt hobbystyczny, niezależny od dostawcy danych. Korzystaj z prognoz jako wskazówki, nie jako pewnej informacji o warunkach w konkretnej lokalizacji.
