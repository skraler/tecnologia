import unittest
from threading import Thread, Lock
from typing import List, Tuple, Callable, Any


def process_range(
    data: List[float],
    start: int,
    end: int,
    thread_id: int,
    result_dict: dict,
    lock: Lock,
    operation: Callable[[List[float]], float],
) -> None:
    range_data = data[start:end]
    if not range_data:
        return

    result = operation(range_data)
    with lock:
        result_dict[thread_id] = {
            'range': (start, end),
            'result': result,
            'processed_count': len(range_data),
        }
        print(f'Поток {thread_id}: обработан диапазон [{start}, {end}), результат: {result}')


def divide_ranges(
    data_length: int,
    num_threads: int,
) -> List[Tuple[int, int]]:
    if data_length == 0:
        return []

    chunk_size = data_length // num_threads
    ranges = []

    for i in range(num_threads):
        start = i * chunk_size
        if i == num_threads - 1:
            end = data_length
        else:
            end = (i + 1) * chunk_size
        ranges.append((start, end))

    return ranges


def find_max_value(data: List[float]) -> float:
    return max(data)


def find_min_value(data: List[float]) -> float:
    return min(data)


def calculate_sum(data: List[float]) -> float:
    return sum(data)


def process_list_with_threads(
    data: List[float],
    num_threads: int = 3,
    operation: Callable[[List[float]], float] = find_max_value,
) -> dict[str, Any]:
    if not data:
        return {'error': 'Список пуст'}

    ranges = divide_ranges(len(data), num_threads)
    result_dict: dict = {}
    lock = Lock()
    threads: List[Thread] = []

    for thread_id, (start, end) in enumerate(ranges):
        thread = Thread(
            target=process_range,
            args=(data, start, end, thread_id, result_dict, lock, operation),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return result_dict


class TestLab1Functions(unittest.TestCase):
    def test_find_max_value_simple(self) -> None:
        data = [1.0, 5.0, 3.0, 9.0, 2.0]
        result = find_max_value(data)
        self.assertEqual(result, 9.0)

    def test_find_max_value_single_element(self) -> None:
        data = [42.0]
        result = find_max_value(data)
        self.assertEqual(result, 42.0)

    def test_find_max_value_negative(self) -> None:
        data = [-5.0, -1.0, -10.0, -3.0]
        result = find_max_value(data)
        self.assertEqual(result, -1.0)

    def test_find_min_value_simple(self) -> None:
        data = [1.0, 5.0, 3.0, 9.0, 2.0]
        result = find_min_value(data)
        self.assertEqual(result, 1.0)

    def test_find_min_value_single_element(self) -> None:
        data = [42.0]
        result = find_min_value(data)
        self.assertEqual(result, 42.0)

    def test_find_min_value_negative(self) -> None:
        data = [-5.0, -1.0, -10.0, -3.0]
        result = find_min_value(data)
        self.assertEqual(result, -10.0)

    def test_calculate_sum_simple(self) -> None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_sum(data)
        self.assertEqual(result, 15.0)

    def test_calculate_sum_single_element(self) -> None:
        data = [42.0]
        result = calculate_sum(data)
        self.assertEqual(result, 42.0)

    def test_calculate_sum_negative(self) -> None:
        data = [-5.0, 10.0, -3.0]
        result = calculate_sum(data)
        self.assertEqual(result, 2.0)

    def test_calculate_sum_empty(self) -> None:
        data: list[float] = []
        result = calculate_sum(data)
        self.assertEqual(result, 0.0)

    def test_divide_ranges(self) -> None:
        ranges = divide_ranges(12, 3)
        expected = [(0, 4), (4, 8), (8, 12)]
        self.assertEqual(ranges, expected)

    def test_process_list_with_threads_max(self) -> None:
        data = [1.5, 2.3, 4.7, 3.2, 5.1, 6.8, 7.4, 8.9, 9.2, 10.5, 11.3, 12.7]
        results = process_list_with_threads(data, num_threads=3, operation=find_max_value)
        overall_max = max(result['result'] for result in results.values())
        expected_max = max(data)
        self.assertEqual(overall_max, expected_max)

    def test_process_list_with_threads_min(self) -> None:
        data = [1.5, 2.3, 4.7, 3.2, 5.1, 6.8, 7.4, 8.9, 9.2, 10.5, 11.3, 12.7]
        results = process_list_with_threads(data, num_threads=3, operation=find_min_value)
        overall_min = min(result['result'] for result in results.values())
        expected_min = min(data)
        self.assertEqual(overall_min, expected_min)

    def test_process_list_with_threads_sum(self) -> None:
        data = [1.5, 2.3, 4.7, 3.2, 5.1, 6.8, 7.4, 8.9, 9.2, 10.5, 11.3, 12.7]
        results = process_list_with_threads(data, num_threads=3, operation=calculate_sum)
        overall_sum = sum(result['result'] for result in results.values())
        expected_sum = sum(data)
        self.assertAlmostEqual(overall_sum, expected_sum, places=10)

    def test_process_list_with_threads_sum_different_list(self) -> None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        results = process_list_with_threads(data, num_threads=3, operation=calculate_sum)
        overall_sum = sum(result['result'] for result in results.values())
        expected_sum = sum(data)
        self.assertAlmostEqual(overall_sum, expected_sum, places=10)

    def test_process_list_with_threads_sum_small_list(self) -> None:
        data = [1.0, 2.0, 3.0]
        results = process_list_with_threads(data, num_threads=3, operation=calculate_sum)
        overall_sum = sum(result['result'] for result in results.values())
        expected_sum = sum(data)
        self.assertAlmostEqual(overall_sum, expected_sum, places=10)

    def test_process_list_with_threads_empty_list(self) -> None:
        data: list[float] = []
        results = process_list_with_threads(data, num_threads=3, operation=find_max_value)
        self.assertIn('error', results)

    def test_process_list_with_threads_single_element(self) -> None:
        data = [42.0]
        results = process_list_with_threads(data, num_threads=3, operation=find_max_value)
        overall_max = max(result['result'] for result in results.values())
        self.assertEqual(overall_max, 42.0)


if __name__ == '__main__':
    test_data = [1.5, 2.3, 4.7, 3.2, 5.1, 6.8, 7.4, 8.9, 9.2, 10.5, 11.3, 12.7]

    print(f'Исходный список: {test_data}')
    print(f'Длина списка: {len(test_data)}')

    print('\n' + '='*60)
    print('Поиск максимального значения:')
    print('='*60)
    results_max = process_list_with_threads(test_data, num_threads=3, operation=find_max_value)
    print('\nРезультаты работы потоков:')
    for thread_id in sorted(results_max.keys()):
        info = results_max[thread_id]
        print(
            f'Поток {thread_id}: диапазон {info["range"]}, '
            f'обработано элементов: {info["processed_count"]}, '
            f'результат: {info["result"]}',
        )
    overall_max = max(result['result'] for result in results_max.values())
    print(f'\nОбщий максимальный результат: {overall_max}')

    print('\n' + '='*60)
    print('Поиск минимального значения:')
    print('='*60)
    results_min = process_list_with_threads(test_data, num_threads=3, operation=find_min_value)
    print('\nРезультаты работы потоков:')
    for thread_id in sorted(results_min.keys()):
        info = results_min[thread_id]
        print(
            f'Поток {thread_id}: диапазон {info["range"]}, '
            f'обработано элементов: {info["processed_count"]}, '
            f'результат: {info["result"]}',
        )
    overall_min = min(result['result'] for result in results_min.values())
    print(f'\nОбщий минимальный результат: {overall_min}')

    print('\n' + '='*60)
    print('Вычисление суммы:')
    print('='*60)
    results_sum = process_list_with_threads(test_data, num_threads=3, operation=calculate_sum)
    print('\nРезультаты работы потоков:')
    for thread_id in sorted(results_sum.keys()):
        info = results_sum[thread_id]
        print(
            f'Поток {thread_id}: диапазон {info["range"]}, '
            f'обработано элементов: {info["processed_count"]}, '
            f'результат: {info["result"]}',
        )
    overall_sum = sum(result['result'] for result in results_sum.values())
    print(f'\nОбщая сумма (сумма результатов потоков): {overall_sum}')
    print(f'Проверка (сумма всех элементов): {sum(test_data)}')
