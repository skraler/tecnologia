from datetime import date

from lab3 import TransportCompanyDB


def init_database() -> None:
    db = TransportCompanyDB('transport_company.db')
    print('Создание базы данных и наполнение данными...')

    print('Добавление водителей...')
    driver1 = db.add_driver('Иван Петров', 'DL001', '+79001234567', 10)
    driver2 = db.add_driver('Сергей Сидоров', 'DL002', '+79001234568', 5)
    driver3 = db.add_driver('Алексей Иванов', 'DL003', '+79001234569', 15)
    driver4 = db.add_driver('Дмитрий Козлов', 'DL004', '+79001234570', 3)
    driver5 = db.add_driver('Михаил Соколов', 'DL005', '+79001234571', 8)
    print(f'  Добавлено 5 водителей (ID: {driver1.id}-{driver5.id})')

    print('Добавление транспортных средств...')
    vehicle1 = db.add_vehicle('Газель', 'А123БВ', 1500.0, None)
    vehicle2 = db.add_vehicle('МАЗ', 'В456ГД', 10000.0, driver1.id)
    vehicle3 = db.add_vehicle('Камаз', 'Е789ЖЗ', 20000.0, driver2.id)
    vehicle4 = db.add_vehicle('Фургон', 'И012КЛ', 800.0, None)
    vehicle5 = db.add_vehicle('Мерседес Спринтер', 'К345МН', 3500.0, driver3.id)
    print(f'  Добавлено 5 транспортных средств (ID: {vehicle1.id}-{vehicle5.id})')

    print('Добавление маршрутов...')
    route1 = db.add_route('Москва', 'Санкт-Петербург', 700.0, 10.0)
    route2 = db.add_route('Москва', 'Казань', 800.0, 12.0)
    route3 = db.add_route('Санкт-Петербург', 'Новосибирск', 3500.0, 48.0)
    route4 = db.add_route('Москва', 'Воронеж', 500.0, 7.0)
    route5 = db.add_route('Казань', 'Екатеринбург', 1200.0, 15.0)
    print(f'  Добавлено 5 маршрутов (ID: {route1.id}-{route5.id})')

    print('Добавление клиентов...')
    client1 = db.add_client(
        'ООО Торговый дом', '+74951234567', 'Москва, ул. Ленина, 1'
    )
    client2 = db.add_client(
        'ИП Смирнов', '+74951234568', 'Санкт-Петербург, пр. Невский, 10'
    )
    client3 = db.add_client(
        'ЗАО Промышленность', '+74951234569', 'Казань, ул. Баумана, 5'
    )
    client4 = db.add_client(
        'ООО Логистика Плюс', '+74951234570', 'Москва, ул. Тверская, 15'
    )
    client5 = db.add_client(
        'ИП Кузнецов', '+74951234571', 'Новосибирск, ул. Красный проспект, 20'
    )
    print(f'  Добавлено 5 клиентов (ID: {client1.id}-{client5.id})')

    print('Добавление заказов...')
    order1 = db.add_order(
        client1.id,
        route1.id,
        'Электроника',
        500.0,
        date(2024, 1, 15),
        'выполнен',
    )
    order2 = db.add_order(
        client1.id, route2.id, 'Мебель', 2000.0, date(2024, 2, 10), 'в процессе'
    )
    order3 = db.add_order(
        client2.id, route1.id, 'Одежда', 300.0, date(2024, 1, 20), 'выполнен'
    )
    order4 = db.add_order(
        client2.id, route3.id, 'Продукты', 5000.0, date(2024, 3, 5), 'отменен'
    )
    order5 = db.add_order(
        client3.id,
        route4.id,
        'Стройматериалы',
        8000.0,
        date(2024, 2, 25),
        'выполнен',
    )
    print(f'  Добавлено 5 заказов (ID: {order1.id}-{order5.id})')

    print('Добавление рейсов...')
    trip1 = db.add_trip(
        order1.id,
        vehicle2.id,
        driver1.id,
        date(2024, 1, 15),
        date(2024, 1, 16),
        'завершен',
    )
    trip2 = db.add_trip(
        order2.id, vehicle3.id, driver2.id, date(2024, 2, 10), None, 'в пути'
    )
    trip3 = db.add_trip(
        order3.id,
        vehicle2.id,
        driver1.id,
        date(2024, 1, 20),
        date(2024, 1, 21),
        'завершен',
    )
    trip4 = db.add_trip(
        order5.id,
        vehicle3.id,
        driver2.id,
        date(2024, 2, 25),
        date(2024, 2, 26),
        'завершен',
    )
    trip5 = db.add_trip(
        order1.id,
        vehicle5.id,
        driver3.id,
        date(2024, 1, 18),
        date(2024, 1, 19),
        'завершен',
    )
    print(f'  Добавлено 5 рейсов (ID: {trip1.id}-{trip5.id})')

    print('\nБаза данных успешно создана и наполнена данными!')
    print('Файл: transport_company.db')
    print('\nСтатистика:')
    print(f'  Водителей: 5')
    print(f'  Транспортных средств: 5')
    print(f'  Маршрутов: 5')
    print(f'  Клиентов: 5')
    print(f'  Заказов: 5')
    print(f'  Рейсов: 5')


if __name__ == '__main__':
    init_database()
