import vk_api
from VK_settings import VKbot_token, user_token, Api_version
from vk_api.longpoll import VkLongPoll, VkEventType
from DB_engine import *
import requests

started_msg = f'''Привет, я - бот, а зовут меня Vkinder
                🔹Пора начинать поиск пары!

                ❓Как искать? Очень просто!👇
                ▶Введи пол(девушка или парень) *пробел* диапазон возраста (от 18 до 99 через тире) *пробел* город◀

                ПРИМЕР:
                девушка 18-20 Москва'''

def bot_send_msg(id, msg, attachment=None):
    vk.method('messages.send',
    {'user_id': id,
    'message': msg,
    'random_id': 0,
    'attachment': attachment})

def error_msg(id):
    bot_send_msg(id, started_msg)

def search_users(sex, lower_bound, upper_bound, city, user_id):
    all_persons = []
    vk = vk_api.VkApi(token=user_token)
    while len(all_persons) < 1:
        response = vk.method('users.search',
                            {'sex': sex,
                            'status': 1,
                            'age_from': lower_bound,
                            'age_to': upper_bound,
                            'has_photo': 1,
                            'count': 25,
                            'online': 1,
                            'hometown': city
                            })
        for element in response['items']:
            person = [
                element['first_name'],
                element['last_name'],
                'https://vk.com/id' + str(element['id']),
                element['id']
            ]
            get_photo(person)
            if(len(person[4]) > 0 and not check_pair(user_id, int(person[3]))): 
                all_persons.append(person)
    return all_persons

def get_photo(person):
    vk = vk_api.VkApi(token=user_token)
    users_photos = []
    try:
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
        for i in range(10):
            users_photos.append(
                [response['items'][i]['likes']['count'] + response['items'][i]['comments']['count'],
                    'photo' + str(response['items'][i]['owner_id']) + '_' + str(response['items'][i]['id'])])
        users_photos.sort(reverse=True, key=lambda x: x[0])
        person.append(users_photos[:3])
    except:
        person.append([])

def main_bot_loop():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW and this_event.to_me:
            return this_event.text.lower(), this_event.user_id

if __name__ == '__main__':
    try:
        vk = vk_api.VkApi(token=VKbot_token)
    except:
        print("Enable to connect to VKapi")
    try:    
        run_db()
    except:
        print("Enable to connect to DB")
    while True:
        longpoll = VkLongPoll(vk)
        try:
            text, user_id = main_bot_loop()
            text_splited = text.split()
            if not is_user_registered(user_id):
                user_registration(user_id)
            if text == 'начать':
                bot_send_msg(user_id, started_msg)
            elif len(text_splited) == 3:
                if text_splited[0].lower() == "девушка":
                    sex = 1
                elif text_splited[0].lower() == "парень":
                    sex = 2
                else:
                    error_msg(user_id)
                    continue
                city = text_splited[2].lower()
                age_splited = text_splited[1].split("-")
                try:
                    lower_bound = int(age_splited[0])
                    upper_bound = int(age_splited[1])
                    if lower_bound > upper_bound or lower_bound > 99:
                        bot_send_msg(user_id, "Ты что-то напутал с возрастом, попробуй еще раз, вот тебе инструкция:")
                        bot_send_msg(user_id, started_msg)
                        continue
                    if lower_bound < 18:
                        bot_send_msg(user_id, "Не младше 18, я поправил, не переживай :)")
                        lower_bound = 18
                    if upper_bound > 99:
                        bot_send_msg(user_id, "Не старше 99, я поправил О_о")
                        upper_bound = 99
                except:
                    bot_send_msg(user_id, "Ты что-то напутал с возрастом, попробуй еще раз, вот тебе инструкция:")
                    bot_send_msg(user_id, started_msg)
                    continue
                bot_send_msg(user_id, "Выполняю поиск подходящих анкет, подождите")
                for person in search_users(sex,lower_bound,upper_bound,city, user_id):
                    bot_send_msg(user_id,f'\n{person[0]}  {person[1]}  {person[2]}',)
                    bot_send_msg(user_id, f'фото:',attachment=','.join([person[4][0][1],person[4][1][1],person[4][2][1]]))
                    add_pair(user_id,person[3])
                    bot_send_msg(user_id, "Напиши \"далее\" для следующей анкеты")
                    text, user_id = main_bot_loop()
                    if text.lower() == "далее":
                        continue
                    else:
                        bot_send_msg(user_id, "Прости, я тебя не понял, воспользуйся инструкцией:")
                        error_msg(user_id)
                        continue
                bot_send_msg(user_id, "Введите запрос для продолжения")
            if text == "q" or text == "выход" or text == "quit":
                break
            else:
                bot_send_msg(user_id, "Прости, я тебя не понял, воспользуйся инструкцией:")
                error_msg(user_id)
        except requests.exceptions.ReadTimeout as timeout:
            continue
    disconnect_db()