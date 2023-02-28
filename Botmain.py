import vk_api
from VK_settings import VKbot_token, user_token, Api_version
from vk_api.longpoll import VkLongPoll, VkEventType
from DB_engine import *
import requests
import datetime

started_msg = f'''Привет, я - бот, а зовут меня Vkinder
                🔹Пора начинать поиск пары!'''

def bot_send_msg(id, msg, attachment=None):
    vk.method('messages.send',
    {'user_id': id,
    'message': msg,
    'random_id': 0,
    'attachment': attachment})

def error_msg(id):
    bot_send_msg(id, started_msg)

def search_users(sex, age, city, user_id):
    all_persons = []
    vk = vk_api.VkApi(token=user_token)
    while len(all_persons) < 1:
        response = vk.method('users.search',
                            {'sex': sex,
                            'status': 1,
                            'age_from': age,
                            'age_to': age,
                            'has_photo': 1,
                            'count': 25,
                            'online': 1,
                            'hometown': city
                            })
        try:
            response = response['items']
        except KeyError:
            print("Ошибка в ответе users.search")
            bot_send_msg(user_id, "Извините, произошла ошибка, повторите попытку позднее")
            return None
        for element in response:
            is_closed = vk.method('users.get',
                                {'user_ids': element['id'],
                                'fields': 'is_closed'
                                })
            try:
                is_closed = is_closed[0]['is_closed']
            except KeyError:
                print("Ошибка в ответе users.get")
                bot_send_msg(user_id, "Извините, произошла ошибка, повторите попытку позднее")
                return None
            if is_closed:
                continue
            person = [
                    element['first_name'],
                    element['last_name'],
                    'https://vk.com/id' + str(element['id']),
                    element['id']
                    ]
            if get_photo(person, user_id) is None:
                return None
            if(len(person[4]) > 0 and not check_pair(user_id, int(person[3]))): 
                all_persons.append(person)
    return all_persons

def get_photo(person, user_id):
    vk = vk_api.VkApi(token=user_token)
    users_photos = []
    response = vk.method('photos.get',
                            {
                                'access_token': user_token,
                                'v': Api_version,
                                'owner_id': person[3],
                                'album_id': 'profile',
                                'count': 10,
                                'extended': 1,
                                'photo_sizes': 1,
                            })
    try:
        response = response['items']
    except KeyError:
        print("Ошибка в ответе photos.get")
        bot_send_msg(user_id, "Извините, произошла ошибка, повторите попытку позднее")
        return None
    if len(response) > 3:
        for i in range(len(response)):
            users_photos.append(
                [response[i]['likes']['count'] + response[i]['comments']['count'],
                    'photo' + str(response[i]['owner_id']) + '_' + str(response[i]['id'])])
        users_photos.sort(reverse=True, key=lambda x: x[0])
        person.append(users_photos[:3])
        return 0
    else:
        print("Недостаточно фото для выдачи")
        person.append([])
        return 0

def main_bot_loop():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW and this_event.to_me:
            return this_event.text.lower(), this_event.user_id

def get_search_params(user_id):
    response = vk.method('users.get',
                    {'user_ids': user_id,
                     'fields': 'sex, bdate, city'
                    })
    try:
        response = response[0]
    except:
        print("Ошибка в ответе users.get")
        bot_send_msg(user_id, "Извините, произошла ошибка, повторите попытку позднее")
        return None
    if 'sex' in response:
        if response['sex'] == 1:
            sex = 2
        else:
            sex = 1
    else:
        while True:
            bot_send_msg(user_id, "У тебя в профиле не указан пол. Для поиска, напиши свой пол: \"девушка\" или \"парень\"")
            text, user_ids = main_bot_loop()
            if text == "девушка":
                sex = 2
                break
            elif text == "парень":
                sex = 1
                break
    if 'bdate' in response and len(response['bdate']) > 4:
        age = datetime.date.today().year - int(response['bdate'][-4:])
    else:
        while True:
            bot_send_msg(user_id, "У тебя в профиле не указан возраст. Для поиска, напиши свой год рождения, например, вот так: 1990")
            text, user_ids = main_bot_loop()
            if len(text) == 4 and str.isdigit(text):
                age = datetime.date.today().year - int(text)
                if age < 18:
                    bot_send_msg(user_id, "Нельзя пользоваться ботом, если тебе нет 18")
                elif age > 99:
                    bot_send_msg(user_id, "Во вселенной бота нельзя быть старше 99")
                else:
                    break
    if 'city' in response:
        city = response['city']['title']
    else:
        bot_send_msg(user_id, "У тебя в профиле не указан город. Для поиска, напиши свой город")
        city, user_ids = main_bot_loop()
    return sex,age,city

if __name__ == '__main__':
    vk = vk_api.VkApi(token=VKbot_token)
    run_db()
    while True:
        longpoll = VkLongPoll(vk)
        text, user_id = main_bot_loop()
        if not is_user_registered(user_id):
            user_registration(user_id)
        if text == 'начать':
            bot_send_msg(user_id, started_msg)
        search_params = get_search_params(user_id)
        if search_params is None:
            continue
        else:
            sex = search_params[0]
            age = search_params[1]
            city = search_params[2]
        bot_send_msg(user_id, "Выполняю поиск подходящих анкет, подождите")
        found_users = search_users(sex,age,city, user_id)
        if found_users is None:
            continue
        for person in found_users:
            bot_send_msg(user_id,f'\n{person[0]}  {person[1]}  {person[2]}',)
            bot_send_msg(user_id, f'фото:',attachment=','.join([person[4][0][1],person[4][1][1],person[4][2][1]]))
            add_pair(user_id,person[3])
            bot_send_msg(user_id, "Напиши \"далее\" для следующей анкеты")
            text, user_id = main_bot_loop()
            if text.lower() == "далее":
                continue
            else:
                bot_send_msg(user_id, "Прости, я тебя не понял. Напиши любое сообщение для продолжения")
                continue
        bot_send_msg(user_id, "Введите запрос для продолжения")
        if text == "q" or text == "выход" or text == "quit":
            break
    disconnect_db()