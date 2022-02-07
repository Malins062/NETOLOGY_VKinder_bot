import hues  # для цветного вывода сообщений, + время
from vkbot import FILE_SETTINGS  # имя файла параметров

import datetime  # для работы с датой и временем

# Для работы с ORM БД PostgreSQL
from peewee import PostgresqlDatabase, Model
from peewee import SmallIntegerField, DateTimeField, CharField, TextField, ForeignKeyField, BooleanField
from playhouse.postgres_ext import ArrayField, JSONField

try:
    from cfg.settings import DATABASE_SETTINGS, DATABASE_CHARSET
except Exception as Error:
    DATABASE_SETTINGS, DATABASE_CHARSET = (), "utf8mb4"
    hues.warn(f'Ошибка инициализации подключения к БД: {Error}!\n'
              f'Для использования базы данны проверьте значения параметров '
              f'(DATABASE_SETTINGS, DATABASE_CHARSET).'
              f'в файле - "{FILE_SETTINGS}".')

driver_params = {}
if DATABASE_CHARSET:
    driver_params['charset'] = DATABASE_CHARSET

if len(DATABASE_SETTINGS) == 0:
    db_handler = None
else:
    name, host, port, user, password = DATABASE_SETTINGS
    db_handler = PostgresqlDatabase(name,
                                    host=host,
                                    port=port,
                                    user=user,
                                    password=password,
                                    **driver_params)


class BaseModel(Model):
    """Базовая модель БД"""

    class Meta:
        database = db_handler
        schema = 'public'


class Users(BaseModel):
    """Таблица пользователей ВК"""
    # id = PrimaryKeyField(unique=True)
    # uid = BigIntegerField(index=True, unique=True)  # id пользователя ВК
    uid = CharField(primary_key=True, unique=True, null=False)  # id пользователя ВК
    # uid = CharField(index=True, null=False)  # id пользователя ВК

    first_name = CharField(null=False)  # Имя
    last_name = CharField(null=True)  # Фамилия
    screen_name = CharField(null=True)  # отображаемое имя
    bdate = CharField(null=True)  # дата рождения, если указана
    sex = SmallIntegerField(default=0, null=True)  # пол
    relation = SmallIntegerField(default=0, null=True)  # отношение
    status = TextField(null=True)  # статус пользователя
    home_town = CharField(null=True)  # родной город пользователя
    city = JSONField(null=True)  # город пользователя
    offset = ArrayField(default=[0, 0, 0])  # сдвиги для поиска
    must_updated = BooleanField(default=False)  # данные должны быть обновлены

    datetime_update = DateTimeField(default=datetime.datetime.now(), null=True)  # дата обновления данных о пользователе

    class Meta:
        table_name = 'users'


class Friends(BaseModel):
    """Таблица найденных друзей для пользователей"""
    uid = ForeignKeyField(Users, backref='friends')  # id пользователя ВК
    fid = CharField(index=True, null=False)  # id друга ВК

    class Meta:
        table_name = 'friends'


class Favorites(BaseModel):
    """Таблица избранных друзей для пользователей"""
    uid = ForeignKeyField(Users, backref='favorites')  # id пользователя ВК
    fid = CharField(index=True, null=False)  # id друга ВК
    state = SmallIntegerField(default=0, null=False)  # статус друга: 0 - избранный, 1 - заблокированный

    class Meta:
        table_name = 'favorites'
