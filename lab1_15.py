import os
import shutil
import time
import unittest
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Event, Lock, Thread
from typing import Any, Dict, List, Optional, Tuple


class ChangeType(Enum):
    CREATED = 'Создан'
    DELETED = 'Удален'
    MODIFIED = 'Изменен'
    MOVED = 'Перемещен'

    @property
    def plural(self) -> str:
        plurals = {
            ChangeType.CREATED: 'Создано файлов',
            ChangeType.DELETED: 'Удалено файлов',
            ChangeType.MODIFIED: 'Изменено файлов',
            ChangeType.MOVED: 'Перемещено файлов',
        }
        return plurals.get(self, self.value)


@dataclass
class FileChange:
    change_type: ChangeType
    path: str
    timestamp: datetime
    src_path: Optional[str] = None
    dest_path: Optional[str] = None


@dataclass
class FileState:
    path: str
    size: int
    mtime: float
    inode: Optional[int] = None


@dataclass
class DirectoryMonitorResult:
    directory: str
    changes: List[FileChange] = field(default_factory=list)
    is_running: bool = False
    error: Optional[str] = None


class DirectoryMonitor:
    def __init__(self, directories: List[str], poll_interval: float = 1.0) -> None:
        self.directories = directories
        self.results: Dict[str, DirectoryMonitorResult] = {}
        self.lock = Lock()
        self.stop_event = Event()
        self.threads: List[Thread] = []
        self.poll_interval = poll_interval

    @staticmethod
    def scan_directory(directory: str) -> Dict[str, FileState]:
        file_states: Dict[str, FileState] = {}
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                stat = os.stat(file_path)
                file_states[file_path] = FileState(
                    path=file_path,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                    inode=stat.st_ino if hasattr(stat, 'st_ino') else None,
                )
        return file_states

    @staticmethod
    def detect_changes(
        old_state: Dict[str, FileState],
        new_state: Dict[str, FileState],
    ) -> List[Tuple[ChangeType, str, Optional[str]]]:
        changes: List[Tuple[ChangeType, str, Optional[str]]] = []

        old_paths = set(old_state.keys())
        new_paths = set(new_state.keys())

        created_paths = new_paths - old_paths
        deleted_paths = old_paths - new_paths
        common_paths = old_paths & new_paths

        for path in created_paths:
            changes.append((ChangeType.CREATED, path, None))

        for path in deleted_paths:
            changes.append((ChangeType.DELETED, path, None))

        for path in common_paths:
            old_file = old_state[path]
            new_file = new_state[path]
            if old_file.size != new_file.size or old_file.mtime != new_file.mtime:
                changes.append((ChangeType.MODIFIED, path, None))

        inode_map_old: Dict[Optional[int], str] = {
            state.inode: path for path, state in old_state.items() if state.inode is not None
        }
        inode_map_new: Dict[Optional[int], str] = {
            state.inode: path for path, state in new_state.items() if state.inode is not None
        }

        for inode, old_path in inode_map_old.items():
            if inode and inode in inode_map_new:
                new_path = inode_map_new[inode]
                if old_path != new_path and old_path in deleted_paths and new_path in created_paths:
                    changes.append((ChangeType.MOVED, old_path, new_path))
                    if (ChangeType.CREATED, new_path, None) in changes:
                        changes.remove((ChangeType.CREATED, new_path, None))
                    if (ChangeType.DELETED, old_path, None) in changes:
                        changes.remove((ChangeType.DELETED, old_path, None))

        return changes

    def _monitor_directory(
        self,
        directory: str,
        result: DirectoryMonitorResult,
    ) -> None:
        if not os.path.isdir(directory):
            with self.lock:
                result.error = f'Каталог не существует: {directory}'
                result.is_running = False
            return

        try:
            previous_state: Dict[str, FileState] = {}
            first_scan = True

            with self.lock:
                result.is_running = True

            while not self.stop_event.is_set():
                current_state = self.scan_directory(directory)

                if not first_scan:
                    detected = self.detect_changes(previous_state, current_state)
                    for change_type, path, dest_path in detected:
                        change = FileChange(
                            change_type=change_type,
                            path=path,
                            timestamp=datetime.now(),
                            dest_path=dest_path,
                        )
                        with self.lock:
                            result.changes.append(change)
                else:
                    first_scan = False

                previous_state = current_state

                elapsed = 0.0
                while elapsed < self.poll_interval and not self.stop_event.is_set():
                    time.sleep(0.1)
                    elapsed += 0.1

            with self.lock:
                result.is_running = False

        except Exception as e:
            with self.lock:
                result.error = f'Ошибка при мониторинге {directory}: {str(e)}'
                result.is_running = False

    def start_monitoring(self) -> None:
        for directory in self.directories:
            result = DirectoryMonitorResult(directory=directory)
            self.results[directory] = result

            thread = Thread(
                target=self._monitor_directory,
                args=(directory, result),
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()

        time.sleep(0.5)

    def stop_monitoring(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=2.0)

    def get_all_changes(self) -> Dict[str, List[FileChange]]:
        with self.lock:
            return {
                directory: result.changes.copy()
                for directory, result in self.results.items()
            }

    def get_summary(self) -> Dict[str, Dict[str, int]]:
        with self.lock:
            summary: Dict[str, Dict[str, int]] = {}
            for directory, result in self.results.items():
                change_counts: Dict[str, int] = defaultdict(int)
                for change in result.changes:
                    change_counts[change.change_type.value] += 1
                summary[directory] = dict(change_counts)
            return summary

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        with self.lock:
            status: Dict[str, Dict[str, Any]] = {}
            for directory, result in self.results.items():
                status[directory] = {
                    'is_running': result.is_running,
                    'total_changes': len(result.changes),
                    'error': result.error,
                }
            return status

    @staticmethod
    def format_changes(changes: List[FileChange]) -> str:
        if not changes:
            return '  Изменений не обнаружено'

        lines: List[str] = []
        for change in changes:
            timestamp_str = change.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            change_type_ru = change.change_type.value

            if change.change_type == ChangeType.MOVED and change.dest_path:
                lines.append(
                    f'  [{timestamp_str}] {change_type_ru}: {change.path} -> {change.dest_path}',
                )
            else:
                lines.append(f'  [{timestamp_str}] {change_type_ru}: {change.path}')

        return '\n'.join(lines)

    def print_report(self) -> None:
        print('\n' + '=' * 80)
        print('ОТЧЕТ О МОНИТОРИНГЕ КАТАЛОГОВ')
        print('=' * 80)

        status = self.get_status()
        summary = self.get_summary()
        all_changes = self.get_all_changes()

        for directory in self.directories:
            print(f'\nКаталог: {directory}')
            print('-' * 80)

            dir_status = status.get(directory, {})
            if dir_status.get('error'):
                print(f'  ОШИБКА: {dir_status["error"]}')
                continue

            is_running = dir_status.get('is_running', False)
            total_changes = dir_status.get('total_changes', 0)
            print(f'  Статус: {"Активен" if is_running else "Остановлен"}')
            print(f'  Всего изменений: {total_changes}')

            dir_summary = summary.get(directory, {})
            if dir_summary:
                print('  Статистика по типам изменений:')
                for change_type_str, count in sorted(dir_summary.items()):
                    change_type = ChangeType(change_type_str)
                    print(f'    {change_type.plural}: {count}')

            changes = all_changes.get(directory, [])
            if changes:
                print('\n  Детали изменений:')
                print(self.format_changes(changes))


class TestDirectoryMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = os.path.join(os.getcwd(), 'test_monitor')
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self) -> None:
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_file_creation(self) -> None:
        monitor = DirectoryMonitor([self.test_dir], poll_interval=0.5)
        monitor.start_monitoring()
        time.sleep(0.6)

        test_file = os.path.join(self.test_dir, 'test1.txt')
        with open(test_file, 'w') as f:
            f.write('test content')

        time.sleep(1.0)
        monitor.stop_monitoring()

        changes = monitor.get_all_changes()
        self.assertIn(self.test_dir, changes)
        self.assertEqual(len(changes[self.test_dir]), 1)
        self.assertEqual(changes[self.test_dir][0].change_type, ChangeType.CREATED)
        self.assertEqual(changes[self.test_dir][0].path, test_file)

    def test_file_deletion(self) -> None:
        test_file = os.path.join(self.test_dir, 'test2.txt')
        with open(test_file, 'w') as f:
            f.write('test content')

        monitor = DirectoryMonitor([self.test_dir], poll_interval=0.5)
        monitor.start_monitoring()
        time.sleep(0.6)

        os.remove(test_file)
        time.sleep(1.0)
        monitor.stop_monitoring()

        changes = monitor.get_all_changes()
        self.assertIn(self.test_dir, changes)
        self.assertEqual(len(changes[self.test_dir]), 1)
        self.assertEqual(changes[self.test_dir][0].change_type, ChangeType.DELETED)
        self.assertEqual(changes[self.test_dir][0].path, test_file)

    def test_file_modification(self) -> None:
        test_file = os.path.join(self.test_dir, 'test3.txt')
        with open(test_file, 'w') as f:
            f.write('initial content')

        monitor = DirectoryMonitor([self.test_dir], poll_interval=0.5)
        monitor.start_monitoring()
        time.sleep(0.6)

        with open(test_file, 'w') as f:
            f.write('modified content')

        time.sleep(1.0)
        monitor.stop_monitoring()

        changes = monitor.get_all_changes()
        self.assertIn(self.test_dir, changes)
        self.assertEqual(len(changes[self.test_dir]), 1)
        self.assertEqual(changes[self.test_dir][0].change_type, ChangeType.MODIFIED)
        self.assertEqual(changes[self.test_dir][0].path, test_file)

    def test_file_move(self) -> None:
        test_file1 = os.path.join(self.test_dir, 'test4.txt')
        test_file2 = os.path.join(self.test_dir, 'test4_moved.txt')
        with open(test_file1, 'w') as f:
            f.write('content to move')

        monitor = DirectoryMonitor([self.test_dir], poll_interval=0.5)
        monitor.start_monitoring()
        time.sleep(0.6)

        os.rename(test_file1, test_file2)
        time.sleep(1.0)
        monitor.stop_monitoring()

        changes = monitor.get_all_changes()
        self.assertIn(self.test_dir, changes)
        moved_changes = [
            c for c in changes[self.test_dir]
            if c.change_type == ChangeType.MOVED
        ]
        self.assertGreaterEqual(len(moved_changes), 1)
        if moved_changes:
            self.assertEqual(moved_changes[0].path, test_file1)
            self.assertEqual(moved_changes[0].dest_path, test_file2)

    def test_multiple_changes(self) -> None:
        test_file1 = os.path.join(self.test_dir, 'test5_1.txt')
        test_file2 = os.path.join(self.test_dir, 'test5_2.txt')
        test_file3 = os.path.join(self.test_dir, 'test5_3.txt')

        with open(test_file1, 'w') as f:
            f.write('initial')

        monitor = DirectoryMonitor([self.test_dir], poll_interval=0.5)
        monitor.start_monitoring()
        time.sleep(0.6)

        with open(test_file2, 'w') as f:
            f.write('new file')
        time.sleep(0.7)

        with open(test_file1, 'w') as f:
            f.write('modified')
        time.sleep(0.7)

        os.remove(test_file1)
        time.sleep(0.7)

        with open(test_file3, 'w') as f:
            f.write('another new file')

        time.sleep(1.0)
        monitor.stop_monitoring()

        changes = monitor.get_all_changes()
        self.assertIn(self.test_dir, changes)
        self.assertGreaterEqual(len(changes[self.test_dir]), 3)

        change_types = [c.change_type for c in changes[self.test_dir]]
        self.assertIn(ChangeType.CREATED, change_types)
        self.assertIn(ChangeType.MODIFIED, change_types)
        self.assertIn(ChangeType.DELETED, change_types)

        summary = monitor.get_summary()
        self.assertIn(self.test_dir, summary)
        dir_summary = summary[self.test_dir]
        self.assertGreater(dir_summary.get(ChangeType.CREATED.value, 0), 0)
        self.assertGreater(dir_summary.get(ChangeType.DELETED.value, 0), 0)
        self.assertGreater(dir_summary.get(ChangeType.MODIFIED.value, 0), 0)


if __name__ == '__main__':
    test_directories = [
        os.path.join(os.getcwd(), 'test_dir1'),
        os.path.join(os.getcwd(), 'test_dir2'),
    ]

    for directory in test_directories:
        os.makedirs(directory, exist_ok=True)

    print('Запуск мониторинга каталогов...')
    print(f'Отслеживаемые каталоги: {test_directories}')

    monitor = DirectoryMonitor(test_directories, poll_interval=1.0)
    monitor.start_monitoring()

    print('\nМониторинг запущен. Ожидание изменений (10 секунд)...')
    print('Вы можете создавать, изменять или удалять файлы в отслеживаемых каталогах.')

    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print('\nПрерывание по запросу пользователя...')

    monitor.stop_monitoring()
    monitor.print_report()
