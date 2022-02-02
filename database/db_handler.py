import peewee

from database.models import *
from vk_classes import VKUser


def get_user(user_id):
    """Поиск данных пользователя по user_id в таблице Users
    :user_id: идентификатор пользователя ВКонтакте
    """

    try:
        return Users.get(uid=str(user_id))

    except peewee.DoesNotExist:
        return None

    except Exception as Ex:
        hues.warn(f'Ошибка получения информации из БД о пользователе: {Ex}')
        return None


def add_user(adding_user: VKUser):
    """Добавление пользователя в таблицу Users с данными vk_user
    @type adding_user: данные пользователя в формате VKUser
    """

    try:
        # Подготовка данных
        insert_data = {key: value for key, value in adding_user.data.items() if getattr(Users, key, False)}
        insert_data['uid'] = str(insert_data.pop('id'))
        if insert_data.get('city', None):
            insert_data['city'] = insert_data['city']['title']
        # insert_data = {
            # 'user_id': adding_user.data['id'],
            # 'first_name': adding_user.data['first_name']
        # }
        #
        # if adding_user.data.get('city', None):
        #     insert_data['city'] = adding_user.data['city']['title']
        # if insert_data.get('city', None):
        #     insert_data['city'] = insert_data['city']['title']

        # Вставка данных
        # row = Users(**insert_data)
        # row = Users(city=insert_data['city'],
        #             first_name=insert_data['first_name'])
        # row = Users(city='dds',
        #             first_name='asdadaf')
        # row.save()
        # Users.create(user_id=insert_data['user_id'],
        #              first_name=insert_data['first_name'])
        Users.create(**insert_data)
        return True

    except peewee.InternalError:
        return None


# def set_up_roles(bot):
#     from cfg.settings import BLACK_LIST, FAVORITE_LIST
#
#     if WHITELIST:
#         bot.WHITELISTED = True
#
#     for u in WHITELIST:
#         await database.get_or_create(Role, user_id=u, role="whitelisted")
#
#     for u in BLACKLIST:
#         await database.get_or_create(Role, user_id=u, role="blacklisted")
#
#     check_white_list(bot)


# def check_white_list(bot):
#     if database.count(Role.select().where(Role.role == "whitelisted")) > 0:
#         bot.WHITELISTED = True
#
#     else:
#         bot.WHITELISTED = False
#