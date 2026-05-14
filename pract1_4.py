"""Практическая работа №1: параллельное асинхронное чтение нескольких файлов."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Iterable, List


async def read_file_async(path: Path, encoding: str = "utf-8") -> str:
    """Читает текст файла в пуле потоков, не блокируя цикл событий."""

    def _read() -> str:
        return path.read_text(encoding=encoding)

    return await asyncio.to_thread(_read)


async def read_files_parallel(paths: Iterable[Path], encoding: str = "utf-8") -> List[str]:
    """Читает несколько файлов параллельно; порядок результатов совпадает с порядком путей."""
    path_list: List[Path] = list(paths)
    tasks = [read_file_async(p, encoding=encoding) for p in path_list]
    return list(await asyncio.gather(*tasks))


async def print_files_contents(paths: Iterable[Path], encoding: str = "utf-8") -> None:
    """Читает файлы параллельно и выводит содержимое каждого на экран."""
    path_list: List[Path] = list(paths)
    contents: List[str] = await read_files_parallel(path_list, encoding=encoding)
    for path, text in zip(path_list, contents):
        print(f"===== {path.name} =====")
        print(text.rstrip("\n"))
        print()


def default_data_paths(base_dir: Path | None = None) -> List[Path]:
    """Пути к демонстрационным файлам pract1_4_data1.txt и pract1_4_data2.txt."""
    root: Path = base_dir if base_dir is not None else Path(__file__).resolve().parent
    return [root / "pract1_4_data1.txt", root / "pract1_4_data2.txt"]


async def main() -> None:
    paths: List[Path] = default_data_paths()
    missing: List[Path] = [p for p in paths if not p.is_file()]
    if missing:
        names: str = ", ".join(p.name for p in missing)
        print(f"Не найдены файлы: {names}", file=sys.stderr)
        sys.exit(1)
    await print_files_contents(paths)


class TestPract1AsyncRead(unittest.IsolatedAsyncioTestCase):
    async def test_read_file_async_returns_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "one.txt"
            p.write_text("hello-async", encoding="utf-8")
            text: str = await read_file_async(p)
            self.assertEqual(text, "hello-async")

    async def test_read_files_parallel_preserves_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "a.txt").write_text("A", encoding="utf-8")
            (base / "b.txt").write_text("B", encoding="utf-8")
            (base / "c.txt").write_text("C", encoding="utf-8")
            paths: List[Path] = [base / "a.txt", base / "b.txt", base / "c.txt"]
            out: List[str] = await read_files_parallel(paths)
            self.assertEqual(out, ["A", "B", "C"])

    async def test_read_file_async_missing_raises(self) -> None:
        missing_path: Path = Path(tempfile.gettempdir()) / "pract1_4_nonexistent_file_xyz.txt"
        with self.assertRaises(FileNotFoundError):
            await read_file_async(missing_path)


if __name__ == "__main__":
    asyncio.run(main())
