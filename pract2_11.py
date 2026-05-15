"""Практическая работа №2: шаблон «Наблюдатель» для курса валют (pract2_11)."""

from __future__ import annotations

import sys
import unittest
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class Observer(ABC):
    """Абстрактный наблюдатель (GoF Observer)."""

    @abstractmethod
    def update(self, subject: CurrencyData) -> None:
        """Вызывается при изменении данных о курсе валют."""


class CurrencyData:
    """Субъект: данные о курсе валют и список наблюдателей."""

    def __init__(self, base_currency: str, quote_currency: str) -> None:
        self._base_currency: str = base_currency.upper()
        self._quote_currency: str = quote_currency.upper()
        self._rate: Optional[float] = None
        self._date: str = ""
        self._observers: List[Observer] = []

    @property
    def base_currency(self) -> str:
        return self._base_currency

    @property
    def quote_currency(self) -> str:
        return self._quote_currency

    @property
    def rate(self) -> Optional[float]:
        return self._rate

    @property
    def date(self) -> str:
        return self._date

    def add_observer(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self) -> None:
        for observer in list(self._observers):
            observer.update(self)

    def update_currency_data(self, rate: float, date: str = "") -> None:
        self._rate = rate
        if date:
            self._date = date
        self.notify_observers()

    def pair_label(self) -> str:
        return f"{self._base_currency}/{self._quote_currency}"


class CurrencyWatcher(Observer):
    """Конкретный наблюдатель: выводит оповещение об изменении курса."""

    def __init__(self, name: str) -> None:
        self._name: str = name
        self.last_message: str = ""

    @property
    def name(self) -> str:
        return self._name

    def update(self, subject: CurrencyData) -> None:
        rate: Optional[float] = subject.rate
        if rate is None:
            return
        date_part: str = f", дата: {subject.date}" if subject.date else ""
        self.last_message = (
            f"[{self._name}] Курс {subject.pair_label()}: {rate:.4f}{date_part}"
        )
        print(self.last_message)


class CurrencyApi:
    """Учебное API: имитация внешнего сервиса курсов валют."""

    def __init__(self) -> None:
        self._rates: Dict[Tuple[str, str], Tuple[float, str]] = {
            ("USD", "RUB"): (92.50, "2026-05-15"),
            ("EUR", "RUB"): (100.20, "2026-05-15"),
            ("EUR", "USD"): (1.08, "2026-05-15"),
        }

    def get_rate(self, base_currency: str, quote_currency: str) -> dict:
        """Возвращает данные о курсе в формате, похожем на ответ REST API."""
        base: str = base_currency.upper()
        quote: str = quote_currency.upper()
        key: Tuple[str, str] = (base, quote)
        if key not in self._rates:
            raise KeyError(f"Пара {base}/{quote} не найдена в API")
        rate, date = self._rates[key]
        return {
            "result": "success",
            "base": base,
            "quote": quote,
            "rate": rate,
            "date": date,
        }

    def set_rate(self, base_currency: str, quote_currency: str, rate: float, date: str) -> None:
        """Обновляет курс в «базе» API (имитация изменения на рынке)."""
        key = (base_currency.upper(), quote_currency.upper())
        self._rates[key] = (rate, date)


def fetch_exchange_rate(
    base_currency: str,
    quote_currency: str,
    api: Optional[CurrencyApi] = None,
) -> tuple[float, str]:
    """Запрашивает курс у учебного CurrencyApi."""
    client: CurrencyApi = api if api is not None else CurrencyApi()
    payload: dict = client.get_rate(base_currency, quote_currency)
    return float(payload["rate"]), str(payload["date"])


def run_currency_monitor(
    base_currency: str = "USD",
    quote_currency: str = "RUB",
    api: Optional[CurrencyApi] = None,
) -> CurrencyData:
    """Регистрирует наблюдателей, запрашивает курс и оповещает об обновлении."""
    client: CurrencyApi = api if api is not None else CurrencyApi()
    currency_data: CurrencyData = CurrencyData(base_currency, quote_currency)
    currency_data.add_observer(CurrencyWatcher("Банк"))
    currency_data.add_observer(CurrencyWatcher("Брокер"))
    currency_data.add_observer(CurrencyWatcher("Аналитик"))

    print(f"Запрос курса {currency_data.pair_label()} (учебное API)...\n")
    rate, date = fetch_exchange_rate(base_currency, quote_currency, client)
    currency_data.update_currency_data(rate, date)

    print("\nИзменение курса в API...\n")
    client.set_rate(base_currency, quote_currency, rate + 0.75, date)
    new_rate, new_date = fetch_exchange_rate(base_currency, quote_currency, client)
    currency_data.update_currency_data(new_rate, new_date)

    return currency_data


def main() -> None:
    try:
        run_currency_monitor("USD", "RUB")
    except KeyError as exc:
        print(f"Ошибка API: {exc}", file=sys.stderr)
        sys.exit(1)


class _RecordingObserver(Observer):
    """Вспомогательный наблюдатель для тестов."""

    def __init__(self) -> None:
        self.updates: int = 0
        self.last_rate: Optional[float] = None

    def update(self, subject: CurrencyData) -> None:
        self.updates += 1
        self.last_rate = subject.rate


class TestPract211Observer(unittest.TestCase):
    def test_add_and_remove_observer(self) -> None:
        data: CurrencyData = CurrencyData("USD", "EUR")
        observer: _RecordingObserver = _RecordingObserver()
        data.add_observer(observer)
        self.assertEqual(len(data._observers), 1)
        data.remove_observer(observer)
        self.assertEqual(len(data._observers), 0)

    def test_update_currency_data_notifies_observers(self) -> None:
        data: CurrencyData = CurrencyData("USD", "RUB")
        observer: _RecordingObserver = _RecordingObserver()
        data.add_observer(observer)
        data.update_currency_data(90.5, "2026-05-15")
        self.assertEqual(observer.updates, 1)
        self.assertAlmostEqual(observer.last_rate, 90.5)

    def test_notify_observers_calls_all_registered(self) -> None:
        data: CurrencyData = CurrencyData("EUR", "USD")
        first: _RecordingObserver = _RecordingObserver()
        second: _RecordingObserver = _RecordingObserver()
        data.add_observer(first)
        data.add_observer(second)
        data._rate = 1.08
        data.notify_observers()
        self.assertEqual(first.updates, 1)
        self.assertEqual(second.updates, 1)

    def test_removed_observer_not_notified(self) -> None:
        data: CurrencyData = CurrencyData("GBP", "USD")
        observer: _RecordingObserver = _RecordingObserver()
        data.add_observer(observer)
        data.remove_observer(observer)
        data.update_currency_data(1.25)
        self.assertEqual(observer.updates, 0)

    def test_currency_watcher_update_message(self) -> None:
        data: CurrencyData = CurrencyData("USD", "RUB")
        watcher: CurrencyWatcher = CurrencyWatcher("Тест")
        data.update_currency_data(95.1234, "2026-05-15")
        watcher.update(data)
        self.assertIn("Тест", watcher.last_message)
        self.assertIn("USD/RUB", watcher.last_message)
        self.assertIn("95.1234", watcher.last_message)

    def test_custom_api_returns_rate(self) -> None:
        api: CurrencyApi = CurrencyApi()
        payload: dict = api.get_rate("USD", "RUB")
        self.assertEqual(payload["result"], "success")
        rate, date = fetch_exchange_rate("USD", "RUB", api)
        self.assertAlmostEqual(rate, 92.50)
        self.assertEqual(date, "2026-05-15")


if __name__ == "__main__":
    main()
