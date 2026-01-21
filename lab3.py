import os
import tempfile
import unittest
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import Session, declarative_base, joinedload, relationship, sessionmaker

Base = declarative_base()


class Driver(Base):
    __tablename__ = 'drivers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    experience_years = Column(Integer, nullable=False)

    vehicles = relationship('Vehicle', back_populates='driver')
    trips = relationship('Trip', back_populates='driver')


class Vehicle(Base):
    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)
    license_plate = Column(String(20), unique=True, nullable=False)
    capacity_kg = Column(Float, nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=True)

    driver = relationship('Driver', back_populates='vehicles')
    trips = relationship('Trip', back_populates='vehicle')


class Route(Base):
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)

    orders = relationship('Order', back_populates='route')


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(200), nullable=False)

    orders = relationship('Order', back_populates='client')


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=False)
    cargo_description = Column(String(200), nullable=False)
    weight_kg = Column(Float, nullable=False)
    order_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)

    client = relationship('Client', back_populates='orders')
    route = relationship('Route', back_populates='orders')
    trips = relationship('Trip', back_populates='order')


class Trip(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False)

    order = relationship('Order', back_populates='trips')
    vehicle = relationship('Vehicle', back_populates='trips')
    driver = relationship('Driver', back_populates='trips')


class TransportCompanyDB:
    def __init__(self, db_path: str = 'transport_company.db'):
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.Session()

    def query_drivers_by_experience(self, min_experience: int) -> List[Driver]:
        with self.get_session() as session:
            return session.query(Driver).filter(Driver.experience_years >= min_experience).all()

    def query_vehicles_by_capacity(self, min_capacity: float) -> List[Vehicle]:
        with self.get_session() as session:
            return session.query(Vehicle).filter(Vehicle.capacity_kg >= min_capacity).all()

    def query_orders_by_client_name(self, client_name: str) -> List[Order]:
        with self.get_session() as session:
            return (
                session.query(Order)
                .join(Client)
                .filter(Client.name == client_name)
                .options(joinedload(Order.client))
                .all()
            )

    def query_trips_by_status(self, status: str) -> List[Trip]:
        with self.get_session() as session:
            return session.query(Trip).filter(Trip.status == status).all()

    def query_average_vehicle_capacity(self) -> float:
        with self.get_session() as session:
            result = session.query(func.avg(Vehicle.capacity_kg)).scalar()
            return float(result) if result else 0.0

    def query_order_count_by_client(self) -> List[tuple]:
        with self.get_session() as session:
            return (
                session.query(Client.name, func.count(Order.id).label('order_count'))
                .join(Order)
                .group_by(Client.id, Client.name)
                .all()
            )

    def query_routes_by_distance(self, min_distance: float) -> List[Route]:
        with self.get_session() as session:
            return session.query(Route).filter(Route.distance_km >= min_distance).all()

    def query_drivers_without_vehicles(self) -> List[Driver]:
        with self.get_session() as session:
            return (
                session.query(Driver)
                .outerjoin(Vehicle)
                .filter(Vehicle.id.is_(None))
                .all()
            )

    def query_orders_by_date_range(self, start_date: date, end_date: date) -> List[Order]:
        with self.get_session() as session:
            return (
                session.query(Order)
                .filter(Order.order_date >= start_date, Order.order_date <= end_date)
                .all()
            )

    def query_top_routes_by_distance(self, limit: int = 5) -> List[Route]:
        with self.get_session() as session:
            return (
                session.query(Route)
                .order_by(Route.distance_km.desc())
                .limit(limit)
                .all()
            )

    def query_trips_by_driver_id(self, driver_id: int) -> List[Trip]:
        with self.get_session() as session:
            return session.query(Trip).filter(Trip.driver_id == driver_id).all()

    def query_clients_with_many_orders(self, min_orders: int) -> List[tuple]:
        with self.get_session() as session:
            return (
                session.query(Client.name, func.count(Order.id).label('order_count'))
                .join(Order)
                .group_by(Client.id, Client.name)
                .having(func.count(Order.id) >= min_orders)
                .all()
            )

    def query_vehicles_with_drivers(self) -> List[Vehicle]:
        with self.get_session() as session:
            return (
                session.query(Vehicle)
                .filter(Vehicle.driver_id.isnot(None))
                .options(joinedload(Vehicle.driver))
                .all()
            )

    def query_orders_by_status(self, status: str) -> List[Order]:
        with self.get_session() as session:
            return session.query(Order).filter(Order.status == status).all()

    def add_driver(
        self, name: str, license_number: str, phone: str, experience_years: int
    ) -> Driver:
        with self.get_session() as session:
            driver = Driver(
                name=name,
                license_number=license_number,
                phone=phone,
                experience_years=experience_years,
            )
            session.add(driver)
            session.commit()
            session.refresh(driver)
            return driver

    def add_vehicle(
        self, model: str, license_plate: str, capacity_kg: float, driver_id: Optional[int] = None
    ) -> Vehicle:
        with self.get_session() as session:
            vehicle = Vehicle(
                model=model,
                license_plate=license_plate,
                capacity_kg=capacity_kg,
                driver_id=driver_id,
            )
            session.add(vehicle)
            session.commit()
            session.refresh(vehicle)
            return vehicle

    def add_route(
        self, origin: str, destination: str, distance_km: float, duration_hours: float
    ) -> Route:
        with self.get_session() as session:
            route = Route(
                origin=origin,
                destination=destination,
                distance_km=distance_km,
                duration_hours=duration_hours,
            )
            session.add(route)
            session.commit()
            session.refresh(route)
            return route

    def add_client(self, name: str, phone: str, address: str) -> Client:
        with self.get_session() as session:
            client = Client(name=name, phone=phone, address=address)
            session.add(client)
            session.commit()
            session.refresh(client)
            return client

    def add_order(
        self,
        client_id: int,
        route_id: int,
        cargo_description: str,
        weight_kg: float,
        order_date: date,
        status: str,
    ) -> Order:
        with self.get_session() as session:
            order = Order(
                client_id=client_id,
                route_id=route_id,
                cargo_description=cargo_description,
                weight_kg=weight_kg,
                order_date=order_date,
                status=status,
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return order

    def add_trip(
        self,
        order_id: int,
        vehicle_id: int,
        driver_id: int,
        start_date: date,
        end_date: Optional[date],
        status: str,
    ) -> Trip:
        with self.get_session() as session:
            trip = Trip(
                order_id=order_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                start_date=start_date,
                end_date=end_date,
                status=status,
            )
            session.add(trip)
            session.commit()
            session.refresh(trip)
            return trip


class TestTransportCompanyDB(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = TransportCompanyDB(self.temp_db.name)
        self._populate_test_data()

    def tearDown(self) -> None:
        self.db.engine.dispose()
        try:
            os.unlink(self.temp_db.name)
        except (OSError, PermissionError):
            pass

    def _populate_test_data(self) -> None:
        with self.db.get_session() as session:
            driver1 = Driver(
                name='Иван Петров',
                license_number='DL001',
                phone='+79001234567',
                experience_years=10,
            )
            driver2 = Driver(
                name='Сергей Сидоров',
                license_number='DL002',
                phone='+79001234568',
                experience_years=5,
            )
            driver3 = Driver(
                name='Алексей Иванов',
                license_number='DL003',
                phone='+79001234569',
                experience_years=15,
            )
            driver4 = Driver(
                name='Дмитрий Козлов',
                license_number='DL004',
                phone='+79001234570',
                experience_years=3,
            )

            vehicle1 = Vehicle(
                model='Газель',
                license_plate='А123БВ',
                capacity_kg=1500.0,
                driver_id=None,
            )
            vehicle2 = Vehicle(
                model='МАЗ',
                license_plate='В456ГД',
                capacity_kg=10000.0,
                driver_id=1,
            )
            vehicle3 = Vehicle(
                model='Камаз',
                license_plate='Е789ЖЗ',
                capacity_kg=20000.0,
                driver_id=2,
            )
            vehicle4 = Vehicle(
                model='Фургон',
                license_plate='И012КЛ',
                capacity_kg=800.0,
                driver_id=None,
            )

            route1 = Route(
                origin='Москва',
                destination='Санкт-Петербург',
                distance_km=700.0,
                duration_hours=10.0,
            )
            route2 = Route(
                origin='Москва',
                destination='Казань',
                distance_km=800.0,
                duration_hours=12.0,
            )
            route3 = Route(
                origin='Санкт-Петербург',
                destination='Новосибирск',
                distance_km=3500.0,
                duration_hours=48.0,
            )
            route4 = Route(
                origin='Москва',
                destination='Воронеж',
                distance_km=500.0,
                duration_hours=7.0,
            )

            client1 = Client(
                name='ООО Торговый дом',
                phone='+74951234567',
                address='Москва, ул. Ленина, 1',
            )
            client2 = Client(
                name='ИП Смирнов',
                phone='+74951234568',
                address='Санкт-Петербург, пр. Невский, 10',
            )
            client3 = Client(
                name='ЗАО Промышленность',
                phone='+74951234569',
                address='Казань, ул. Баумана, 5',
            )

            order1 = Order(
                client_id=1,
                route_id=1,
                cargo_description='Электроника',
                weight_kg=500.0,
                order_date=date(2024, 1, 15),
                status='выполнен',
            )
            order2 = Order(
                client_id=1,
                route_id=2,
                cargo_description='Мебель',
                weight_kg=2000.0,
                order_date=date(2024, 2, 10),
                status='в процессе',
            )
            order3 = Order(
                client_id=2,
                route_id=1,
                cargo_description='Одежда',
                weight_kg=300.0,
                order_date=date(2024, 1, 20),
                status='выполнен',
            )
            order4 = Order(
                client_id=2,
                route_id=3,
                cargo_description='Продукты',
                weight_kg=5000.0,
                order_date=date(2024, 3, 5),
                status='отменен',
            )
            order5 = Order(
                client_id=3,
                route_id=4,
                cargo_description='Стройматериалы',
                weight_kg=8000.0,
                order_date=date(2024, 2, 25),
                status='выполнен',
            )
            order6 = Order(
                client_id=1,
                route_id=1,
                cargo_description='Бытовая техника',
                weight_kg=1200.0,
                order_date=date(2024, 3, 10),
                status='в процессе',
            )

            trip1 = Trip(
                order_id=1,
                vehicle_id=2,
                driver_id=1,
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 16),
                status='завершен',
            )
            trip2 = Trip(
                order_id=2,
                vehicle_id=3,
                driver_id=2,
                start_date=date(2024, 2, 10),
                end_date=None,
                status='в пути',
            )
            trip3 = Trip(
                order_id=3,
                vehicle_id=2,
                driver_id=1,
                start_date=date(2024, 1, 20),
                end_date=date(2024, 1, 21),
                status='завершен',
            )
            trip4 = Trip(
                order_id=5,
                vehicle_id=3,
                driver_id=2,
                start_date=date(2024, 2, 25),
                end_date=date(2024, 2, 26),
                status='завершен',
            )
            trip5 = Trip(
                order_id=6,
                vehicle_id=2,
                driver_id=1,
                start_date=date(2024, 3, 10),
                end_date=None,
                status='в пути',
            )

            session.add_all(
                [
                    driver1,
                    driver2,
                    driver3,
                    driver4,
                    vehicle1,
                    vehicle2,
                    vehicle3,
                    vehicle4,
                    route1,
                    route2,
                    route3,
                    route4,
                    client1,
                    client2,
                    client3,
                    order1,
                    order2,
                    order3,
                    order4,
                    order5,
                    order6,
                    trip1,
                    trip2,
                    trip3,
                    trip4,
                    trip5,
                ]
            )
            session.commit()

    def test_query_drivers_by_experience_min_10(self) -> None:
        drivers = self.db.query_drivers_by_experience(10)
        self.assertEqual(len(drivers), 2)
        self.assertTrue(all(d.experience_years >= 10 for d in drivers))

    def test_query_drivers_by_experience_min_5(self) -> None:
        drivers = self.db.query_drivers_by_experience(5)
        self.assertEqual(len(drivers), 3)
        self.assertTrue(all(d.experience_years >= 5 for d in drivers))

    def test_query_vehicles_by_capacity_min_10000(self) -> None:
        vehicles = self.db.query_vehicles_by_capacity(10000.0)
        self.assertEqual(len(vehicles), 2)
        self.assertTrue(all(v.capacity_kg >= 10000.0 for v in vehicles))

    def test_query_vehicles_by_capacity_min_5000(self) -> None:
        vehicles = self.db.query_vehicles_by_capacity(5000.0)
        self.assertEqual(len(vehicles), 2)
        self.assertTrue(all(v.capacity_kg >= 5000.0 for v in vehicles))

    def test_query_orders_by_client_name_existing(self) -> None:
        orders = self.db.query_orders_by_client_name('ООО Торговый дом')
        self.assertEqual(len(orders), 3)
        self.assertTrue(all(o.client.name == 'ООО Торговый дом' for o in orders))

    def test_query_orders_by_client_name_nonexistent(self) -> None:
        orders = self.db.query_orders_by_client_name('Несуществующий клиент')
        self.assertEqual(len(orders), 0)

    def test_query_trips_by_status_completed(self) -> None:
        trips = self.db.query_trips_by_status('завершен')
        self.assertEqual(len(trips), 3)
        self.assertTrue(all(t.status == 'завершен' for t in trips))

    def test_query_trips_by_status_in_progress(self) -> None:
        trips = self.db.query_trips_by_status('в пути')
        self.assertEqual(len(trips), 2)
        self.assertTrue(all(t.status == 'в пути' for t in trips))

    def test_query_average_vehicle_capacity_calculation(self) -> None:
        avg_capacity = self.db.query_average_vehicle_capacity()
        expected = (1500.0 + 10000.0 + 20000.0 + 800.0) / 4.0
        self.assertAlmostEqual(avg_capacity, expected, places=2)

    def test_query_average_vehicle_capacity_not_empty(self) -> None:
        avg_capacity = self.db.query_average_vehicle_capacity()
        self.assertGreater(avg_capacity, 0.0)

    def test_query_order_count_by_client_all_clients(self) -> None:
        results = self.db.query_order_count_by_client()
        self.assertEqual(len(results), 3)
        order_counts = {name: count for name, count in results}
        self.assertEqual(order_counts['ООО Торговый дом'], 3)
        self.assertEqual(order_counts['ИП Смирнов'], 2)
        self.assertEqual(order_counts['ЗАО Промышленность'], 1)

    def test_query_order_count_by_client_structure(self) -> None:
        results = self.db.query_order_count_by_client()
        self.assertTrue(all(len(r) == 2 for r in results))
        self.assertTrue(all(isinstance(r[0], str) and isinstance(r[1], int) for r in results))

    def test_query_routes_by_distance_min_700(self) -> None:
        routes = self.db.query_routes_by_distance(700.0)
        self.assertEqual(len(routes), 3)
        self.assertTrue(all(r.distance_km >= 700.0 for r in routes))

    def test_query_routes_by_distance_min_1000(self) -> None:
        routes = self.db.query_routes_by_distance(1000.0)
        self.assertEqual(len(routes), 1)
        self.assertTrue(all(r.distance_km >= 1000.0 for r in routes))

    def test_query_drivers_without_vehicles_count(self) -> None:
        drivers = self.db.query_drivers_without_vehicles()
        self.assertEqual(len(drivers), 2)
        driver_names = {d.name for d in drivers}
        self.assertIn('Алексей Иванов', driver_names)
        self.assertIn('Дмитрий Козлов', driver_names)

    def test_query_drivers_without_vehicles_no_vehicles(self) -> None:
        drivers = self.db.query_drivers_without_vehicles()
        with self.db.get_session() as session:
            for driver in drivers:
                vehicles = session.query(Vehicle).filter(Vehicle.driver_id == driver.id).all()
                self.assertEqual(len(vehicles), 0)

    def test_query_orders_by_date_range_january(self) -> None:
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        orders = self.db.query_orders_by_date_range(start, end)
        self.assertEqual(len(orders), 2)
        self.assertTrue(all(start <= o.order_date <= end for o in orders))

    def test_query_orders_by_date_range_february(self) -> None:
        start = date(2024, 2, 1)
        end = date(2024, 2, 29)
        orders = self.db.query_orders_by_date_range(start, end)
        self.assertEqual(len(orders), 2)
        self.assertTrue(all(start <= o.order_date <= end for o in orders))

    def test_query_top_routes_by_distance_limit_3(self) -> None:
        routes = self.db.query_top_routes_by_distance(3)
        self.assertEqual(len(routes), 3)
        distances = [r.distance_km for r in routes]
        self.assertEqual(distances, sorted(distances, reverse=True))

    def test_query_top_routes_by_distance_longest_first(self) -> None:
        routes = self.db.query_top_routes_by_distance(5)
        self.assertGreater(len(routes), 0)
        if len(routes) > 1:
            self.assertGreaterEqual(routes[0].distance_km, routes[1].distance_km)

    def test_query_trips_by_driver_id_existing(self) -> None:
        trips = self.db.query_trips_by_driver_id(1)
        self.assertEqual(len(trips), 3)
        self.assertTrue(all(t.driver_id == 1 for t in trips))

    def test_query_trips_by_driver_id_nonexistent(self) -> None:
        trips = self.db.query_trips_by_driver_id(999)
        self.assertEqual(len(trips), 0)

    def test_query_clients_with_many_orders_min_2(self) -> None:
        results = self.db.query_clients_with_many_orders(2)
        self.assertEqual(len(results), 2)
        client_names = {name for name, _ in results}
        self.assertIn('ООО Торговый дом', client_names)
        self.assertIn('ИП Смирнов', client_names)

    def test_query_clients_with_many_orders_min_3(self) -> None:
        results = self.db.query_clients_with_many_orders(3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 'ООО Торговый дом')
        self.assertEqual(results[0][1], 3)

    def test_query_vehicles_with_drivers_count(self) -> None:
        vehicles = self.db.query_vehicles_with_drivers()
        self.assertEqual(len(vehicles), 2)
        self.assertTrue(all(v.driver_id is not None for v in vehicles))

    def test_query_vehicles_with_drivers_has_drivers(self) -> None:
        vehicles = self.db.query_vehicles_with_drivers()
        for vehicle in vehicles:
            self.assertIsNotNone(vehicle.driver)

    def test_query_orders_by_status_completed(self) -> None:
        orders = self.db.query_orders_by_status('выполнен')
        self.assertEqual(len(orders), 3)
        self.assertTrue(all(o.status == 'выполнен' for o in orders))

    def test_query_orders_by_status_in_process(self) -> None:
        orders = self.db.query_orders_by_status('в процессе')
        self.assertEqual(len(orders), 2)
        self.assertTrue(all(o.status == 'в процессе' for o in orders))


def main() -> None:
    db = TransportCompanyDB('transport_company.db')
    print('=' * 60)
    print('Демонстрация запросов к базе данных')
    print('=' * 60)

    print('\n1. Водители с опытом >= 10 лет:')
    drivers = db.query_drivers_by_experience(10)
    for driver in drivers:
        print(f'   - {driver.name}, опыт: {driver.experience_years} лет')

    print('\n2. Транспорт с грузоподъемностью >= 10000 кг:')
    vehicles = db.query_vehicles_by_capacity(10000.0)
    for vehicle in vehicles:
        print(
            f'   - {vehicle.model} ({vehicle.license_plate}), '
            f'грузоподъемность: {vehicle.capacity_kg} кг'
        )

    print('\n3. Заказы клиента "ООО Торговый дом":')
    orders = db.query_orders_by_client_name('ООО Торговый дом')
    for order in orders:
        print(
            f'   - Заказ #{order.id}: {order.cargo_description}, '
            f'вес: {order.weight_kg} кг, статус: {order.status}'
        )

    print('\n4. Рейсы со статусом "завершен":')
    trips = db.query_trips_by_status('завершен')
    for trip in trips:
        print(f'   - Рейс #{trip.id}, заказ #{trip.order_id}, статус: {trip.status}')

    print('\n5. Средняя грузоподъемность транспорта:')
    avg_capacity = db.query_average_vehicle_capacity()
    print(f'   Средняя грузоподъемность: {avg_capacity:.2f} кг')

    print('\n6. Количество заказов по клиентам:')
    order_counts = db.query_order_count_by_client()
    for client_name, count in order_counts:
        print(f'   - {client_name}: {count} заказ(ов)')

    print('\n7. Маршруты длиннее 1000 км:')
    routes = db.query_routes_by_distance(1000.0)
    for route in routes:
        print(
            f'   - {route.origin} -> {route.destination}, '
            f'расстояние: {route.distance_km} км'
        )

    print('\n8. Водители без назначенного транспорта:')
    drivers_without_vehicles = db.query_drivers_without_vehicles()
    for driver in drivers_without_vehicles:
        print(f'   - {driver.name}')

    print('\n9. Заказы за январь 2024:')
    jan_orders = db.query_orders_by_date_range(date(2024, 1, 1), date(2024, 1, 31))
    for order in jan_orders:
        print(
            f'   - Заказ #{order.id}: {order.cargo_description}, '
            f'дата: {order.order_date}'
        )

    print('\n10. Топ-3 самых длинных маршрута:')
    top_routes = db.query_top_routes_by_distance(3)
    for route in top_routes:
        print(
            f'   - {route.origin} -> {route.destination}, '
            f'расстояние: {route.distance_km} км'
        )

    print('\n11. Рейсы водителя с ID=1:')
    driver_trips = db.query_trips_by_driver_id(1)
    for trip in driver_trips:
        print(f'   - Рейс #{trip.id}, заказ #{trip.order_id}, статус: {trip.status}')

    print('\n12. Клиенты с количеством заказов >= 1:')
    clients = db.query_clients_with_many_orders(1)
    for client_name, order_count in clients:
        print(f'   - {client_name}: {order_count} заказ(ов)')

    print('\n13. Транспорт с назначенными водителями:')
    vehicles_with_drivers = db.query_vehicles_with_drivers()
    for vehicle in vehicles_with_drivers:
        print(
            f'   - {vehicle.model} ({vehicle.license_plate}), '
            f'водитель: {vehicle.driver.name}'
        )

    print('\n14. Заказы со статусом "выполнен":')
    completed_orders = db.query_orders_by_status('выполнен')
    for order in completed_orders:
        print(
            f'   - Заказ #{order.id}: {order.cargo_description}, '
            f'дата: {order.order_date}'
        )

    print('\n' + '=' * 60)
    print('Демонстрация завершена!')
    print('=' * 60)


if __name__ == '__main__':
    main()
