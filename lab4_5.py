"""Лабораторная работа №4: структурный шаблон «Компоновщик» (организационная структура)."""

from __future__ import annotations

import io
import sys
import unittest
from abc import ABC, abstractmethod
from contextlib import redirect_stdout
from typing import List


class OrganizationComponent(ABC):
    """Базовый компонент организационной структуры (участник паттерна «Компоновщик»)."""

    def add(self, component: OrganizationComponent) -> None:
        raise NotImplementedError(
            "Добавление дочерних элементов поддерживается только для подразделений"
        )

    def remove(self, component: OrganizationComponent) -> None:
        raise NotImplementedError(
            "Удаление дочерних элементов поддерживается только для подразделений"
        )

    @abstractmethod
    def display(self, indent: int = 0) -> None:
        """Выводит описание компонента в консоль с отступом по уровню вложенности."""


class Employee(OrganizationComponent):
    """Лист дерева: сотрудник без подчинённых."""

    def __init__(self, name: str, position: str) -> None:
        self._name: str = name
        self._position: str = position

    @property
    def name(self) -> str:
        return self._name

    @property
    def position(self) -> str:
        return self._position

    def display(self, indent: int = 0) -> None:
        prefix: str = "  " * indent
        print(f"{prefix}Сотрудник: {self._name} — {self._position}")


class Department(OrganizationComponent):
    """Узел дерева: подразделение, объединяющее сотрудников и вложенные отделы."""

    def __init__(self, name: str) -> None:
        self._name: str = name
        self._children: List[OrganizationComponent] = []

    @property
    def name(self) -> str:
        return self._name

    def add(self, component: OrganizationComponent) -> None:
        self._children.append(component)

    def remove(self, component: OrganizationComponent) -> None:
        try:
            self._children.remove(component)
        except ValueError as exc:
            raise ValueError("Компонент не входит в состав подразделения") from exc

    def display(self, indent: int = 0) -> None:
        prefix: str = "  " * indent
        print(f"{prefix}Подразделение: {self._name}")
        for child in self._children:
            child.display(indent + 1)


def build_demo_company() -> Department:
    """Собирает пример иерархии для консольной демонстрации."""
    company = Department("ООО «Техно»")
    it = Department("ИТ-отдел")
    it.add(Employee("Анна Смирнова", "Руководитель отдела"))
    it.add(Employee("Иван Петров", "Инженер ПО"))
    hr = Department("Отдел кадров")
    hr.add(Employee("Мария Козлова", "HR-менеджер"))
    company.add(it)
    company.add(hr)
    company.add(Employee("Сергей Волков", "Генеральный директор"))
    return company


def main() -> None:
    print("Организационная структура компании:\n")
    root: Department = build_demo_company()
    root.display(0)


class TestCompositeOrganization(unittest.TestCase):
    """Минимальный набор тестов для шаблона «Компоновщик»."""

    def test_employee_display_contains_name_and_position(self) -> None:
        emp: Employee = Employee("Тест Тестов", "Аналитик")
        buf: io.StringIO = io.StringIO()
        with redirect_stdout(buf):
            emp.display(0)
        out: str = buf.getvalue()
        self.assertIn("Тест Тестов", out)
        self.assertIn("Аналитик", out)
        self.assertIn("Сотрудник", out)

    def test_employee_add_raises_not_implemented(self) -> None:
        emp: Employee = Employee("Лист", "Должность")
        other: Employee = Employee("Другой", "Роль")
        with self.assertRaises(NotImplementedError):
            emp.add(other)

    def test_employee_remove_raises_not_implemented(self) -> None:
        emp: Employee = Employee("Лист", "Должность")
        other: Employee = Employee("Другой", "Роль")
        with self.assertRaises(NotImplementedError):
            emp.remove(other)

    def test_department_add_and_nested_display(self) -> None:
        dept: Department = Department("Отдел А")
        dept.add(Employee("Сотрудник 1", "Инженер"))
        inner: Department = Department("Группа Б")
        inner.add(Employee("Сотрудник 2", "Тестировщик"))
        dept.add(inner)
        buf: io.StringIO = io.StringIO()
        with redirect_stdout(buf):
            dept.display(0)
        lines: List[str] = [line.strip() for line in buf.getvalue().splitlines() if line.strip()]
        self.assertTrue(any("Отдел А" in line for line in lines))
        self.assertTrue(any("Сотрудник 1" in line for line in lines))
        self.assertTrue(any("Группа Б" in line for line in lines))
        self.assertTrue(any("Сотрудник 2" in line for line in lines))

    def test_department_remove_child(self) -> None:
        dept: Department = Department("Один отдел")
        e1: Employee = Employee("Первый", "Роль")
        e2: Employee = Employee("Второй", "Роль")
        dept.add(e1)
        dept.add(e2)
        dept.remove(e1)
        buf: io.StringIO = io.StringIO()
        with redirect_stdout(buf):
            dept.display(0)
        out: str = buf.getvalue()
        self.assertIn("Второй", out)
        self.assertNotIn("Первый", out)

    def test_department_remove_unknown_raises(self) -> None:
        dept: Department = Department("X")
        orphan: Employee = Employee("Не в отделе", "Y")
        with self.assertRaises(ValueError):
            dept.remove(orphan)


if __name__ == "__main__":
    main()
