from datetime import date

from vk_classes import VKSender, VKSearcher, VKUser
from chatter import Command, Keyboards


class MessageAnswer:
    def __init__(self, vk_search: VKSearcher, vk_sender: VKSender, vk_user: VKUser,
                 cmd: Command, answer: Keyboards, count_records: int, year_offset: int, access_key, db):
        self.searcher = vk_search
        self.sender = vk_sender
        self.user = vk_user
        self.cmd = cmd
        self.count_records = count_records
        self.year_offset = year_offset
        self.access_key = access_key
        self.db = db
        self.params_receiver = {
            'receiver_user_id': self.user.data['id']
        }

        self.answer = answer
        self.answer_params = self.answer.keyboard.get(str(self.cmd.command), None)

    def process_message(self):
        # Отправка сообщения пользователю, согласно найденного ответа лексикона бота
        self.sender.send_message(self.user.data['id'], self.cmd.answer)

        if self.cmd.command != 99:
            getattr(self, self.cmd.function)()  # отправка сообщения, согласно выбранной команде

        self.send_main_answer()  # отправка основного меню

    def send_message(self, message_text):
        params = {
            'message_text': message_text
        }
        self.sender.send_message(**self.params_receiver, **params)

    def send_main_answer(self):
        params = self.answer.keyboard.get('99', None)  # подготовка клавиатуры
        self.sender.send_message(**self.params_receiver, **params)

    def add_favorite(self):
        self.send_message(self.db.add_favorite(self.cmd.contact_id))

    def add_blacklist(self):
        self.send_message(self.db.add_blacklist(self.cmd.contact_id))

    def delete_favorite(self):
        self.send_message(self.db.delete_favorite(self.cmd.contact_id))

    def delete_blacklist(self):
        self.send_message(self.db.delete_blacklist(self.cmd.contact_id))

    def clear_search(self):
        self.db.clear_search()
        self.send_message(self.db.clear_friends())

    def clear_favorites(self):
        self.send_message(self.db.clear_favorites())

    def clear_blacklist(self):
        self.send_message(self.db.clear_blacklist())

    def update_user(self):
        self.send_message(self.db.clear_user())

    def account_user(self):
        _LINE = '-' * 70 + '\n'
        message = _LINE
        message += self.answer_params.get('message_text', '')  # подготовка клавиатуры
        # data = self.db.get_user()  # получение текущей информации пользователя
        data = self.user.data  # получение текущей информации пользователя
        message += self._user_info(data) if data else '\nЛичные данные пользователя не найдены!\n'
        message += _LINE
        message += '\nЖду от Вас команды:'
        params = {
            'message_text': message,
            'keyboard': self.answer_params.get('keyboard', None)
        }

        self.sender.send_message(**self.params_receiver, **params)

    def list_search_params(self):
        _LINE = '-' * 70 + '\n'
        message = _LINE
        message += self.answer_params.get('message_text', '')  # подготовка клавиатуры
        data = self.user.data  # получение текущей информации пользователя
        message += self._search_info(data) if data else '\nПараметры поиска не найдены!\n'
        message += _LINE
        message += '\nЖду от Вас команды:'
        params = {
            'message_text': message,
            'keyboard': self.answer_params.get('keyboard', None)
        }

        self.sender.send_message(**self.params_receiver, **params)

    def _user_info(self, _dict: dict) -> str:
        _EMPTY_DATA = 'не указано'

        message = '\nID: ' + str(_dict.get('id', _EMPTY_DATA))
        message += '\nИмя: ' + _dict.get('first_name', _EMPTY_DATA)
        message += '\nФамилия: ' + _dict.get('last_name', _EMPTY_DATA)
        message += '\nДата рождения: ' + _dict.get('bdate', _EMPTY_DATA)

        message += '\nПол: '
        value = str(_dict.get('sex', 0))
        value = self.searcher.guide['sex'].get(value, None)
        message += value if value else _EMPTY_DATA

        message += '\nГород: '
        value = _dict.get('city', None)
        message += _dict['city']['title'] if value else _EMPTY_DATA
        message += '\nРодной город = '
        value = _dict.get('home_town', _EMPTY_DATA)
        message += value if value else _EMPTY_DATA

        message += '\nСемейное положение: '
        value = str(_dict.get('relation', 0))
        value = self.searcher.guide['relation'].get(value, None)
        message += value if value else _EMPTY_DATA

        message += '\n'

        return message

    def _search_info(self, _dict: dict) -> str:
        _ANY_DATA = 'любое значение'

        message = '\nВозраст '
        bdate = _dict.get('bdate', '')
        if bdate and len(bdate) > 7:
            message += 'от ' + str((date.today().year - int(bdate[-4:]) - self.year_offset))
            message += ' до ' + str((date.today().year - int(bdate[-4:]) + self.year_offset + 1))
        else:
            message = '= ' + _ANY_DATA

        message += '\nПол = '
        value = str(_dict.get('sex', 0))
        value = self.searcher.guide['sex'].get(value, None)
        message += value if value else _ANY_DATA

        message += '\nГород = '
        value = _dict.get('city', None)
        message += _dict['city']['title'] if value else _ANY_DATA
        message += '\nРодной город = '
        value = _dict.get('home_town', _ANY_DATA)
        message += value if value else _ANY_DATA

        message += '\nСемейное положение = '
        value = str(_dict.get('relation', 0))
        value = self.searcher.guide['relation'].get(value, None)
        message += value if value else _ANY_DATA

        message += '\n'

        return message

    def list_favorites(self):
        contacts = self.db.get_favorites()  # получение списка id избранных контактов

        # Проверка на наличие контактов в списке
        if contacts:
            self._list_contacts(contacts)  # вывод списка контактов

        else:
            self.send_message('В списке избранных контактов пока никого нет.')

    def list_blacklist(self):
        contacts = self.db.get_blacklist()  # получение черного списка id контактов

        # Проверка на наличие контактов в списке
        if contacts:
            self._list_contacts(contacts)  # вывод списка контактов

        else:
            self.send_message('В "черном" списке контактов пока никого нет.')

    def _list_contacts(self, _list_contacts):
        for vk_id in _list_contacts:
            # Получение данных о контакте
            user = VKUser(self.user.vk_api_object, vk_id)
            user.get_user_data()

            if user.data.get('id', False):
                contact = user.data
                photos = self._get_user_photos(contact['id'])
                if photos:
                    contact.update(photos)

                # Установка параметров сообщения
                sender_params = self.set_message_friend(contact)

                # Отправка сообщения
                self.sender.send_message(**sender_params)

    def search_friends(self):
        cnt_finds = 0
        founded_friends = []
        offset = self.user.data['offset'][self.cmd.command]
        while cnt_finds < self.count_records:
            friends = self._get_friends(self.cmd.command,
                                        offset,
                                        self.count_records)

            cnt_friends = len(friends)
            if cnt_friends > 0:
                offset += cnt_friends
            else:
                break

            friends = self.check_friends(friends)

            for friend in friends:
                if friend == 0 or cnt_finds == self.count_records:
                    break
                else:
                    if friend:
                        founded_friends.append(friend)
                        self.db.add_friend(friend['id'])  # Сохранение контакта в список найденных
                        cnt_finds += 1

        if founded_friends:
            self.user.data['offset'][self.cmd.command] = offset

            self.send_message(f'Показываю {cnt_finds} контактов:')

            for friend in founded_friends:
                # Установка параметров сообщения
                sender_params = self.set_message_friend(friend)

                # Отправка сообщения
                self.sender.send_message(**sender_params)

        else:
            self.user.data['offset'][self.cmd.command] = 0
            self.send_message(f'Подходящих контактов не найдено.')

        self.db.update_offset(self.user)

    def check_friends(self, list_friends: list):
        new_friends = []
        for user in list_friends:
            if not user['is_closed'] and not self.db.is_friend_or_black(user['id']):

                # if (self.user.data.get('city', None) and
                #     self.user.data.get('city', None) != user.get('city', None)) or \
                #         (self.user.data.get('home_town', None) and
                #          self.user.data.get('home_town', None) != user.get('hometown', None)):
                #     continue

                photos = self._get_user_photos(user['id'])
                if photos:
                    new_friends.append({**user, **photos})

        return new_friends

    def _get_friends(self, sex, offset, cnt):
        # Параметры запроса поиска друзей
        search_params = {
            'sort': 0,
            'has_photo': 1,
            'offset': offset,
            'count': cnt,
            'sex': sex,
            'fields': 'photo_max, photo_id, sex, bdate, home_town, status, city, interests,'
                      'books, music, relation, is_closed'
        }

        bdate = self.user.data.get('bdate', None)
        if bdate and len(bdate) > 7:
            # search_params['birth_year'] = self.user.data['bdate'][-4:]
            search_params['age_from'] = date.today().year - int(bdate[-4:]) - self.year_offset
            search_params['age_to'] = date.today().year - int(bdate[-4:]) + self.year_offset

        if self.user.data.get('city', None):
            search_params['city'] = self.user.data['city']['id']
        elif self.user.data.get('home_town', None):
            search_params['hometown'] = self.user.data['home_town']

        search_params['status'] = self.user.data.get('relation', 0)

        result = self.searcher.get_users_search(**search_params)

        if not result.get('count', 0):
            return []

        friends = result.get('items', None)

        return friends

    def _get_user_photos(self, owner_id) -> dict:

        # Параметры запроса
        photos_params = {
            'extended': 1,
            'owner_id': owner_id,
            'album_id': 'profile'
        }

        # Запрос к ресурсу
        result = self.searcher.get_users_photos(**photos_params)

        # Проверка на наличие необходимых данных в ответе сервера
        if len(result.get('items', None)) < 3:
            return {}

        # Создание списка фоток с подсчетом количества лайков и комментов
        new_result = []
        for key, value in enumerate(result['items']):
            new_result.append({
                'photo_id': value['id'],
                'owner_id': value['owner_id'],
                'likes': value['likes']['count'] + value['comments']['count']
            })

        # Сортировка фоток по значению атрибута 'likes'
        new_result = sorted(new_result, key=lambda x: x.get('likes'), reverse=True)

        # Выборка ТОП-3 фоток
        photo_result = {
            'photos': [new_result[photo] for photo in range(3)]
        }

        return photo_result

    def set_message_friend(self, _dict) -> dict:
        # Параметры сообщения
        params = {}

        # Формирование Имя и Фамилии пользователя в тексте сообщения
        first_name = _dict.get('first_name', '')
        last_name = _dict.get('last_name', '')
        message = f'{first_name} {last_name}'

        # Добавление вывода даты рождения человека в сообщение
        bdate = _dict.get('bdate', None)
        if bdate:
            message += f', '
            for value in bdate.split('.'):
                value = value.rjust(2, "0")
                message += f'{value}.'
            message += f' г.р.'

        # Добавление вывода пола человека в сообщение
        sex = str(_dict.get('sex', 0))
        sex = self.searcher.guide['sex'].get(sex, None)
        if sex:
            message += f', пол: {sex}'

        # Добавление вывода города человека в сообщение
        city = _dict.get('city', None)
        if city:
            city = _dict['city']['title']
            message += f'\nг. {city}'

        # Добавление вывода родного города человека в сообщение
        if _dict.get('home_town', None):
            home_town = _dict['home_town']
            message += f' (родной город: {home_town})' if city else f'\nРодной город: {home_town}'

        # Добавление статус человека в сообщение
        relation = str(_dict.get('relation', 0))
        relation = self.searcher.guide['relation'].get(relation, None)
        if relation:
            message += f'\nСемейное положение - {relation}'

        # Добавление статуса человека в сообщение
        if _dict.get('status', None):
            value = _dict['status']
            message += f'\nСтатус: {value}'

        # Добавление интересов человека в сообщение
        if _dict.get('interests', None):
            value = _dict['interests']
            message += f'\nИнтересы: {value}'

        # Добавление любимых книг человека в сообщение
        if _dict.get('books', None):
            value = _dict['books']
            message += f'\nКниги: {value}'

        # Добавление любимой музыки человека в сообщение
        if _dict.get('music', None):
            value = _dict['music']
            message += f'\nМузыка: {value}'

        photos = _dict.get('photos', None)
        photo = [f'photo{value["owner_id"]}_{value["photo_id"]}_{self.access_key}' for value in photos]
        if photo:
            params['attachment'] = photo
        else:
            message += f'\nНет фото.'

        # Добавление ссылки на человека и кнопок к сообщению
        user_id = str(_dict.get('id', ''))
        link_contact = 'https://vk.com/id' + user_id
        if self.answer_params:
            params['keyboard'] = self.answer_params['keyboard'].replace(r'"link": ""', r'"link": "'+link_contact+r'"')
            params['keyboard'] = params['keyboard'].replace(r'\"type\": \"id\"', r'\"type\": \"'+user_id+r'\"')
        else:
            message += f'\n Ссылка на контакт: {link_contact}'

        # Формирование сообщения
        params['message_text'] = message

        # Формирование адресата
        params['receiver_user_id'] = self.user.data['id']

        return params
