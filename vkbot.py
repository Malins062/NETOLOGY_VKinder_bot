# Для операции с файлами
import shutil
from os.path import isfile

# Дополнительные классы для работы ВК
import peewee

from vk_classes import VKSearcher, VKSender, VKUser

# Дополнительные свои функции
from chatter import *
from utils import *
from answer import MessageAnswer

# Для работы с API VK
import vk_api  # использование VK API для бота ВКонтакте
from vk_api.longpoll import VkLongPoll, VkEventType  # использование VkLongPoll и VkEventType

from database.db_handler import *  # для работы с БД
from database.json_handler import *  # для работы с JSON вместо БД

# Файл параметров запуска бота
FILE_SETTINGS = 'cfg/settings.py'

# Файл параметров запуска бота ПРИМЕР
FILE_SETTINGS_SAMPLE = 'cfg/settings.py.sample'


class VKBot:
    """Главный класс бота"""
    # Использование slots для экономии памяти
    __slots__ = ['ACCESS_TOKEN_GROUP', 'ACCESS_TOKEN_USER', 'VK_GUIDE_FILE_NAME',
                 'LOG_COMMANDS', 'LOG_MESSAGES', 'LEXICON_FILE_NAME', 'ANSWER_FILE_NAME',
                 'COUNT_RECORDS', 'DATABASE_REWRITE', 'DATABASE_JSON', 'YEAR_OFFSET',
                 'vk_group', 'vk_user', 'vk_session', 'vk_searcher', 'vk_sender',
                 'long_poll', 'users', 'chat', 'keyboards', 'db']

    @progress_indicator('Инициализация параметров бота...', 'Параметры инициализированы. Бот готов к запуску.')
    def __init__(self):
        # Параметры бота
        self.DATABASE_JSON = None
        self.DATABASE_REWRITE = None
        self.COUNT_RECORDS = None
        self.LOG_COMMANDS = None
        self.LOG_MESSAGES = None
        self.VK_GUIDE_FILE_NAME = None
        self.ANSWER_FILE_NAME = None
        self.LEXICON_FILE_NAME = None
        self.YEAR_OFFSET = None
        self.ACCESS_TOKEN_USER = None
        self.ACCESS_TOKEN_GROUP = None

        self.long_poll = None
        self.vk_session = None
        self.vk_group = None
        self.vk_user = None
        self.vk_sender = None
        self.vk_searcher = None
        self.db = None
        self.keyboards = None
        self.chat = None
        self.users = None

        self.init_settings()  # инициализация параметров бота
        self.init_db()  # инициализация подключения к БД
        self.init_chat()  # инициализация данных для чата
        self.init_vk()  # авторизация бота

    def init_settings(self):
        """Функция инициализации файла параметров запуска бота или его создания"""
        self.users = {}

        # Если у нас есть только FILE_SETTINGS_SAMPLE
        if isfile(FILE_SETTINGS_SAMPLE) and not isfile(FILE_SETTINGS):
            try:
                shutil.copy(FILE_SETTINGS_SAMPLE, FILE_SETTINGS)
            except Exception as Ex:
                fatal(f'Невозможно скопировать файлы ("{FILE_SETTINGS_SAMPLE}" -> "{FILE_SETTINGS_SAMPLE}") '
                      f'в текущей папке, проверьте Ваши права на неё!\n'
                      f'Ошибка: {Ex}')

        # Если у нас уже есть FILE_SETTINGS
        elif isfile(FILE_SETTINGS):
            from cfg import settings
            try:
                self.ACCESS_TOKEN_GROUP = settings.ACCESS_TOKEN_GROUP
                self.ACCESS_TOKEN_USER = settings.ACCESS_TOKEN_USER

                if not (self.ACCESS_TOKEN_GROUP or self.ACCESS_TOKEN_USER):
                    fatal(f'Проверьте, что у есть "ACCESS_TOKEN_GROUP" и "ACCESS_TOKEN_USER" в файле '
                          f'{FILE_SETTINGS}!\nБез них БОТ работать НЕ СМОЖЕТ!.')

                self.LEXICON_FILE_NAME = settings.LEXICON_FILE_NAME
                self.ANSWER_FILE_NAME = settings.ANSWER_FILE_NAME
                self.VK_GUIDE_FILE_NAME = settings.VK_GUIDE_FILE_NAME

                self.LOG_MESSAGES = settings.LOG_MESSAGES
                self.LOG_COMMANDS = settings.LOG_COMMANDS

                self.DATABASE_REWRITE = settings.DATABASE_REWRITE
                self.DATABASE_JSON = settings.DATABASE_JSON

                self.YEAR_OFFSET = settings.YEAR_OFFSET
                self.COUNT_RECORDS = settings.COUNT_RECORDS

            except (ValueError, AttributeError, NameError):
                fatal(f'Проверьте содержимое файла - "{FILE_SETTINGS}", возможно Вы удалили что-то нужное!')

        # Если не нашли ни FILE_SETTINGS, ни FILE_SETTINGS_SAMPLE
        else:
            fatal(f'Файлы - "{FILE_SETTINGS}" и "{FILE_SETTINGS_SAMPLE}" не найдены, возможно вы их удалили?')

    def init_db(self):
        """Функция инициализации подключения к БД и первичная настройка"""
        if self._connect_db(db_handler):
            # Подключение к БД
            # self.db.connect(reuse_if_open=True)
            # db_handler.connect(reuse_if_open=True)

            try:
                # Удаление таблиц
                if self.DATABASE_REWRITE:
                    # self.db.drop_tables([Users, Friends, Favorites], cascade=True)
                    db_handler.drop_tables([Users, Friends, Favorites], cascade=True)

                # Создание таблиц
                # self.db.create_tables([Users, Friends, Favorites])
                db_handler.create_tables([Users, Friends, Favorites])

            except Exception as Err:
                # self.db = None
                hues.warn(f'Ошибка создания таблиц БД: {Err}\n'
                          f'Необходимо запустить бот с параметром "DATABASE_REWRITE = True" в файле {FILE_SETTINGS}')

        # except Exception as Ex:
        #     self.db = None
        #     hues.warn(f'Ошибка при инициализации работы с БД: {Ex}!\n'
        #               f'Дальнейшая работа бота будет продолжена без использования БД.')
        else:
            # self.db = None
            hues.warn(f'Проблемы с инициализацией БД!\n'
                      f'Дальнейшая работа бота будет продолжена без использования БД.')

    @staticmethod
    def _connect_db(handler):
        try:
            handler.connect(reuse_if_open=True)
            return True
        except peewee.PeeweeException as Err:
            hues.warn(f'Ошибка соединения с БД: {Err}!\n')
            return False

    def init_chat(self):
        """Функция инициализации дополнительных данных для чата"""
        self.chat = Chatter(self.LEXICON_FILE_NAME)  # инициализация лексикона
        self.keyboards = Keyboards(self.ANSWER_FILE_NAME)  # инициализация клавиатур для ответчика на запросы

    def init_vk(self):
        """Функция авторизации пользователя и сообщества API ВКонтакте"""
        self.vk_user = self.do_auth(self.ACCESS_TOKEN_USER)
        self.vk_group = self.do_auth(self.ACCESS_TOKEN_GROUP)

        if not (self.vk_group and self.vk_user):
            fatal('Бот не авторизовался, запуск невозможен!')

        self.vk_searcher = VKSearcher(self.vk_user, self.VK_GUIDE_FILE_NAME)
        self.vk_sender = VKSender(self.vk_group, self.LOG_MESSAGES)

    def do_auth(self, token):
        """Авторизация vk_api"""
        try:
            self.vk_session = vk_api.VkApi(token=token)
            return self.vk_session.get_api()
        except Exception as Ex:
            fatal(f'ОШИБКА авторизации: {Ex}')
            return None

    def init_long_polling(self):
        """Функция для инициализации Long Polling"""
        self.long_poll = VkLongPoll(self.vk_session)

        if not self.long_poll:
            fatal('Не удалось получить значения Long Poll сервера!')

    def _update_user(self, _user: VKUser):
        uid = _user.data.get('user_id', None)
        if uid:
            self.users[uid] = _user.data

    def check_event(self, new_event):
        """Проверка получения ЛС от пользователя"""
        # Если сообщение пришло личное и оно не пустое
        if new_event.type == VkEventType.MESSAGE_NEW and \
                new_event.to_me and \
                new_event.text:

            # Параметры сообщения
            uid = new_event.user_id  # id отправителя
            msg_id = new_event.message_id  # id сообщения
            dt = new_event.timestamp  # время сообщения
            msg = new_event.text  # текст сообщения
            contact_id = contact_id_from_dict(new_event.extra_values)  # id контакта вызова кнопки

            # Создание экземпляра сообщения
            event_data = MessageEventData(uid, msg_id, dt, msg, contact_id)

            # if uid not in self.users:
            #     self.users[uid] = VKUser(self.vk_group, uid)

            # user_vk = VKUser(self.vk_group, uid)

            if self._connect_db(db_handler):
                self.db = PostgreSQLDatabase(self.DATABASE_JSON, uid)
                self.db.json_to_db()  # миграция данных из JSON в БД
            else:
                self.db = JSONDatabase(self.DATABASE_JSON, uid)

            vk_user = VKUser(self.vk_group, uid)
            vk_user.data = self.db.get_user()  # получение данных о пользователе из местной БД

            # Если пользователя нет еще в БД, то получаем данные о нем из сети ВК
            if not vk_user.data:
                vk_user.get_user_data()
                self.db.update_user(vk_user)  # обновление данных о пользователе в местной БД

            self.select_command(event_data, vk_user)  # обработка входящего сообщения

    def select_command(self, data: MessageEventData, user_vk: VKUser) -> None:
        if self.LOG_MESSAGES:
            hues.info(f'<-- Получено сообщение id{data.message_id} от {user_vk.data.get("name", None)} > {data}')

        # Анализ принятого сообщения и вычисление команды
        cmd = self.chat.response_question(data)
        cmd.contact_id = data.contact_id

        if self.LOG_COMMANDS:
            hues.info(f'Анализ задачи в полученном сообщении: {cmd.command_description}')

        msg_obj = MessageAnswer(self.vk_searcher, self.vk_sender, user_vk,
                                cmd, self.keyboards, self.COUNT_RECORDS, self.YEAR_OFFSET,
                                self.ACCESS_TOKEN_USER, self.db)
        msg_obj.process_message()

    @progress_indicator('Бот запущен. Ждем сообщений...', 'Бот отключен.')
    def run(self):
        """Главная функция запуска бота - ожидание новых событий (сообщений)"""
        self.init_long_polling()

        while True:
            for event in self.long_poll.listen():
                self.check_event(event)


if __name__ == '__main__':

    try:

        # Инициализация бота
        bot = VKBot()

        # Запуск бота
        bot.run()
    except Exception as error:

        # Ошибка и выход
        fatal(error)
