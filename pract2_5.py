"""Практическая работа №2: шаблон «Итератор» для обхода коллекции книг (pract2_5)."""
from __future__ import annotations

import unittest
from typing import List, Optional


class Book:
    """Книга: название, автор, год издания."""

    def __init__(self, title: str, author: str, year: int) -> None:
        self._title: str = title
        self._author: str = author
        self._year: int = year

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def year(self) -> int:
        return self._year

    def info(self) -> str:
        return f'«{self._title}» — {self._author}, {self._year} г.'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return (
            self._title == other._title
            and self._author == other._author
            and self._year == other._year
        )


class BookIterator:
    """Итератор по коллекции книг (GoF Iterator)."""

    def __init__(self, books: List[Book]) -> None:
        self._books: List[Book] = list(books)
        self._index: int = 0

    def has_next(self) -> bool:
        return self._index < len(self._books)

    def next(self) -> Book:
        if not self.has_next():
            raise StopIteration("Элементов больше нет")
        book: Book = self._books[self._index]
        self._index += 1
        return book

    def reset(self) -> None:
        self._index = 0

    @property
    def position(self) -> int:
        return self._index


class BookCollection:
    """Агрегат: коллекция книг, создаёт итератор для обхода."""

    def __init__(self) -> None:
        self._books: List[Book] = []

    def add_book(self, book: Book) -> None:
        self._books.append(book)

    def count(self) -> int:
        return len(self._books)

    def create_iterator(self) -> BookIterator:
        return BookIterator(self._books)


def print_books_with_iterator(collection: BookCollection) -> None:
    """Обходит коллекцию через BookIterator и выводит сведения о каждой книге."""
    iterator: BookIterator = collection.create_iterator()
    index: int = 1
    while iterator.has_next():
        book: Book = iterator.next()
        print(f"{index}. {book.info()}")
        index += 1


def build_demo_collection() -> BookCollection:
    """Демонстрационная коллекция книг."""
    collection: BookCollection = BookCollection()
    collection.add_book(Book("Война и мир", "Л. Н. Толстой", 1869))
    collection.add_book(Book("Преступление и наказание", "Ф. М. Достоевский", 1866))
    collection.add_book(Book("Мастер и Маргарита", "М. А. Булгаков", 1967))
    collection.add_book(Book("Евгений Онегин", "А. С. Пушкин", 1833))
    return collection


def main() -> None:
    collection: BookCollection = build_demo_collection()
    print(f"Коллекция книг ({collection.count()} шт.):\n")
    print_books_with_iterator(collection)


class TestPract25Iterator(unittest.TestCase):
    def test_book_info_format(self) -> None:
        book: Book = Book("Идиот", "Ф. М. Достоевский", 1869)
        self.assertEqual(book.info(), "«Идиот» — Ф. М. Достоевский, 1869 г.")

    def test_iterator_traverses_all_books(self) -> None:
        collection: BookCollection = BookCollection()
        b1 = Book("A", "Author A", 2000)
        b2 = Book("B", "Author B", 2001)
        collection.add_book(b1)
        collection.add_book(b2)
        iterator: BookIterator = collection.create_iterator()
        seen: List[Book] = []
        while iterator.has_next():
            seen.append(iterator.next())
        self.assertEqual(seen, [b1, b2])
        self.assertFalse(iterator.has_next())

    def test_iterator_next_raises_when_exhausted(self) -> None:
        collection: BookCollection = BookCollection()
        collection.add_book(Book("X", "Y", 1999))
        iterator: BookIterator = collection.create_iterator()
        _ = iterator.next()
        with self.assertRaises(StopIteration):
            iterator.next()

    def test_empty_collection_iterator(self) -> None:
        collection: BookCollection = BookCollection()
        iterator: BookIterator = collection.create_iterator()
        self.assertEqual(collection.count(), 0)
        self.assertFalse(iterator.has_next())

    def test_iterator_reset(self) -> None:
        collection: BookCollection = build_demo_collection()
        iterator: BookIterator = collection.create_iterator()
        first_pass: List[Optional[str]] = []
        while iterator.has_next():
            first_pass.append(iterator.next().title)
        iterator.reset()
        second_pass: List[Optional[str]] = []
        while iterator.has_next():
            second_pass.append(iterator.next().title)
        self.assertEqual(first_pass, second_pass)
        self.assertEqual(len(first_pass), collection.count())


if __name__ == "__main__":
    main()
