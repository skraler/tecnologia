import glob
import os
import tempfile
import unittest
from multiprocessing import Pool
from typing import Dict, List, Tuple


def count_word_in_file(file_path: str, search_word: str) -> int:
    count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        words = content.split()
        for word in words:
            cleaned_word = word.strip(".,!?;:()[]{}'\"-").lower()
            if cleaned_word == search_word.lower():
                count += 1
    return count


def process_file_wrapper(args: Tuple[str, str]) -> Tuple[str, int]:
    file_path, search_word = args
    count = count_word_in_file(file_path, search_word)
    return file_path, count


def find_text_files(pattern: str = "search_text_*_lab2.txt", output_dir: str = ".") -> List[str]:
    search_pattern = os.path.join(output_dir, pattern)
    file_paths = sorted(glob.glob(search_pattern))
    return file_paths


def count_word_in_files_parallel(file_paths: List[str], search_word: str) -> Dict[str, int]:
    num_processes = len(file_paths)
    if num_processes == 0:
        return {}

    args_list = [(file_path, search_word) for file_path in file_paths]

    with Pool(processes=num_processes) as pool:
        results = pool.map(process_file_wrapper, args_list)

    return dict(results)


def main() -> None:
    search_word = input("Введите слово для поиска: ").strip()
    if not search_word:
        print("Слово не может быть пустым")
        return

    file_paths = find_text_files()
    if not file_paths:
        print("Файлы search_text_*_lab2.txt не найдены в текущей директории")
        print("Запустите create_text_files.py для создания тестовых файлов")
        return

    num_processes = len(file_paths)
    print(f"Найдено {num_processes} файлов для обработки")
    print(f"Создано {num_processes} процессов")
    print(f"Поиск слова '{search_word}'...")

    results = count_word_in_files_parallel(file_paths, search_word)

    total_count = sum(results.values())
    print("\nРезультаты поиска:")
    print("-" * 60)
    for file_path, count in results.items():
        filename = os.path.basename(file_path)
        print(f"{filename}: {count} вхождений")
    print("-" * 60)
    print(f"Общее количество вхождений слова '{search_word}': {total_count}")


class TestLab2Functions(unittest.TestCase):
    def test_count_word_in_file_simple(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Python is a powerful language. Python developers love Python.")
            temp_path = f.name

        try:
            result = count_word_in_file(temp_path, "Python")
            self.assertEqual(result, 3)
        finally:
            os.unlink(temp_path)

    def test_count_word_in_file_case_insensitive(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Python python PYTHON pYtHoN")
            temp_path = f.name

        try:
            result = count_word_in_file(temp_path, "python")
            self.assertEqual(result, 4)
        finally:
            os.unlink(temp_path)

    def test_count_word_in_file_with_punctuation(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Python, Python! Python? Python. (Python) [Python]")
            temp_path = f.name

        try:
            result = count_word_in_file(temp_path, "Python")
            self.assertEqual(result, 6)
        finally:
            os.unlink(temp_path)

    def test_count_word_in_file_no_matches(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Java is a programming language. JavaScript is different.")
            temp_path = f.name

        try:
            result = count_word_in_file(temp_path, "Python")
            self.assertEqual(result, 0)
        finally:
            os.unlink(temp_path)

    def test_count_word_in_file_empty_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = count_word_in_file(temp_path, "Python")
            self.assertEqual(result, 0)
        finally:
            os.unlink(temp_path)

    def test_count_word_in_file_partial_match(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Python Pythonic Pythonista")
            temp_path = f.name

        try:
            result = count_word_in_file(temp_path, "Python")
            self.assertEqual(result, 1)
        finally:
            os.unlink(temp_path)

    def test_count_word_in_files_parallel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "test1.txt")
            file2 = os.path.join(temp_dir, "test2.txt")
            file3 = os.path.join(temp_dir, "test3.txt")

            with open(file1, "w", encoding="utf-8") as f:
                f.write("Python is great. Python developers love Python.")
            with open(file2, "w", encoding="utf-8") as f:
                f.write("Python programming can be fun.")
            with open(file3, "w", encoding="utf-8") as f:
                f.write("Java and JavaScript are different languages.")

            file_paths = [file1, file2, file3]
            results = count_word_in_files_parallel(file_paths, "Python")

            self.assertEqual(len(results), 3)
            self.assertEqual(results[file1], 3)
            self.assertEqual(results[file2], 1)
            self.assertEqual(results[file3], 0)

            total_count = sum(results.values())
            self.assertEqual(total_count, 4)

    def test_count_word_in_files_parallel_empty_list(self) -> None:
        results = count_word_in_files_parallel([], "Python")
        self.assertEqual(results, {})

    def test_count_word_in_files_parallel_real_files(self) -> None:
        file_paths = find_text_files()
        if not file_paths:
            self.skipTest("Файлы search_text_*_lab2.txt не найдены")

        results = count_word_in_files_parallel(file_paths, "Python")

        self.assertEqual(len(results), 5)

        expected_counts = {
            "search_text_01_lab2.txt": 5,
            "search_text_02_lab2.txt": 1,
            "search_text_03_lab2.txt": 3,
            "search_text_04_lab2.txt": 2,
            "search_text_05_lab2.txt": 0,
        }

        for file_path, count in results.items():
            filename = os.path.basename(file_path)
            self.assertIn(filename, expected_counts)
            self.assertEqual(count, expected_counts[filename], f"Неверное количество в файле {filename}")

        total_count = sum(results.values())
        self.assertEqual(total_count, 11, "Общее количество вхождений должно быть 11")


if __name__ == "__main__":
    main()
