# Дополнительные свои функции
from chatter import *
from utils import *
from answer import MessageAnswer

# Дополнительные классы для работы ВК
from vk_classes import VKUser, VKSearcher, VKSender

# Для операции с файлами
import shutil
from os.path import isfile

# Для работы с API VK
import vk_api  # использование VK API для бота ВКонтакте
from vk_api.longpoll import VkLongPoll, VkEventType  # использование VkLongPoll и VkEventType

import hues  # для колоризированного вывода сообщений, + время

# Файл параметров запуска бота
FILE_SETTINGS = 'cfg/settings.py'

# Файл параметров запуска бота ПРИМЕР
FILE_SETTINGS_SAMPLE = 'cfg/settings.py.sample'


class VKBot:
    """Главный класс бота"""
    # Ипсользование slots для экономии памяти
    __slots__ = ['ACCESS_TOKEN_GROUP', 'ACCESS_TOKEN_USER', 'GROUP_ID', 'VK_GUDIE_FILE_NAME',
                 'LOG_COMMANDS', 'LOG_MESSAGES', 'LEXICON_FILE_NAME', 'ANSWER_FILE_NAME',
                 'COUNT_RECORDS',
                 'vk_group', 'vk_user', 'vk_session', 'vk_searcher', 'vk_sender', 'authorized',
                 'long_poll', 'users', 'chat', 'answers']

    @progress_indicator('Инициализация параметров бота...', 'Параметры инициализированы. Бот готов к запуску.')
    def __init__(self):
        self.init_settings()  # инициализация параметров бота
        self.additional_init()  # инициализация данных для чата
        self.vk_init()  # авторизация бота

    def init_settings(self):
        """Функция инициализации файла параметров запуска бота или его создания"""
        self.users = {}

        # Если у нас есть только FILE_SETTINGS_SAMPLE
        if isfile(FILE_SETTINGS_SAMPLE) and not isfile(FILE_SETTINGS):
            try:
                shutil.copy(FILE_SETTINGS_SAMPLE, FILE_SETTINGS)
            except Exception:
                fatal(f'Невозможно скопировать файлы ("{FILE_SETTINGS_SAMPLE}" -> "{FILE_SETTINGS_SAMPLE}") '
                      f'в текущей папке, проверьте Ваши права на неё!')

        # Если у нас уже есть FILE_SETTINGS
        elif isfile(FILE_SETTINGS):
            from cfg import settings
            try:
                self.ACCESS_TOKEN_GROUP = settings.ACCESS_TOKEN_GROUP
                self.ACCESS_TOKEN_USER = settings.ACCESS_TOKEN_USER
                self.GROUP_ID = settings.GROUP_ID
                self.LEXICON_FILE_NAME = settings.LEXICON_FILE_NAME
                self.ANSWER_FILE_NAME = settings.ANSWER_FILE_NAME
                self.VK_GUDIE_FILE_NAME = settings.VK_GUDIE_FILE_NAME

                self.LOG_MESSAGES = settings.LOG_MESSAGES
                self.LOG_COMMANDS = settings.LOG_COMMANDS

                self.COUNT_RECORDS = settings.COUNT_RECORDS

                if not self.ACCESS_TOKEN_GROUP or not self.ACCESS_TOKEN_USER:
                    fatal(f'Проверьте, что у есть "ACCESS_TOKEN_GROUP" и "ACCESS_TOKEN_USER" в файле '
                          f'{FILE_SETTINGS}!\nБез них БОТ работать НЕ СМОЖЕТ!.')

            except (ValueError, AttributeError, NameError):
                fatal(f'Проверьте содержимое файла - "{FILE_SETTINGS}", возможно Вы удалили что-то нужное!')

        # Если не нашли ни FILE_SETTINGS, ни FILE_SETTINGS_SAMPLE
        else:
            fatal(f'Файлы - "{FILE_SETTINGS}" и "{FILE_SETTINGS_SAMPLE}" не найдены, возможно вы их удалили?')

    def additional_init(self):
        """Функция инициализации дополнительных данных для чата"""
        self.chat = Chatter(self.LEXICON_FILE_NAME)  # инициализация лексикона
        self.answers = Answers(self.ANSWER_FILE_NAME)  # инициализация ответчика на запросы

    def vk_init(self):
        """Функция авторизации пользователя и сообщества API ВКонтакте"""
        self.vk_user = self.do_auth(self.ACCESS_TOKEN_USER)
        self.vk_group = self.do_auth(self.ACCESS_TOKEN_GROUP)

        self.authorized = self.vk_group and self.vk_user
        if not self.authorized:
            fatal('Бот не авторизовался, запуск невозможен!')

        self.vk_searcher = VKSearcher(self.vk_user, self.VK_GUDIE_FILE_NAME)
        self.vk_sender = VKSender(self.vk_group, self.LOG_MESSAGES)

    def do_auth(self, token):
        """Авторизация vk_api"""
        try:
            self.vk_session = vk_api.VkApi(token=token)
            return self.vk_session.get_api()
        except Exception as Err:
            fatal(f'ОШИБКА авторизации: {Err}')
            return None

    def init_long_polling(self):
        """Функция для инициализации Long Polling"""
        self.long_poll = VkLongPoll(self.vk_session)

        if not self.long_poll:
            fatal('Не удалось получить значения Long Poll сервера!')

    def _update_user(self, user: VKUser):
        uid = user.data.get('user_id', None)
        if uid:
            self.users[uid] = user.data

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

            # Создание экзмепляра сообщения
            event_data = MessageEventData(uid, msg_id, dt, msg)

            # Создание экземпляра пользователя + чтение всех данных о нем из ВК
            if uid not in self.users:
                self.users[uid] = VKUser(self.vk_group, uid)

            # Обработка входящего сообщения
            self.select_command(event_data, self.users[uid])

    def select_command(self, data: MessageEventData, user: VKUser) -> None:
        if self.LOG_MESSAGES:
            hues.info(f'<-- Получено сообщение id{data.message_id} от {user.data.get("name", None)} > {data}')

        # Анализ принятого сообщения и вычисление команды
        cmd = self.chat.response_question(data)

        if self.LOG_COMMANDS:
            hues.info(f'Анализ задачи в полученном сообщении: {cmd.command_description}')

        msg_obj = MessageAnswer(self.vk_searcher, self.vk_sender, user,
                                cmd, self.answers, self.COUNT_RECORDS,
                                self.ACCESS_TOKEN_USER)
        msg_obj.process_message()

    @progress_indicator('Бот запущен. Ждем сообщений...', 'Бот оключен.')
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
