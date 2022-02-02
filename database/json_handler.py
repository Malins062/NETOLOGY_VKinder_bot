import json
import hues
from os.path import isfile
from vk_classes import VKUser


class JSONDatabase:

    def __init__(self, path, user_id):
        self.KEY_FRIENDS = 'friends'
        self.KEY_FAVORITES = 'favorites'
        self.KEY_BLACKLIST = 'blacklist'
        self.KEY_USER = 'user'
        self.KEY_USER_DATA = 'data'
        self.KEY_USER_OFFSET = 'offset'

        self.json_path = path
        self.user_id = user_id
        self.file_name = self.json_path + '/' + str(self.user_id) + '.json'

    def get_user(self) -> dict:
        data = self._read_json_key(self.KEY_USER)
        return data.get(self.KEY_USER_DATA, False) if isinstance(data, dict) else False

    def update_user(self, user: VKUser):
        self._update_user_json(user)

    def get_offset(self, index: int):
        data = self._read_json_key(self.KEY_USER)
        return data.get(self.KEY_USER_OFFSET, [0, 0, 0])[index] if isinstance(data, dict) else 0

    def update_offset(self, index: int, value_offset: int):
        self._update_offset_json(index, value_offset)

    def add_friend(self, vk_id: int):
        self._append_json(self.KEY_FRIENDS, vk_id)

    def add_favorite(self, vk_id: int):
        if self._append_json(self.KEY_FAVORITES, vk_id):
            return f'Контакт id{vk_id} успешно добавлен в список избранных.'
        else:
            return f'Контакт id{vk_id} НЕ ДОБАВЛЕН в список избранных.'

    def add_blacklist(self, vk_id: int):
        if self._append_json(self.KEY_BLACKLIST, vk_id):
            return f'Контакт id{vk_id} успешно добавлен в "черный" список.'
        else:
            return f'Контакт id{vk_id} НЕ ДОБАВЛЕН в "черный" список.'

    def delete_favorite(self, vk_id: int):
        if self._delete_json_key(self.KEY_FAVORITES, vk_id):
            return f'Контакт id{vk_id} удален из списка избранных.'
        else:
            return f'Контакт id{vk_id} НЕ УДАЛЕН из списка избранных.'

    def clear_friends(self):
        if self._clear_json_key(self.KEY_FRIENDS):
            return f'Список результатов поиска контактов УДАЛЕН.'
        else:
            return f'Список  результатов поиска контактов НЕ ОЧИЩЕН.'

    def clear_search(self):
        self._clear_search_json()

    def clear_favorites(self):
        if self._clear_json_key(self.KEY_FAVORITES):
            return f'Список избранных контактов УДАЛЕН.'
        else:
            return f'Список избранных контактов НЕ ОЧИЩЕН.'

    def clear_blacklist(self):
        if self._clear_json_key(self.KEY_BLACKLIST):
            return f'"Черный" список УДАЛЕН.'
        else:
            return f'"Черный" список контактов НЕ ОЧИЩЕН.'

    def delete_blacklist(self, vk_id: int):
        if self._delete_json_key(self.KEY_BLACKLIST, vk_id):
            return f'Контакт id{vk_id} удален из "черного" списка.'
        else:
            return f'Контакт id{vk_id} НЕ УДАЛЕН из "черного" списка.'

    def get_favorites(self) -> list:
        return self._read_json_key(self.KEY_FAVORITES)

    def get_blacklist(self) -> list:
        return self._read_json_key(self.KEY_BLACKLIST)

    def is_friend_or_black(self, vk_id: int):
        try:
            data = self._read_json()  # чтение данных из json файла
            return vk_id in data[self.KEY_FRIENDS] or vk_id in data[self.KEY_BLACKLIST]

        except Exception as err:
            hues.warn(f'ОШИБКА чтения данных из файла - {self.file_name}: {err}')
            return False

    def _append_json(self, key: str, contact_id: int):
        try:
            data = self._read_json()  # чтение данных из json файла

            # Добавление контакта в список по ключу
            if contact_id not in data[key]:
                data[key] += [contact_id]

            self._write_json(data)  # запись данных в файл
            return True

        except Exception as err:
            hues.warn(f'ОШИБКА добавления данных в файл - {self.file_name}: {err}')
            return False

    def _update_offset_json(self, index: int, value_offset: int):
        try:
            data = self._read_json()  # чтение данных из json файла

            if self.KEY_USER not in data:
                data[self.KEY_USER] = {}

            data[self.KEY_USER][self.KEY_USER_OFFSET][index] = value_offset  # сохранение информации о сдвиге поиска
            self._write_json(data)  # запись данных в файл
            return True

        except Exception as err:
            hues.warn(f'ОШИБКА обновления данных в файле - {self.file_name}: {err}')
            return False

    def _update_user_json(self, user_data: VKUser):
        try:
            data = self._read_json()  # чтение данных из json файла

            if self.KEY_USER not in data:
                data[self.KEY_USER] = {}

            data[self.KEY_USER][self.KEY_USER_DATA] = user_data.data  # сохранение информации о пользователе
            self._write_json(data)  # запись данных в файл
            return True

        except Exception as err:
            hues.warn(f'ОШИБКА обновления данных в файле - {self.file_name}: {err}')
            return False

    def _delete_json_key(self, key: str, contact_id: int):
        try:
            data = self._read_json() # чтение данных из json файла

            # Удаление контакта из списка по ключу
            if contact_id in data[key]:
                data[key].remove(contact_id)

            self._write_json(data)  # запись данных в файл
            return True

        except Exception as err:
            hues.warn(f'ОШИБКА удаления данных из файла - {self.file_name}: {err}')
            return False

    def _clear_json_key(self, key: str):
        try:
            data = self._read_json() # чтение данных из json файла
            data[key] = []  # удаления данных по ключу
            self._write_json(data)  # запись данных в файл
            return True

        except Exception as err:
            hues.error(f'ОШИБКА удаления данных из файла - {self.file_name}: {err}')
            return False

    def _clear_search_json(self):
        try:
            data = self._read_json()  # чтение данных из json файла
            data[self.KEY_USER][self.KEY_USER_OFFSET] = [0, 0, 0]  # сброс всех сдвигов поиска
            self._write_json(data)  # запись данных в файл
            return True

        except Exception as err:
            hues.error(f'ОШИБКА удаления данных из файла - {self.file_name}: {err}')
            return False

    def _read_json_key(self, key: str):
        result = False
        try:
            result = self._read_json().get(key, False)

        except Exception as err:
            hues.warn(f'ОШИБКА чтения данных из файла - {self.file_name}: {err}')

        return result

    def _read_json(self):
        try:
            result = {
                self.KEY_FRIENDS: [],
                self.KEY_FAVORITES: [],
                self.KEY_BLACKLIST: [],
                self.KEY_USER: {self.KEY_USER_DATA: {}, self.KEY_USER_OFFSET: [0, 0, 0]}
            }

            if isfile(self.file_name):
                with open(self.file_name) as f:
                    result = json.load(f)

        except Exception as err:
            hues.warn(f'ОШИБКА чтения данных из файла - {self.file_name}: {err}')

        finally:
            return result

    def _write_json(self, data_for_write):
        try:
            with open(self.file_name, 'w') as f:
                json.dump(data_for_write, f)
            return True

        except Exception as err:
            hues.error(f'ОШИБКА записи данных {data_for_write} в файл - {self.file_name}: {err}')
            return False


