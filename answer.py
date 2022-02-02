from datetime import date

import hues

from vk_classes import VKSender, VKSearcher, VKUser
from chatter import Command, Keyboards


class MessageAnswer:
    def __init__(self, vk_search: VKSearcher, vk_sender: VKSender, vk_user: VKUser,
                 cmd: Command, answer: Keyboards, count_records: int, access_key, db):
        self.searcher = vk_search
        self.sender = vk_sender
        self.user = vk_user
        self.cmd = cmd
        self.count_records = count_records
        self.access_key = access_key
        self.db = db

        self.answer = answer
        self.answer_params = self.answer.keyboard.get(str(self.cmd.command), None)

    def process_message(self):
        # Отправка сообщения пользователю, согласно найденного ответа лексикона бота
        self.sender.send_message(self.user.data['id'], self.cmd.answer)

        if self.cmd.command != 99:
            getattr(self, self.cmd.function)()  # отправка сообщения, согласно выбранной команде

        self.answer_params = self.answer.keyboard.get('99', None)  # подготовка клавиатуры
        self.send_main_answer()  # отправка основного меню

    def send_message(self, message_text):
        params = {
            'receiver_user_id': self.user.data['id'],
            'message_text': message_text
        }
        self.sender.send_message(**params)

    def send_main_answer(self):
        params = {
            'receiver_user_id': self.user.data['id']
        }
        self.sender.send_message(**params, **self.answer_params)

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

    def search_friends(self):
        cnt_finds = 0
        founded_friends = []
        while cnt_finds < self.count_records:
            offset = self.db.get_offset(self.cmd.command)
            # offset = self.user.search['offset']
            friends = self._get_friends(self.cmd.command,
                                        offset,
                                        self.count_records)

            # self.user.search['offset'] += len(friends)
            offset += len(friends)
            self.db.update_offset(self.cmd.command, offset)

            friends = self.check_friends(friends)

            for friend in friends:
                if friend == 0 or cnt_finds == self.count_records:
                    break
                else:
                    if friend:
                        founded_friends.append(friend)
                        cnt_finds += 1

        if founded_friends:
            self.send_message(f'Показываю {cnt_finds} контактов:')

            for friend in founded_friends:
                # Установка параметров сообщения
                sender_params = self.set_message_friend(friend)

                # Отправка сообщения
                self.sender.send_message(**sender_params)

                # Сохранение контакта в список найденных
                self.db.add_friend(friend['id'])

        else:
            self.send_message(f'Подходящих контактов не найдено.')

    def check_friends(self, list_friends: list):
        new_friends = []
        for user in list_friends:
            if not user['is_closed'] and not self.db.is_friend_or_black(user['id']):

                if (self.user.data.get('city', None) and
                    self.user.data.get('city', None) != user.get('city', None)) or \
                        (self.user.data.get('howm_town', None) and
                         self.user.data.get('howm_town', None) != user.get('howm_town', None)):
                    continue

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
            'fields': 'photo_max, photo_id, sex, bdate, howm_town, status, city, relation, is_closed'
        }

        if len(self.user.data.get('bdate', None)) > 7:
            # search_params['birth_year'] = self.user.data['bdate'][-4:]
            search_params['age_from'] = date.today().year - int(self.user.data['bdate'][-4:]) - 1
            search_params['age_to'] = date.today().year - int(self.user.data['bdate'][-4:]) + 1

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
        if _dict.get('city', None):
            city = _dict["city"]["title"]
            message += f'\nг. {city}'

        # Добавление статус человека в сообщение
        relation = str(_dict.get('relation', 0))
        relation = self.searcher.guide['relation'].get(relation, None)
        if relation:
            message += f'\nСтатус - {relation}'

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
