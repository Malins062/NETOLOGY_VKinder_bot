from utils import *  # свои дополнительные функции
import random  # для генерации случайных ответов
from enum import Enum


class Command:
    __slots__ = ('answer', 'command', 'command_description')

    def __init__(self, answer=None, command=-1, commad_description=None):
        self.answer = answer
        self.command = command
        self.command_description = commad_description

    def __repr__(self):
        return self.command_description


class Chatter:
    """Лексикон бота и обработка сообщений"""
    __slots__ = ('lexicon', 'questions')

    def __init__(self, file_name):
        try:
            # Загрузка лексикона
            self.lexicon = read_json(file_name)

            # Создание общего списка словаря запросов и разибение по темам
            self.questions = self._create_vocabulary()
        except Exception as Err:
            fatal(f'Ошибка загрузки лексикона бота: {Err}')

    def _create_vocabulary(self) -> dict:
        """
        Создание общего списка вопросов и тем к которому относится вопрос
        """
        questions = {}

        for intent, intent_data in self.lexicon["intents"].items():
            for example in intent_data["examples"]:
                keywords = get_normalize_set(example)
                questions[frozenset(keywords)] = intent

        return questions

    def response_question(self, question: MessageEventData) -> Command:
        """
        Поиск ответа пользователю на его запрос и выдача команды на поиск друзей.
        :param question: сообщение пользователя;
        :return: ответ для пользователя, команда для поиска друзей
        """
        # Определение намерения пользователя, использование заготовленного ответа
        intent = self._get_intent(question.text_normalize)

        # Бот нашел тему сообщения - отправляется ответ по теме
        if intent:
            return self._get_response_by_intent(intent)

        # Бот не может подобрать ответ - отправляется ответ-заглушка
        return self._get_failure_phrase()

    def _get_intent(self, request: frozenset):
        """
        Получение вероятной темы сообщения пользователя, которая есть в лексиконе.
        :return: тема сообщения
        """
        for value in self.questions:
            if value == request:
                return self.questions[value]
        else:
            return None

    def _get_response_by_intent(self, intent: str) -> Command:
        """
        Получение случайного ответа на намерение пользователя, а также команда поиска друзей если он определена.
        :param intent: намерение (тема сообщения);
        :return: случайный ответ из прописанных для тем сообщения + команда поиска если она определена для ответа
        """
        cmd = Command()
        # Ответ по теме
        cmd.answer = random.choice(self.lexicon['intents'][intent]['responses'])
        # Номер команды
        cmd.command = self.lexicon['intents'][intent].get('command', 99)
        # Описание команды
        cmd.command_description = self.lexicon['intents'][intent].get('command_description', 'КОМАНДА НЕ ЗАДАНА')

        return cmd

    def _get_failure_phrase(self) -> Command:
        """
        Если бот не может найти тему запроса пользователя, то будет отправлена случайная фраза
        из списка failure_phrases лексикона бота.
        :return: случайная фраза в случае провала подбора ответа ботом
        """
        cmd = Command()
        # Случайный ответ на не распознанную тему
        cmd.answer = random.choice(self.lexicon['failure_phrases']['responses'])
        # Номер команды
        cmd.command = self.lexicon['failure_phrases'].get('command', 99)
        # Описание команды
        cmd.command_description = self.lexicon['failure_phrases'].get('command_description', None)

        return cmd


class Answers:
    __slots__ = 'answers'

    def __init__(self, file_name):
        try:
            # Загрузка параметров ответа на команды
            self.answers = read_json(file_name)

            for key, value in self.answers.items():
                if value.get('keyboard', None):
                    value['keyboard'] = json.dumps(value['keyboard'], ensure_ascii=True)

        except Exception as Err:
            fatal(f'Ошибка загрузки параметров ответов бота: {Err}')
