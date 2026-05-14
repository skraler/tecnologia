"""Практическая работа №1: асинхронная обработка набора файлов с числовыми заданиями (pract1_7)."""

from __future__ import annotations

import asyncio
import glob
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Sequence


def calculate_median(numbers: List[float]) -> float:
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n % 2 == 0:
        return (sorted_numbers[n // 2 - 1] + sorted_numbers[n // 2]) / 2.0
    return sorted_numbers[n // 2]


def calculate_arithmetic_mean(numbers: List[float]) -> float:
    return sum(numbers) / len(numbers) if numbers else 0.0


def calculate_rms(numbers: List[float]) -> float:
    if not numbers:
        return 0.0
    sum_squares = sum(x * x for x in numbers)
    return (sum_squares / len(numbers)) ** 0.5


def calculate_sum_of_roots(numbers: List[float]) -> float:
    return sum(x**0.5 for x in numbers if x >= 0)


def calculate_minimum(numbers: List[float]) -> float:
    return min(numbers) if numbers else 0.0


def calculate_maximum(numbers: List[float]) -> float:
    return max(numbers) if numbers else 0.0


def process_data_file_sync(path: Path, encoding: str = "utf-8") -> float:
    """Синхронно читает файл: строка 1 — код действия, строка 2 — числа через пробел."""
    lines = path.read_text(encoding=encoding).splitlines()
    if len(lines) < 2:
        return 0.0
    action = int(lines[0].strip())
    numbers = [float(x) for x in lines[1].strip().split()]
    if action == 1:
        return calculate_median(numbers)
    if action == 2:
        return calculate_arithmetic_mean(numbers)
    if action == 3:
        return calculate_rms(numbers)
    if action == 4:
        return calculate_sum_of_roots(numbers)
    if action == 5:
        return calculate_minimum(numbers)
    if action == 6:
        return calculate_maximum(numbers)
    return 0.0


async def process_file_task(path: Path, encoding: str = "utf-8") -> float:
    """Одна асинхронная задача: вычисление по одному файлу (без блокировки цикла событий)."""
    return await asyncio.to_thread(process_data_file_sync, path, encoding)


async def sum_results_for_files(paths: Sequence[Path], encoding: str = "utf-8") -> float:
    """Запускает по задаче на файл и возвращает сумму результатов."""
    path_list: List[Path] = list(paths)
    tasks = [asyncio.create_task(process_file_task(p, encoding=encoding), name=p.name) for p in path_list]
    results: List[float] = await asyncio.gather(*tasks)
    return float(sum(results))


def discover_data_files(directory: Path, pattern: str = "pract1_7_data_*.txt") -> List[Path]:
    """Возвращает отсортированный список путей к файлам данных в каталоге."""
    search = str(directory / pattern)
    return sorted(Path(p) for p in glob.glob(search))


async def run_pipeline(
    data_dir: Path | None = None,
    output_name: str = "out_pract1_7.dat",
    encoding: str = "utf-8",
) -> float:
    root: Path = data_dir if data_dir is not None else Path(__file__).resolve().parent
    paths: List[Path] = discover_data_files(root)
    if not paths:
        print(f"В каталоге {root} не найдены файлы по шаблону pract1_7_data_*.txt", file=sys.stderr)
        sys.exit(1)
    total: float = await sum_results_for_files(paths, encoding=encoding)
    out_path: Path = root / output_name
    out_path.write_text(str(total), encoding=encoding)
    print(f"Обработано файлов: {len(paths)}. Сумма результатов записана в {out_path.name}: {total}")
    return total


def main() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run_pipeline())


class TestPract17AsyncFiles(unittest.IsolatedAsyncioTestCase):
    def test_process_data_file_median_and_mean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            f1 = base / "a.txt"
            f1.write_text("1\n1.0 3.0 5.0\n", encoding="utf-8")
            self.assertEqual(process_data_file_sync(f1), 3.0)
            f2 = base / "b.txt"
            f2.write_text("2\n2.0 4.0 6.0\n", encoding="utf-8")
            self.assertEqual(process_data_file_sync(f2), 4.0)

    def test_unknown_action_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("99\n1.0 2.0\n", encoding="utf-8")
            self.assertEqual(process_data_file_sync(p), 0.0)

    async def test_async_sum_matches_sequential(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "d1.txt").write_text("5\n10.0 3.0\n", encoding="utf-8")
            (base / "d2.txt").write_text("6\n1.0 2.0 9.0\n", encoding="utf-8")
            paths = [base / "d1.txt", base / "d2.txt"]
            sequential = sum(process_data_file_sync(p) for p in paths)
            async_sum = await sum_results_for_files(paths)
            self.assertAlmostEqual(async_sum, sequential, places=10)
            self.assertEqual(async_sum, 3.0 + 9.0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        unittest.main(argv=[__name__, "-v"] + sys.argv[2:])
    else:
        main()
