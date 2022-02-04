import hues  # для цветного вывода сообщений, + время
import re  # для нормализации строки
import json  # для работы json-данными


class MessageEventData:
    __slots__ = ('user_id', 'message_id', 'time', 'message_id', 'text', 'text_normalize', 'contact_id')

    def __init__(self, uid: int, msg_id: int, dt: int, body: str, contact_id: int):
        self.user_id = uid
        self.message_id = msg_id
        self.time = dt
        self.text = body
        self.text_normalize = get_normalize_set(self.text)
        self.contact_id = contact_id

    def __repr__(self):
        return self.text


def fatal(*args):
    """Печатает ошибку - args и выходит"""
    hues.error(f'Ошибка: {args}')
    exit()


def contact_id_from_dict(_dict: dict) -> int:
    result = _dict.get('payload', None)
    try:
        result = int(json.loads(result).get('type', None)) if result else None
    except Exception as Err:
        hues.warn(f'Ошибка получения contact_id: {Err}')
        result = None

    return result


def progress_indicator(in_title: str, out_title=''):
    """
    Декоратор - индикатор выполнения функции.
    Выводит надпись с помощью hues, сначала выполнения и после.
    :param in_title: сообщение INFO, перед началом выполнения;
    :param out_title: сообщение типа SUCCESS "OK", после выполнения;
    :return: сообщение типа ERROR - "Err", если произошла ошибка при выполнении.
    """
    def _decorator(_function):
        def _hues(*args, **kwargs):

            try:
                # Вывод сообщения перед выполнением
                if in_title:
                    hues.info(in_title)

                # Выполнение функции
                result = _function(*args, **kwargs)

                # Вывод сообщения после выполнением
                if out_title:
                    hues.success(out_title)

            except Exception as err:
                result = err
                # Вывод сообщения после выполнением
                hues.error(result)

            return result

        return _hues

    return _decorator


def get_normalize_set(string_: str) -> frozenset:
    """
    Нормализация строки к одному общему виду, разбиения на отдельные слова.
    :param string_: исходная строка;
    :return: множество из отдельных слов в нижнем регистре
    """
    new_string = string_.lower()
    set_of_words = frozenset(re.findall(r'[a-zA-Zа-яА-ЯЁё]+', new_string))
    return set_of_words


def read_json(file_name: str) -> dict:
    """
    Функция чтения json-файла.
    :param file_name: имя файла для чтения;
    :return: словарь, или ОШИБКУ в случае отсутствия файла
    """
    try:
        with open(file_name, encoding='utf-8') as f:
            return json.load(f)

    except Exception as err:
        print(f'ОШИБКА загрузки необходимых сведений: {err}')
        print(f'Проверьте наличие данных в файле - {file_name}.')
