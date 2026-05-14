"""Лабораторная работа №4: структурный шаблон «Приспособленец» (моделирование автодвижения)."""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from typing import Dict, Tuple


class Car:
    """
    Приспособленец: разделяемые данные марки и модели.
    Контекст движения (номер, участок, скорость) передаётся в drive() извне.
    """

    __slots__ = ("_brand", "_model")

    def __init__(self, brand: str, model: str) -> None:
        self._brand: str = brand
        self._model: str = model

    @property
    def brand(self) -> str:
        return self._brand

    @property
    def model(self) -> str:
        return self._model

    def drive(self, license_plate: str, road_segment: str, speed_kmh: int) -> None:
        print(
            f"[{license_plate}] {self._brand} {self._model} — "
            f"участок «{road_segment}», {speed_kmh} км/ч"
        )


class CarFactory:
    """Фабрика приспособленцев: создаёт автомобиль по марке/модели и кэширует экземпляры."""

    def __init__(self) -> None:
        self._pool: Dict[Tuple[str, str], Car] = {}

    def get_car(self, brand: str, model: str) -> Car:
        key: Tuple[str, str] = (brand, model)
        if key not in self._pool:
            self._pool[key] = Car(brand, model)
        return self._pool[key]

    def unique_models_count(self) -> int:
        return len(self._pool)


def simulate_traffic(factory: CarFactory) -> None:
    """Демонстрация: много машин на дороге, мало уникальных объектов Car в памяти."""
    trips: list[tuple[str, str, str, str, int]] = [
        ("Toyota", "Camry", "A001AA", "Центр", 50),
        ("Toyota", "Camry", "B777BB", "Набережная", 60),
        ("Toyota", "Camry", "C999CC", "Кольцо", 40),
        ("Kia", "Rio", "D010DD", "Центр", 45),
        ("Kia", "Rio", "E020EE", "Кольцо", 55),
        ("Kia", "Rio", "F030FF", "Набережная", 50),
        ("Volkswagen", "Polo", "G040GG", "Центр", 48),
        ("Volkswagen", "Polo", "H050HH", "Кольцо", 52),
    ]
    print("Моделирование потока (один объект Car на пару марка+модель):\n")
    for brand, model, plate, segment, speed in trips:
        car = factory.get_car(brand, model)
        car.drive(plate, segment, speed)
    print(
        f"\nУникальных шаблонов автомобилей в пуле: {factory.unique_models_count()} "
        f"(всего проездов: {len(trips)})"
    )


def main() -> None:
    simulate_traffic(CarFactory())


class TestFlyweightCars(unittest.TestCase):
    def test_factory_reuses_same_car_instance(self) -> None:
        factory = CarFactory()
        c1 = factory.get_car("Toyota", "Camry")
        c2 = factory.get_car("Toyota", "Camry")
        self.assertIs(c1, c2)
        self.assertEqual(factory.unique_models_count(), 1)

    def test_different_brand_or_model_is_different_instance(self) -> None:
        factory = CarFactory()
        a = factory.get_car("Toyota", "Camry")
        b = factory.get_car("Toyota", "Corolla")
        c = factory.get_car("Kia", "Camry")
        self.assertIsNot(a, b)
        self.assertIsNot(a, c)
        self.assertEqual(factory.unique_models_count(), 3)

    def test_drive_prints_intrinsic_and_extrinsic(self) -> None:
        car = Car("Kia", "Rio")
        buf = io.StringIO()
        with redirect_stdout(buf):
            car.drive("X123XX", "МКАД", 90)
        out = buf.getvalue()
        self.assertIn("Kia", out)
        self.assertIn("Rio", out)
        self.assertIn("X123XX", out)
        self.assertIn("МКАД", out)
        self.assertIn("90", out)

    def test_pool_size_smaller_than_trips_when_reusing(self) -> None:
        factory = CarFactory()
        for _ in range(100):
            factory.get_car("Same", "Model")
        self.assertEqual(factory.unique_models_count(), 1)


if __name__ == "__main__":
    main()
