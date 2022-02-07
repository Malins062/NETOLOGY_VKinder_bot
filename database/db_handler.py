import json  # для работы json-данными
from os.path import isfile  # наличие файла в системе
from os import remove  # удаление файла из системы

import peewee  # для работы с ORM PostgreSQL

from database.models import *  # загрузка моделей БД
from vk_classes import VKUser  # класс пользователя ВК


class PostgreSQLDatabase:
    """
    Класс работы с БД PostgreSQL
    """

    def __init__(self, path, user_id):
        self.KEY_FRIENDS = 'friends'
        self.KEY_FAVORITES = 'favorites'
        self.KEY_BLACKLIST = 'blacklist'
        self.KEY_USER = 'user'
        self.KEY_USER_OFFSET = 'offset'

        self.json_path = path
        self.user_id = str(user_id)
        self.file_name = self.json_path + '/' + str(self.user_id) + '.json'

    def _is_exists_user(self):
        try:
            data = Users.get_by_id(self.user_id)
            return {
                'id': self.user_id,
                'first_name': data.first_name,
                'last_name': data.last_name,
                'screen_name': data.last_name,
                'bdate': data.bdate,
                'sex': data.sex,
                'relation': data.relation,
                'status': data.status,
                'home_town': data.home_town,
                'city': data.city,
                self.KEY_USER_OFFSET: data.offset,
                'must_updated': data.must_updated
            }

        except peewee.DoesNotExist:
            return {}

    def get_user(self) -> dict:
        result = self._is_exists_user()

        if not result or result.get('must_updated', False):
            return {}

        else:
            return result

    def update_user(self, user_update: VKUser):
        try:
            if self._is_exists_user():
                self._update_user(user_update.data)
            else:
                Users.create(
                    uid=self.user_id,
                    first_name=user_update.data.get('first_name', ''),
                    last_name=user_update.data.get('last_name', ''),
                    screen_name=user_update.data.get('screen_name', ''),
                    bdate=user_update.data.get('bdate', ''),
                    sex=user_update.data.get('sex', 0),
                    relation=user_update.data.get('relation', 0),
                    status=user_update.data.get('status', ''),
                    home_town=user_update.data.get('home_town', ''),
                    city=user_update.data.get('city', {}),
                    offset=user_update.data.get(self.KEY_USER_OFFSET, [0, 0, 0])
                )

        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка вставки данных о пользователе {self.user_id} ВК в БД: {Err}')
            return {}

    def _update_user(self, data: dict):
        try:
            change_user = Users.get_by_id(self.user_id)
            change_user.first_name = data.get('first_name', '')
            change_user.last_name = data.get('last_name', '')
            change_user.screen_name = data.get('screen_name', '')
            change_user.bdate = data.get('bdate', '')
            change_user.sex = data.get('sex', 0)
            change_user.relation = data.get('relation', 0)
            change_user.status = data.get('status', '')
            change_user.home_town = data.get('home_town', '')
            change_user.city = data.get('city', {})
            change_user.offset = data.get(self.KEY_USER_OFFSET, [0, 0, 0])
            change_user.must_updated = False
            change_user.datetime_update = datetime.datetime.now()
            change_user.save()
        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка обновления данных о пользователе {self.user_id} ВК в БД: {Err}')

    def update_offset(self, user_update: VKUser):
        try:
            change_user = Users.get_by_id(self.user_id)
            change_user.offset = user_update.data.get(self.KEY_USER_OFFSET, [0, 0, 0])
            change_user.datetime_update = datetime.datetime.now()
            change_user.save()

        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка обновления данных сдвига поиска {self.user_id} ВК в БД: {Err}')
            return {}

    def add_friend(self, vk_id: int):
        try:
            Friends.get_or_create(
                uid=self.user_id,
                fid=str(vk_id)
            )

        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка вставки данных о найденном контакте в БД: {Err}')
            return {}

    def add_favorite(self, vk_id: int):
        try:
            Favorites.get_or_create(
                uid=self.user_id,
                fid=str(vk_id),
                state=0
            )
            return f'Контакт id{vk_id} успешно добавлен в список избранных.'

        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка вставки данных контакта в список избранных, в БД: {Err}')
            return f'Контакт id{vk_id} НЕ ДОБАВЛЕН в список избранных.'

    def add_blacklist(self, vk_id: int):
        try:
            Favorites.get_or_create(
                uid=self.user_id,
                fid=str(vk_id),
                state=1
            )
            return f'Контакт id{vk_id} успешно добавлен в "черный" список.'

        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка вставки данных контакта в черный список, в БД: {Err}')
            return f'Контакт id{vk_id} НЕ ДОБАВЛЕН в "черный" список.'

    def delete_favorite(self, vk_id: int):
        try:
            db_query = Favorites.delete().where(Favorites.uid == self.user_id, Favorites.fid == str(vk_id),
                                                Favorites.state == 0)
            db_query.execute()
            return f'Контакт id{vk_id} удален из списка избранных.'

        except peewee.PeeweeException:
            return f'Контакт id{vk_id} НЕ УДАЛЕН из списка избранных.'

    def clear_friends(self):
        try:
            db_query = Friends.delete().where(Friends.uid == self.user_id)
            db_query.execute()
            return f'Список результатов поиска контактов УДАЛЕН.'

        except peewee.PeeweeException:
            return f'Список  результатов поиска контактов НЕ ОЧИЩЕН.'

    def clear_search(self):
        try:
            clear_user = Users.get_by_id(self.user_id)
            clear_user.offset = [0, 0, 0]
            clear_user.save()
            return True

        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка обновления сброса поиска в БД: {Err}')
            return False

    def clear_user(self):
        try:
            clear_user = Users.get_by_id(self.user_id)
            clear_user.must_updated = True
            clear_user.save()
            return f'Ваши личные данные обновлены.'

        except peewee.PeeweeException:
            return f'Личные данные НЕ ОБНОВЛЕНЫ!'

    def clear_favorites(self):
        try:
            db_query = Favorites.delete().where(Favorites.uid == self.user_id, Favorites.state == 0)
            db_query.execute()
            return f'Список избранных контактов УДАЛЕН.'

        except peewee.PeeweeException:
            return f'Список избранных контактов НЕ ОЧИЩЕН.'

    def clear_blacklist(self):
        try:
            db_query = Favorites.delete().where(Favorites.uid == self.user_id, Favorites.state == 1)
            db_query.execute()
            return f'"Черный" список УДАЛЕН.'

        except peewee.PeeweeException:
            return f'"Черный" список контактов НЕ ОЧИЩЕН.'

    def delete_blacklist(self, vk_id: int):
        try:
            db_query = Favorites.delete().where(Favorites.uid == self.user_id, Favorites.fid == str(vk_id),
                                                Favorites.state == 1)
            db_query.execute()
            return f'Контакт id{vk_id} удален из "черного" списка.'

        except peewee.PeeweeException:
            return f'Контакт id{vk_id} НЕ УДАЛЕН из "черного" списка.'

    def get_favorites(self) -> list:
        try:
            db_query = Favorites.select(Favorites.fid).where(Favorites.uid == self.user_id, Favorites.state == 0)
            _list = []
            for value in db_query:
                _list.append(value.fid)
            return _list

        except peewee.PeeweeException:
            return []

    def get_blacklist(self) -> list:
        try:
            db_query = Favorites.select(Favorites.fid).where(Favorites.uid == self.user_id, Favorites.state == 1)
            _list = []
            for value in db_query:
                _list.append(value.fid)
            return _list

        except peewee.PeeweeException:
            return []

    def is_friend_or_black(self, vk_id: int):
        try:
            db_query_friend = Friends.select(Friends.fid).where(Friends.uid_id == self.user_id,
                                                                Friends.fid == str(vk_id))
            db_query_black_favorites = Favorites.select(Favorites.fid).where(Favorites.uid_id == self.user_id,
                                                                             Favorites.fid == str(vk_id))
            return bool(db_query_friend) or bool(db_query_black_favorites)

        except peewee.PeeweeException:
            return False

    def json_to_db(self):
        try:
            data = self._read_json()
            if data and data.get(self.KEY_USER, False) and data[self.KEY_USER].get('id', False):
                # Обновление пользователя
                self._update_user(data[self.KEY_USER])

                # Обновление найденных контактов из JSON в БД
                for value in data.get(self.KEY_FRIENDS, []):
                    self.add_friend(value)

                # Обновление избранных друзей из JSON в БД
                for value in data.get(self.KEY_FAVORITES, []):
                    self.add_favorite(value)

                # Обновление черного списка друзей из JSON в БД
                for value in data.get(self.KEY_BLACKLIST, []):
                    self.add_blacklist(value)

                self._delete_json()

        except Exception as err:
            hues.warn(f'ОШИБКА миграции данных из JSON в БД - {self.file_name}: {err}')

    def _read_json(self):
        try:
            result = False

            if isfile(self.file_name):
                with open(self.file_name) as f:
                    result = json.load(f)

        except Exception as err:
            hues.warn(f'ОШИБКА чтения данных из файла - {self.file_name}: {err}')

        finally:
            return result

    def _delete_json(self):
        try:
            if isfile(self.file_name):
                remove(self.file_name)

        except Exception as err:
            hues.warn(f'ОШИБКА удаления файла - {self.file_name}: {err}')
