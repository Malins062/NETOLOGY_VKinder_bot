from vk_api.vk_api import VkApiMethod
from vk_api.utils import get_random_id  # использование get_random_id для messages.send
from utils import *  # свои дополнительные функции


class VKUser:
    __slots__ = ('data', 'vk_api_object', 'user_id')

    def __init__(self, vk_api_object: VkApiMethod, uid):
        self.vk_api_object = vk_api_object  # объект для доступа к запросам ВК
        self.data = None
        self.user_id = uid

    def get_user_data(self):
        params = {
            'user_id': self.user_id,
            'fields': 'screen_name, bdate, sex, relation, status, home_town, city'
        }
        try:
            # Данные пользователя ВК
            self.data = self.vk_api_object.users.get(**params)[0]
            self.data['offset'] = [0, 0, 0]

            if self.data.get('first_name', None) and self.data.get('first_name', None):
                self.data['name'] = f'{self.data["first_name"]} {self.data["last_name"]}'

        except Exception as Err:
            self.data = Err


class VKSearcher:

    def __init__(self, vk_api_object: VkApiMethod, file_name):
        # Загрузка справочника ВК
        try:
            self.guide = read_json(file_name)
        except Exception as Err:
            fatal(f'Ошибка загрузки справочника ВК: {Err}')

        self.vk = vk_api_object

    def get_users_search(self, **kwargs):
        """
        Поиск пользователей ВК по критериям которые необходимо вытащить.
        :param kwargs: параметры запроса (пол, возраст, город, семейное положение...)
        :return: список пользователей
        """
        # Получение сведений из ВК методом users.search
        result = self.vk.users.search(**kwargs)

        return result

    def get_users_photos(self, **kwargs):
        """
        Поиск фотографий пользователей ВК по критериям которые необходимо вытащить
        :param kwargs: параметры запроса (owner_id, album_id...)
        :return: спписок пользователей
        """
        # Получение сведений из ВК методом photos.get
        result = self.vk.photos.get(**kwargs)

        return result

    def get_cities_by_id(self, **kwargs):
        """
        Поиск названий городов в ВК, по их идентификаторам.
        :param kwargs: параметры запроса (список идентификаторов городов...)
        :return: список названий городов
        """
        # Получение названий городов из ВК методом database.getCitiesById
        result = self.vk.database.getCitiesById(**kwargs)

        return result


class VKSender:
    """
    Класс для отправки сообщений с помощью библиотеки vk_api
    """

    # Флаг отсутствия клавиатуры к сообщению
    NONE_KEY_BOARD = '{\n "one_time": true,\n "buttons": []\n}'

    def __init__(self, vk_api_object: VkApiMethod, log_messages: bool):
        self.vk = vk_api_object
        self.log_messages = log_messages

    def send_message(self, receiver_user_id: str = None,
                     message_text: str = '',
                     keyboard: str = NONE_KEY_BOARD,
                     attachment: str = None):
        """
        Отправка сообщения от лица авторизованного пользователя
        :param receiver_user_id: уникальный идентификатор получателя сообщения
        :param message_text: текст отправляемого сообщения
        :param keyboard: клавиатура к сообщению
        :param attachment: фото или что-то другое, прикрепленное к сообщению
        """

        # Параметры сообщения
        params_message = {
            'user_id': receiver_user_id,
            'message': message_text,
            'keyboard': keyboard,
            'random_id': get_random_id()
        }

        # Добавление вложенной, инфы если она заполнена
        if attachment:
            params_message['attachment'] = attachment

        try:
            self.vk.messages.send(**params_message)

            if self.log_messages:
                hues.info(f'--> Сообщение отправлено для пользователя id{receiver_user_id} > {message_text}')
        except Exception as error:
            hues.warn(f'ОШИБКА отправки сообщения: {error}')
