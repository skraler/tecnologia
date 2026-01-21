import glob
import os
import tempfile
import unittest
from multiprocessing import Pool
from typing import List


def find_existing_files(pattern: str = 'lab2_data_*.txt', output_dir: str = '.') -> List[str]:
    search_pattern = os.path.join(output_dir, pattern)
    file_paths = sorted(glob.glob(search_pattern))
    return file_paths


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
    return sum(x ** 0.5 for x in numbers if x >= 0)


def calculate_minimum(numbers: List[float]) -> float:
    return min(numbers) if numbers else 0.0


def calculate_maximum(numbers: List[float]) -> float:
    return max(numbers) if numbers else 0.0


def process_file(file_path: str) -> float:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
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


def process_files_parallel(file_paths: List[str]) -> float:
    num_processes = len(file_paths)
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_file, file_paths)
    return sum(results)


def main() -> None:
    output_file = 'out.dat'
    file_paths = find_existing_files()
    if not file_paths:
        print('Файлы lab2_data_*.txt не найдены в текущей директории')
        return
    num_processes = len(file_paths)
    print(f'Найдено {num_processes} файлов для обработки')
    print(f'Создано {num_processes} процессов')
    total_sum = process_files_parallel(file_paths)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(total_sum))
    print(f'Сумма результатов вычислений записана в {output_file}: {total_sum}')


class TestLab2Functions(unittest.TestCase):
    def test_calculate_median_odd_count(self) -> None:
        numbers = [1.0, 3.0, 5.0, 7.0, 9.0]
        result = calculate_median(numbers)
        self.assertEqual(result, 5.0)

    def test_calculate_median_even_count(self) -> None:
        numbers = [1.0, 2.0, 3.0, 4.0]
        result = calculate_median(numbers)
        self.assertEqual(result, 2.5)

    def test_calculate_median_single_element(self) -> None:
        numbers = [42.0]
        result = calculate_median(numbers)
        self.assertEqual(result, 42.0)

    def test_calculate_median_unsorted(self) -> None:
        numbers = [9.0, 1.0, 5.0, 3.0, 7.0]
        result = calculate_median(numbers)
        self.assertEqual(result, 5.0)

    def test_calculate_arithmetic_mean_simple(self) -> None:
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_arithmetic_mean(numbers)
        self.assertEqual(result, 3.0)

    def test_calculate_arithmetic_mean_single_element(self) -> None:
        numbers = [10.0]
        result = calculate_arithmetic_mean(numbers)
        self.assertEqual(result, 10.0)

    def test_calculate_arithmetic_mean_negative(self) -> None:
        numbers = [-5.0, 10.0, -3.0]
        result = calculate_arithmetic_mean(numbers)
        self.assertAlmostEqual(result, 0.6666666666666666, places=10)

    def test_calculate_arithmetic_mean_empty(self) -> None:
        numbers: List[float] = []
        result = calculate_arithmetic_mean(numbers)
        self.assertEqual(result, 0.0)

    def test_calculate_rms_simple(self) -> None:
        numbers = [3.0, 4.0]
        result = calculate_rms(numbers)
        expected = ((3.0 * 3.0 + 4.0 * 4.0) / 2.0) ** 0.5
        self.assertAlmostEqual(result, expected, places=10)

    def test_calculate_rms_single_element(self) -> None:
        numbers = [5.0]
        result = calculate_rms(numbers)
        self.assertEqual(result, 5.0)

    def test_calculate_rms_empty(self) -> None:
        numbers: List[float] = []
        result = calculate_rms(numbers)
        self.assertEqual(result, 0.0)

    def test_calculate_sum_of_roots_simple(self) -> None:
        numbers = [4.0, 9.0, 16.0]
        result = calculate_sum_of_roots(numbers)
        expected = 2.0 + 3.0 + 4.0
        self.assertAlmostEqual(result, expected, places=10)

    def test_calculate_sum_of_roots_with_negative(self) -> None:
        numbers = [4.0, -5.0, 9.0, -1.0]
        result = calculate_sum_of_roots(numbers)
        expected = 2.0 + 3.0
        self.assertAlmostEqual(result, expected, places=10)

    def test_calculate_sum_of_roots_zero(self) -> None:
        numbers = [0.0, 4.0, 9.0]
        result = calculate_sum_of_roots(numbers)
        expected = 0.0 + 2.0 + 3.0
        self.assertAlmostEqual(result, expected, places=10)

    def test_calculate_minimum_simple(self) -> None:
        numbers = [5.0, 2.0, 8.0, 1.0, 9.0]
        result = calculate_minimum(numbers)
        self.assertEqual(result, 1.0)

    def test_calculate_minimum_single_element(self) -> None:
        numbers = [42.0]
        result = calculate_minimum(numbers)
        self.assertEqual(result, 42.0)

    def test_calculate_minimum_negative(self) -> None:
        numbers = [-5.0, -1.0, -10.0, -3.0]
        result = calculate_minimum(numbers)
        self.assertEqual(result, -10.0)

    def test_calculate_minimum_empty(self) -> None:
        numbers: List[float] = []
        result = calculate_minimum(numbers)
        self.assertEqual(result, 0.0)

    def test_calculate_maximum_simple(self) -> None:
        numbers = [5.0, 2.0, 8.0, 1.0, 9.0]
        result = calculate_maximum(numbers)
        self.assertEqual(result, 9.0)

    def test_calculate_maximum_single_element(self) -> None:
        numbers = [42.0]
        result = calculate_maximum(numbers)
        self.assertEqual(result, 42.0)

    def test_calculate_maximum_negative(self) -> None:
        numbers = [-5.0, -1.0, -10.0, -3.0]
        result = calculate_maximum(numbers)
        self.assertEqual(result, -1.0)

    def test_calculate_maximum_empty(self) -> None:
        numbers: List[float] = []
        result = calculate_maximum(numbers)
        self.assertEqual(result, 0.0)

    def test_process_files_parallel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, 'test1.txt')
            file2 = os.path.join(temp_dir, 'test2.txt')
            file3 = os.path.join(temp_dir, 'test3.txt')
            with open(file1, 'w', encoding='utf-8') as f:
                f.write('2\n1.0 2.0 3.0\n')
            with open(file2, 'w', encoding='utf-8') as f:
                f.write('5\n4.0 5.0 6.0\n')
            with open(file3, 'w', encoding='utf-8') as f:
                f.write('6\n7.0 8.0 9.0\n')
            file_paths = [file1, file2, file3]
            result = process_files_parallel(file_paths)
            expected = (1.0 + 2.0 + 3.0) / 3.0 + min(4.0, 5.0, 6.0) + max(7.0, 8.0, 9.0)
            self.assertAlmostEqual(result, expected, places=10)


if __name__ == '__main__':
    main()
