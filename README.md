# SQL-python
Создание консольного приложения с поддержкой работы с базой данный SQL
# 1. Инфо:
Талай Артем, 153505
Тема приложения: Сайт для работы фирмы грузоперевозок
СУБД: Postgre SQL

# 2. Функциональные требования:
  1. Авторизация пользователя.
  2. Управление пользователями (CRUD-регистрация, удаление, вход).
  3. Ролевая система(Клиент, Водитель, Диспетчер, Админ).
  4. Ведение журнала действий пользователя.(Логирование)
  5. Управление заказами(Просмотр заказов-Диспетчер, Админ).
  6. Управление водителями и диспетчерами CRUD (Админ).

# 3. Use-case:
Неавторизованный пользователь:

  Просматривать список водителей и их машины
  Авторизовываться 
  
Авторизованный пользователь(Клиент):
  Просматривать историю своих заказов
  Все, что и неавторизованный пользователь
  Совершать заказ
  
Диспетчер:
  Просматривать историю заказов пользователей
  Просматривать лог клиентов
  
Водитель:
  Может создавать машину

Админ:
  Все, что и все + CRUD водителей и диспетчеров
     
# 4. Список таблиц для базы данных:
  1. "Машины":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Модель (VARCHAR(64), NN)
        Год выпуска (DATETIME, NN)
        ID типа кузова(FOREIGN KEY REFERENCES тип кузова(ID), NN)
    Связи:  
       Связь с таблицей "Тип кузова" в отношении "Многие к одному" (Many-to-One) через поле ID тип кузова.

  2. "Заказы":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Номер заказа (DECIMAL, NN)
        Дата создания (DATETIME, NN)
        Дата доставки (DATETIME, NN)
        Статус заказа (VARCHAR(32), NN)
        ID адреса (INT, FOREIGN KEY REFERENCES Адресы(ID), NN)
        ID клиента (INT, FOREIGN KEY REFERENCES Клиенты(ID), NN)
        ID водителя (INT, FOREIGN KEY REFERENCES Водители(ID), NN)
        ID диспетчера (INT, FOREIGN KEY REFERENCES Диспетчеры(ID), NN)      
    Связи:
       Связь с таблицей "Адресы" в отношении "Многие к одному" (Many-to-One) через поле ID адреса.
       Связь с таблицей "Клиенты" в отношении "Многие к одному" (Many-to-One) через поле ID клиента.
       Связь с таблицей "Водители" в отношении "Многие к одному" (Many-to-One) через поле ID водители.
       Связь с таблицей "Диспетчеры" в отношении "Многие к одному" (Many-to-One) через поле ID диспетчеры.


  3. "Клиенты":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN) 
        Вес груза (INT, NN)
        ID пользователя (INT, UNIQUE, NN)
   Связи:
       Связь с таблицей "Пользователи" в отношении "Один к одному" (One-to-One) через поле ID клиента.

  4. "Роли":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Название роли (VARCHAR(25), UNIQUE, NN)

  5. "Диспетчер":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Имя (VARCHAR(32), NN)
        Фамилия (VARCHAR(32), NN)
        ID пользователя (INT, UNIQUE KEY REFERENCES пользователи(ID), NN)
    Связи:
        Связь с таблицей "Пользователи" в отношении "Один к одному" (One-to-One) через поле ID пользователя.
        Связь с таблицей "Заказы" в отношении "Один к многим" (One-to-Many) через поле ID заказы.

  6. "Водители":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Имя (VARCHAR(32), NN)
        Фамилия (VARCHAR(32), NN)
        Стаж водителя(INT)
        ID машины (INT, UNIQUE, NN)
        ID пользователя (INT, UNIQUE, NN)
    Связи:
        Связь с таблицей "Пользователи" в отношении "Один к одному" (One-to-One) через поле ID клиента.
       Связь с таблицей "Машины" в отношении "Один к одному" (One-to-One) через поле ID клиента.
       
  7. "Тип машины":
    
    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Тип (VARCHAR(64), NN)
      Связи:
        Связь с таблицей "Машины" в отношении "Один к многим" (One-to-Many) через поле ID типа машины.
        
  8. "Адреса":
      
    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Адрес, с которого необходимо забрать груз (VARCHAR(64), NN)
        Адрес доставки (VARCHAR(64), NN)
    Связи:
        Связь с таблицей "Заказы" в отношении "Один к многим" (One-to-Many) через поле ID адреса.
      
  9. "Пользователи":

    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Имя (VARCHAR(50), NN)
        Фамилия (VARCHAR(50), NN)
        Телефон (CHAR(13) ~ '+375[0-9]{9}' NN,)
        Пароль (VARCHAR(50), NN)
        ID Роли (INT, FOREIGN KEY REFERENCES Роли(ID))
    Связи:
        Связь с таблицей "Роли" в отношении "Многие к одному" (Many-to-One) через поле ID Роли.

  10. "Тип услуги":
    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        Тип(VARCHAR(50), NN)
    Связи:
        Связь c тип услуги(One to many) через поля ID услуги
  12. "Тип услуги/Заказ"(вспомогательная):
    Поля:
        ID (INT, PRIMARY KEY, AUTOINCREMENT, NN)
        ID услуги(INT, FOREIGN KEY REFERENCES(услуга), NN)
        ID заказа(INT, FOREIGN KEY REFERENCES(заказа), NN)
    Связи:
        Связь между услуги/заказа(Many to many) через поля ID услуги и ID заказа
      
        


    
# 5. Диаграмма: 
https://github.com/Arrttemka/DB_labs/blob/master/photo_1_2023-10-04_11-21-51.jpg

https://github.com/Arrttemka/DB_labs/blob/master/photo_2_2023-10-04_11-21-51.jpg
