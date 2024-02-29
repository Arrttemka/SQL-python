import psycopg2
import re
import getpass
from datetime import datetime, timedelta

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="cargo_transportation",
    user="postgres",
    password="09120912",
)

logged_in = False

def get_client_id_by_user_id(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT Id FROM Clients WHERE UserId = %s", (user_id,))
        client_id = cursor.fetchone()
        return client_id[0] if client_id else None

def is_valid_phone(phone):
    return re.match(r'\+375[0-9]{9}', phone) is not None

def is_valid_password(password):
    return len(re.findall(r'\d', password)) >= 4

def register_user(conn, first_name, last_name, phone, password, role_id, CargoWeight):
    global logged_in
    global current_user_id
    with conn.cursor() as cursor:
        try:
            if len(first_name) < 1:
                raise ValueError("Имя должно содержать не менее 1 символа.")
            if len(last_name) < 1:
                raise ValueError("Фамилия должна содержать не менее 1 символа.")
            if not is_valid_phone(phone):
                raise ValueError("Некорректный формат телефона. Пример: +375291111111")
            if not is_valid_password(password):
                raise ValueError("Пароль должен содержать не менее 4 цифр.")
            print(role_id)
            cursor.execute("""
                INSERT INTO Users (FirstName, LastName, Phone, Password, RolesId)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING Id
            """, (first_name, last_name, phone, password, role_id))
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.execute("""
                INSERT INTO Clients (CargoWeight, UserId)
                VALUES (%s, %s)
            """, (CargoWeight, user_id))
            
            conn.commit()
            
            print("Пользователь успешно зарегистрирован!")

            login_user(conn, first_name, password)
            logged_in = True 
            current_user_id = user_id  
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при регистрации пользователя: {e}")

def login_user(conn, first_name, password):
    global logged_in
    global current_user_id  
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM Users
            WHERE Firstname = %s AND Password = %s
        """, (first_name, password))
        user = cursor.fetchone()
        if user:
            print(f"Добро пожаловать, {user[1]} {user[2]}!")
            logged_in = True
            current_user_id = user[0]  
        else:
            print("Неверный логин или пароль.")

def logout_user():
    global logged_in
    global current_user_id  
    print("Вы успешно вышли из аккаунта.")
    logged_in = False
    current_user_id = None  

def delete_user(conn):
    global current_user_id  
    with conn.cursor() as cursor:
        try:
            if is_client(conn, current_user_id):
                delete_client(conn, current_user_id)
            elif is_dispatcher(conn, current_user_id):
                delete_dispatcher_by_user_id(conn, current_user_id)
            elif is_driver(conn, current_user_id):
                delete_driver_by_user_id(conn, current_user_id)
            cursor.execute("""
                DELETE FROM Logging
                WHERE UserId = %s
            """, (current_user_id,))
           
            cursor.execute("""
                DELETE FROM Users
                WHERE Id = %s
            """, (current_user_id,))


            if cursor.rowcount > 0:
                print(f"Аккаунт успешно удален.")
                conn.commit()
            else:
                print(f"Аккаунт не найден.")
                conn.rollback()
        except Exception as e:
            print(f"Ошибка при удалении пользователя: {e}")
            conn.rollback()

def view_drivers(conn):
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "SELECT U.ID, U.FirstName, U.LastName, D.Experience, C.Model, C.Manufacture_Year "
                "FROM Drivers D "
                "JOIN Users U ON D.UserID = U.ID "
                "JOIN Cars C ON D.CarID = C.ID"
            )
            drivers = cursor.fetchall()

            print("Информация о водителях:")
            for driver in drivers:
                print(f"ID водителя: {driver[0]}, Имя: {driver[1]} {driver[2]}, Опыт: {driver[3]} лет, "
                      f"Модель автомобиля: {driver[4]}, Год выпуска: {driver[5]}")

        except Exception as e:
            print(f"Ошибка при просмотре информации о водителях: {e}")

def create_order(conn):
    global current_user_id

    if not is_client(conn, current_user_id):
        print("Только клиенты могут совершать заказ.")
        return

    with conn.cursor() as cursor:
        try:
            cursor.execute("SELECT D.ID, U.FirstName, U.LastName, D.Experience FROM Drivers D JOIN Users U ON D.UserID = U.ID")
            drivers = cursor.fetchall()
            print("Список водителей:")
            for driver in drivers:
                print(f"ID водителя: {driver[0]}, Имя: {driver[1]} {driver[2]}, Опыт: {driver[3]} лет")


            # Получаем список диспетчеров с их именами
            cursor.execute("SELECT D.ID, U.FirstName, U.LastName, D.Salary FROM Dispatchers D JOIN Users U ON D.UserID = U.ID")
            dispatchers = cursor.fetchall()
            print("\nСписок диспетчеров:")
            for dispatcher in dispatchers:
                print(f"ID диспетчера: {dispatcher[0]}, Имя: {dispatcher[1]} {dispatcher[2]}, Зарплата: {dispatcher[3]}")


            cursor.execute("SELECT ID, PickupAddress, DeliveryAddress FROM Addresses")
            addresses = cursor.fetchall()
            print("\nСписок адресов:")
            for address in addresses:
                print(f"ID: {address[0]}, Забор: {address[1]}, Доставка: {address[2]}")

            order_number = input("\nВведите номер заказа: ")
            address_id = int(input("Выберите адрес (ID): "))
            client_id = get_client_id_by_user_id(conn, current_user_id)
            driver_id = int(input("Выберите водителя (ID): "))
            dispatcher_id = int(input("Выберите диспетчера (ID): "))

            current_datetime = datetime.now()
            delivery_datetime = current_datetime + timedelta(days=10)

            cursor.execute(
                "INSERT INTO Orders (OrderNumber, CreatedDate, DeliveryDate, OrderStatus, AddressID, ClientsID, DriverID, DispatcherID) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING ID",
                (order_number, current_datetime, delivery_datetime, "Processing", address_id, client_id, driver_id, dispatcher_id)
            )
            order_id = cursor.fetchone()[0]

            conn.commit()

            print(f"\nЗаказ создан успешно. ID заказа: {order_id}")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при создании заказа: {e}")

def view_order_history(conn):
    
    global current_user_id

    if not is_client(conn, current_user_id):
        print("Только клиент может посмотреть свою историю заказов.")
        return

    client_id = get_client_id_by_user_id(conn, current_user_id)

    with conn.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT O.ID, O.OrderNumber, O.CreatedDate, O.DeliveryDate, O.OrderStatus,
                       A.PickupAddress, A.DeliveryAddress,
                       D.Experience AS DriverExperience, DS.Salary AS DispatcherSalary
                FROM Orders O
                JOIN Addresses A ON O.AddressID = A.ID
                LEFT JOIN Drivers D ON O.DriverID = D.ID
                LEFT JOIN Dispatchers DS ON O.DispatcherID = DS.ID
                WHERE O.ClientsID = %s
                ORDER BY O.CreatedDate DESC
            """, (client_id,))
            orders = cursor.fetchall()
            if not orders:
                print(f"У Вас нет заказов .")
                return
            # Выводим историю заказов
            print(f"История заказов для клиента с ID {client_id}:")
            for order in orders:
                print(f"ID заказа: {order[0]}, Номер заказа: {order[1]}, "
                      f"Дата создания: {order[2]}, Дата доставки: {order[3]}, "
                      f"Статус: {order[4]}, Адрес забора: {order[5]}, "
                      f"Адрес доставки: {order[6]}, Водитель (опыт): {order[7]} лет, "
                      f"Диспетчер (зарплата): {order[8]}")

        except Exception as e:
            print(f"Ошибка при просмотре истории заказов: {e}")

def is_admin(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT RolesId FROM Users WHERE Id = %s", (user_id,))
        role_id = cursor.fetchone()
        return role_id and role_id[0] == 5 

def is_dispatcher(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT RolesId FROM Users WHERE Id = %s", (user_id,))
        role_id = cursor.fetchone()
        return role_id and role_id[0] == 6 

def is_client(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT RolesId FROM Users WHERE Id = %s", (user_id,))
        role_id = cursor.fetchone()
        return role_id and role_id[0] == 8

def is_driver(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT RolesId FROM Users WHERE Id = %s", (user_id,))
        role_id = cursor.fetchone()
        return role_id and role_id[0] == 7
    
def get_user_id_by_name(conn, user_name):
    with conn.cursor() as cursor:
        cursor.execute("SELECT Id FROM Users WHERE Firstname ILIKE %s", (user_name,))
        user_id = cursor.fetchone()
        return user_id[0] if user_id else None

def get_driver_id_by_user_id(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT Id FROM Drivers WHERE UserId = %s", (user_id,))
        driver_id = cursor.fetchone()
        return driver_id[0] if driver_id else None

def get_dispatcher_id_by_user_id(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT Id FROM Dispatchers WHERE UserId = %s", (user_id,))
        dispatcher_id = cursor.fetchone()
        return dispatcher_id[0] if dispatcher_id else None

def delete_client(conn, user_id):
    client_id = get_client_id_by_user_id(conn, user_id)
    with conn.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM Orders WHERE ClientsId = %s", (client_id,))
            conn.commit()
            cursor.execute("DELETE FROM Clients WHERE UserId = %s", (user_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при удалении пользователя из таблицы клиентов: {e}")

def add_driver(conn):
    global current_user_id

    if not is_admin(conn, current_user_id):
        print("У вас нет прав для добавления водителя.")
        return

    user_name = input("Введите имя пользователя, которого вы хотите назначить водителем: ")

    user_id = get_user_id_by_name(conn, user_name)

    if not user_id:
        print("Пользователь с указанным именем не существует.")
        return
    
    delete_client(conn, user_id)
    available_cars = get_available_cars(conn)
    print("Доступные машины:")
    for car in available_cars:
        print(f"ID: {car[0]}, Модель: {car[1]}, Год выпуска: {car[2]}")

    car_id = int(input("Выберите ID машины для водителя: "))

    experience = input("Введите опыт водителя: ")
   
    with conn.cursor() as cursor:
        try:
            cursor.execute("""
                INSERT INTO Drivers (Experience, CarId, UserId)
                VALUES (%s, %s, %s)
                RETURNING Id
            """, (experience, car_id, user_id))

            cursor.execute("""
                UPDATE Users
                SET RolesId = 7
                WHERE Id = %s
            """, (user_id,))

            conn.commit()
            print("Сотрудник успешно добавлен.")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при добавлении сотрудника: {e}")

def delete_driver_by_name(conn):
    global current_user_id

    if not is_admin(conn, current_user_id):
        print("У вас нет прав для добавления водителя.")
        return
    with conn.cursor() as cursor:
        try:
            user_name = input("Введите имя водителя, которого вы хотите удалить: ")
            user_id = get_user_id_by_name(conn, user_name)
            driver_id = get_driver_id_by_user_id(conn, user_id)

            if not driver_id:
                print(f"Водитель с именем {user_name} не найден.")
                return

            cursor.execute("DELETE FROM Drivers WHERE ID = %s", (driver_id,))

            cursor.execute("UPDATE Users SET RolesId = 8 WHERE ID = %s", (user_id,))

            conn.commit()
            print("Водитель успешно удален.")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при удалении водителя: {e}")

def get_available_cars(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT ID, Model, Manufacture_Year FROM Cars")
        return cursor.fetchall()

def add_dispatcher(conn):
    global current_user_id

    if not is_admin(conn, current_user_id):
        print("У вас нет прав для добавления диспетчера.")
        return
    
    user_name = input("Введите имя пользователя, которого вы хотите назначить диспетчером: ")

    user_id = get_user_id_by_name(conn, user_name)

    if not user_id:
        print("Пользователь с указанным именем не существует.")
        return
    
    delete_client(conn, user_id)
   
    salary = input("Введите зарплату диспетчера: ")
   
    with conn.cursor() as cursor:
        try:
            cursor.execute("""
                INSERT INTO Dispatchers (UserId, Salary)
                VALUES (%s, %s)
                RETURNING Id
            """, (user_id, salary))

            cursor.execute("""
                UPDATE Users
                SET RolesId = 6
                WHERE Id = %s
            """, (user_id,))

            conn.commit()
            print("Диспетчер успешно добавлен.")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при добавлении диспетчера: {e}")

def delete_dispatcher(conn):
    global current_user_id

    if not is_admin(conn, current_user_id):
        print("У вас нет прав для добавления диспетчера.")
        return
    with conn.cursor() as cursor:
        try:
            user_name = input("Введите имя диспетчера, которого вы хотите удалить: ")
            user_id = get_user_id_by_name(conn, user_name)
            dispatcher_id = get_dispatcher_id_by_user_id(conn, user_id)

            if not dispatcher_id:
                print(f"Диспетчер с именем {user_name} не найден.")
                return
            cursor.execute("DELETE FROM Orders WHERE DispatcherId = %s", (dispatcher_id,))

            cursor.execute("DELETE FROM Dispatchers WHERE ID = %s", (dispatcher_id,))

            cursor.execute("UPDATE Users SET RolesId = 8 WHERE ID = %s", (user_id,))

            conn.commit()
            print("Диспетчер успешно удален.")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при удалении диспетчера: {e}")

def delete_dispatcher_by_user_id(conn, user_id):
    dispatcher_id = get_dispatcher_id_by_user_id(conn, user_id)
    with conn.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM Orders WHERE DispatcherID = %s", (dispatcher_id,))
            conn.commit()
            cursor.execute("DELETE FROM Dispatchers WHERE UserId = %s", (user_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при удалении пользователя из таблицы диспетчеров: {e}")

def delete_driver_by_user_id(conn, user_id):
    driver_id = get_driver_id_by_user_id(conn, user_id)
    with conn.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM Orders WHERE DriverID = %s", (driver_id,))
            conn.commit()
            cursor.execute("DELETE FROM Drivers WHERE UserId = %s", (user_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при удалении пользователя из таблицы водителей: {e}")

def view_order_history_for_client(conn):
    
    global current_user_id
    if not is_dispatcher(conn, current_user_id) and not is_admin(conn, current_user_id):
        print("У вас нет прав для просмотра истории заказов.")
        return
    user_name = input("Введите имя пользователя, чью историю заказов вы хотите посмотреть: ")

    user_id = get_user_id_by_name(conn, user_name)

    if not user_id:
        print("Пользователь с указанным именем не существует.")
        return
    client_id = get_client_id_by_user_id(conn, user_id)

    with conn.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT O.ID, O.OrderNumber, O.CreatedDate, O.DeliveryDate, O.OrderStatus,
                       A.PickupAddress, A.DeliveryAddress,
                       D.Experience AS DriverExperience, DS.Salary AS DispatcherSalary
                FROM Orders O
                JOIN Addresses A ON O.AddressID = A.ID
                LEFT JOIN Drivers D ON O.DriverID = D.ID
                LEFT JOIN Dispatchers DS ON O.DispatcherID = DS.ID
                WHERE O.ClientsID = %s
                ORDER BY O.CreatedDate DESC
            """, (client_id,))
            orders = cursor.fetchall()
            if not orders:
                print(f"У {user_name} нет заказов .")
                return
            print(f"История заказов для клиента с ID {client_id}:")
            for order in orders:
                print(f"ID заказа: {order[0]}, Номер заказа: {order[1]}, "
                      f"Дата создания: {order[2]}, Дата доставки: {order[3]}, "
                      f"Статус: {order[4]}, Адрес забора: {order[5]}, "
                      f"Адрес доставки: {order[6]}, Водитель (опыт): {order[7]} лет, "
                      f"Диспетчер (зарплата): {order[8]}")

        except Exception as e:
            print(f"Ошибка при просмотре истории заказов: {e}")

def get_car_types(conn):
    with conn.cursor() as cursor:
        try:
            cursor.execute("SELECT ID, Type FROM CarTypes")
            car_types = cursor.fetchall()
            return car_types
        except Exception as e:
            print(f"Ошибка при получении списка типов машин: {e}")
            return None

def add_car(conn):

    if not is_driver(conn, current_user_id) and not is_admin(conn, current_user_id):
        print("У вас нет прав для добавления машины.")
        return

    car_types = get_car_types(conn)

    if not car_types:
        return

    model = input("Введите модель машины: ")
    manufacture_year = input("Введите год выпуска машины (в формате YYYY-MM-DD): ")

    print("\nВыберите тип машины (укажите ID из списка):")
    for car_type in car_types:
        print(f"{car_type[0]}. {car_type[1]}")

    car_type_id = int(input("Введите ID типа машины: "))

    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO Cars (Model, Manufacture_Year, CarTypeID) VALUES (%s, %s, %s) RETURNING ID",
                (model, manufacture_year, car_type_id)
            )
            car_id = cursor.fetchone()[0]
            conn.commit()
            print(f"Машина успешно добавлена. ID машины: {car_id}")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при добавлении машины: {e}")

def log_action(conn, action_message):
    global current_user_id
    user_id = current_user_id

    with conn.cursor() as cursor:
        try:
            cursor.execute("INSERT INTO Logging (message, UserID) VALUES (%s, %s) RETURNING log_time", (action_message, user_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при записи лога: {e}")

def view_user_log(conn):

    if not is_admin(conn, current_user_id):
        print("У вас нет прав для добавления водителя.")
        return
    
    user_name = input("Введите имя пользователя, чей лог хотите посмотреть: ")

    user_id = get_user_id_by_name(conn, user_name)
    with conn.cursor() as cursor:
        try:
            cursor.execute("SELECT ID, message, log_time FROM Logging WHERE UserID = %s ORDER BY log_time DESC", (user_id,))
            logs = cursor.fetchall()

            print(f"Лог для пользователя с ID {user_id}:")
            for log in logs:
                print(f"ID записи: {log[0]}, Сообщение: {log[1]}, Время: {log[2]}")

        except Exception as e:
            print(f"Ошибка при просмотре лога: {e}")

def main():
    global logged_in
    while True:
        if not logged_in:
            print("\nВыберите действие:")
            print("1. Зарегистрироваться")
            print("2. Войти")
            print("3. Посмотреть доступных водителей и их машины")
            print("0. Выход из приложения")
        else:
            print("\nВыберите действие:")
            print("1. Выход из аккаунта")
            print("2. Удалить аккаунт")
            print("3. Посмотреть доступных водителей и их машины")
            print("4. Совершить заказ")
            print("5. Посмотреть историю заказов")
            print("6. Посмотреть историю заказов для клиента")
            print("7. Добавить машину")
            print("8. Добавить водителя")
            print("9. Удалить водителя")
            print("10. Добавить диспетчера")
            print("11. Удалить диспетчера")            
            print("12. Посмотреть лог пользователя")
            print("0. Выход из приложения")

        choice = input("\nВыберете операцию: ")

        if not logged_in:
            if choice == "1":
                first_name = input("Введите ваше имя: ")
                last_name = input("Введите вашу фамилию: ")
                phone = input("Введите ваш номер телефона: ")
                CargoWeight = input("Введите вес груза: ")
                password = getpass.getpass("Введите ваш пароль: ")
                role_id = 8
                register_user(conn, first_name, last_name, phone, password, role_id, CargoWeight)
            elif choice == "2":
                phone = input("Введите логин: ")
                password = getpass.getpass("Введите пароль: ")
                login_user(conn, phone, password)

            elif choice == "3":
                view_drivers(conn)
            elif choice == "0":
                break
            
        elif logged_in:
            if choice == "1":
                logout_user()
            elif choice == "2":
                delete_user(conn)
                logout_user()
            elif choice == "3":
                view_drivers(conn)
                log_action(conn, "Пользователь посмотрел доступных водителей")
            elif choice == "4":
                create_order(conn)
                log_action(conn, "Пользователь совершил заказ")
            elif choice == "5":
                view_order_history(conn)    
                log_action(conn, "Пользователь посмотрел свою историю заказов")
            elif choice == "6":
                view_order_history_for_client(conn)  
                log_action(conn, "Пользователь посмотрел историю заказов клиента")
            elif choice == "7":
                add_car(conn)
                log_action(conn, "Пользователь добавил новую машину")
            elif choice == "8":
                add_driver(conn)  
                log_action(conn, "Пользователь добавил нового водителя")
            elif choice == "9":
                delete_driver_by_name(conn)  
                log_action(conn, "Пользователь удалил водителя")
            elif choice == "10":
                add_dispatcher(conn)
                log_action(conn, "Пользователь добавил нового диспетчера")
            elif choice == "11":
                delete_dispatcher(conn) 
                log_action(conn, "Пользователь удалил диспетчера")
            elif choice == "12":
                view_user_log(conn) 
                log_action(conn, "Пользователь посмотрел лог пользователя")
            elif choice == "0":
                break
            
if __name__ == "__main__":
    try:
        main()
    finally:
        conn.close()
