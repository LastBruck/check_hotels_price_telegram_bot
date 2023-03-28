import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from loguru import logger

from src.methods import get_price, set_history, get_history, get_best_deal
from src.hotel_requests import request_location

logger.add('debug.log', format='{time} {level} {message}', level='DEBUG',
           rotation='30 KB', compression='zip')
load_dotenv()
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'), parse_mode='HTML')
user_dict = {}


class UserSet:
    def __init__(self):
        self.command = None
        self.date = None
        self.city_id = None
        self.city = None
        self.distance_filter = None
        self.number_hotels = None
        self.photo = False
        self.num_photo = None
        self.sort_method = None
        self.method_filter = None
        self.checkIn_day = None
        self.checkIn_month = None
        self.checkIn_year = None
        self.checkOut_day = None
        self.checkOut_month = None
        self.checkOut_year = None
        self.date_in = None


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=0))
def date_in_calendar(call):
    """
    Callback запроса даты въезда через календарь.
    """
    chat_id = call.message.chat.id
    user = user_dict[chat_id]

    result, key, step = DetailedTelegramCalendar(calendar_id=0,
                                                 min_date=date.today(),
                                                 locale='ru').process(call.data)
    logger.info('{}: {}'.format(chat_id, result))
    if not result and key:
        bot.edit_message_text('Выберите дату въезда',
                              chat_id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        user.date_in = result
        user.checkIn_day = result.day
        user.checkIn_month = result.month
        user.checkIn_year = result.year
        bot.edit_message_text('Дата въезда: {}.{}.{}'.format(result.day, result.month, result.year),
                              chat_id,
                              call.message.message_id)
        date_out(call.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def date_out_calendar(call):
    """
    Callback запроса даты выезда через календарь.
    """
    chat_id = call.message.chat.id
    user = user_dict[chat_id]

    result, key, step = DetailedTelegramCalendar(calendar_id=1,
                                                 min_date=user.date_in +
                                                 timedelta(days=1),
                                                 locale='ru').process(call.data)
    logger.info('{}: {}'.format(chat_id, result))
    if not result and key:
        bot.edit_message_text('Выберите дату выезда',
                              chat_id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        user.checkOut_day = result.day
        user.checkOut_month = result.month
        user.checkOut_year = result.year
        bot.edit_message_text('Дата выезда: {}.{}.{}'.format(result.day, result.month, result.year),
                              chat_id,
                              call.message.message_id)
        query_number_hotel(call.message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Callback запросов: нужно ли указывать даты въезда и выезда, нужно ли загружать фотографии.
    """
    chat_id = call.message.chat.id
    user = user_dict[chat_id]
    logger.info('{}: {}'.format(chat_id, call.data))
    if call.data == 'dt_yes':
        date_in(call.message)
    elif call.data == 'dt_no':
        dt = datetime.now()
        user.checkIn_day = dt.day
        user.checkIn_month = dt.month
        user.checkIn_year = dt.year
        user.checkOut_day = dt.day
        user.checkOut_month = dt.month
        user.checkOut_year = dt.year
        query_number_hotel(call.message)
    elif call.data == 'ph_yes':
        set_query_photo(call.message)
    elif call.data == 'ph_no':
        user.photo = False
        user.num_photo = 0
        get_price_hotels(call.message)


@bot.message_handler(commands=['start'])
def command_start(message):
    """
    Функция СтартБОТА, вывод сообщения с приветствием и командами.
    """
    mess = 'Привет, <b>{}</b>\n' \
           'Я бот для поиска билетов в отели\n' \
           'Выбери команду:\n\n' \
           '<b>/lowprice</b> — вывод самых дешёвых отелей в городе.\n' \
           '<b>/highprice</b> — вывод самых дорогих отелей в городе.\n' \
           '<b>/bestdeal</b> — вывод отелей, наиболее подходящих по цене и расположению от центра.\n' \
           '<b>/history</b> — вывод истории поиска отелей.\n' \
           '<b>/help</b> — помощь по командам бота'.format(message.from_user.first_name)
    bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.message_handler(commands=['help'])
def command_help(message):
    """
    Функция команды: /help — помощь по командам бота.
    """
    mess = 'Выбери команду:\n\n' \
           '<b>/lowprice</b> — вывод самых дешёвых отелей в городе.\n' \
           '<b>/highprice</b> — вывод самых дорогих отелей в городе.\n' \
           '<b>/bestdeal</b> — вывод отелей, наиболее подходящих по цене и расположению от центра.\n' \
           '<b>/history</b> — вывод истории поиска отелей.\n' \
           '<b>/help</b> — помощь по командам бота'.format(message.from_user.first_name)
    bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.message_handler(commands=['history'])
def get_history_commands(message):
    """
    Функция команды: /history — вывод истории поиска отелей.
    """
    if message.chat.type == 'private':
        chat_id = message.chat.id
        user = UserSet()
        user.command = '/history'
        user_dict[chat_id] = user
        logger.info('{}: {}'.format(chat_id, user.command))
        response = get_history(name_table=chat_id)
        if len(response) > 0 and 'error_db' not in response[0].keys():
            for res in response:
                date_res, time_res = res['date'].split()
                date_lst = date_res.split('-')
                time_lst = time_res.split(':')
                text = '<b>Дата:</b> {}.{}.{} {}:{}\t\t<b>Команда:</b> {}'.format(
                    date_lst[2], date_lst[1], date_lst[0], time_lst[0], time_lst[1], res['command']
                )
                bot.send_message(chat_id,
                                 text,
                                 parse_mode='html')
                send_price_hotels(message, list_hotels=res['history_responses'])
        else:
            bot.send_message(chat_id,
                             'Упс! Истории пока нету... Видимо вы еще ничего ранее не находили в нашем поиске...',
                             parse_mode='html')
        command_help(message)


@bot.message_handler(commands=['lowprice', 'highprice'])
def get_lowprice_highprice_commands(message):
    """
    Функция команд: /lowprice — вывод самых дешёвых отелей в городе,
                    /highprice — вывод самых дорогих отелей в городе.
    """
    if message.chat.type == 'private':
        chat_id = message.chat.id
        user = UserSet()
        dt = datetime.now()
        user.date = dt
        if 'lowprice' in message.text:
            user.command = '/lowprice'
            user.sort_method = 'PRICE_LOW_TO_HIGH'
        elif 'highprice' in message.text:
            user.command = '/highprice'
            user.sort_method = 'PRICE_HIGH_TO_LOW'
        user.method_filter = {'availableFilter': 'SHOW_AVAILABLE_ONLY'}
        user_dict[chat_id] = user
        logger.info('{}: {}'.format(chat_id, user.command))
        bot.send_message(chat_id,
                         'Введите название города, где будет проводиться поиск',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_city)


@bot.message_handler(commands=['bestdeal'])
def get_bestdeal_commands(message):
    """
    Функция команды: /bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра.
    """
    if message.chat.type == 'private':
        chat_id = message.chat.id
        user = UserSet()
        dt = datetime.now()
        user.date = dt
        user.command = '/bestdeal'
        user.method_filter = {'price': {
            'max': None,
            'min': None
        }}
        user.distance_filter = {
            'distance': {
                'max': None,
                'min': None
            }
        }
        user.sort_method = 'PRICE_LOW_TO_HIGH'
        user_dict[chat_id] = user
        logger.info('{}: {}'.format(chat_id, user.command))
        bot.send_message(chat_id,
                         'Введите название города, где будет проводиться поиск',
                         parse_mode='html')
    bot.register_next_step_handler(message, set_city)


def set_city(message):
    """
    Функция проверяет наличие названия города в базе поиска.
    При положительном ответе, сохраняет название_города, ID_города и выводит Inline кнопки с вопросом:
    "Нужно ввести даты въезда и выезда из отеля?"
    При ошибке или отрицательном ответе выведет сообщение в БОТ: "К сожалению такого города нет в базе поиска..."
    """
    chat_id = message.chat.id
    city = message.text
    logger.info('{}: {}'.format(chat_id, city))
    try:
        res_location = request_location(city=city)
        if not res_location:
            bot.send_message(chat_id,
                             'К сожалению такого города нет в базе поиска...',
                             parse_mode='html')
            command_help(message)
        else:
            user = user_dict[chat_id]
            user.city_id = res_location[0]['gaiaId']
            user.city = city
            markup = InlineKeyboardMarkup()
            markup.row_width = 2
            markup.add(InlineKeyboardButton('Да', callback_data='dt_yes'),
                       InlineKeyboardButton('Нет', callback_data='dt_no'))
            bot.send_message(chat_id,
                             'Нужно ввести даты въезда и выезда из отеля?',
                             reply_markup=markup)
    except Exception as city_ex:
        logger.error('Ошибка запроса города {}: {}'.format(city, city_ex))
        bot.send_message(chat_id,
                         'К сожалению такого города нет в базе поиска...',
                         parse_mode='html')
        command_help(message)


def date_in(message):
    """
    Функция ввода даты въезда в отель.
    """
    calendar, step = DetailedTelegramCalendar(calendar_id=0,
                                              min_date=date.today(),
                                              locale='ru').build()
    bot.send_message(message.chat.id,
                     'Выберите дату въезда',
                     reply_markup=calendar)


def date_out(message):
    """
    Функция ввода даты выезда в отель.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    calendar, step = DetailedTelegramCalendar(calendar_id=1,
                                              min_date=user.date_in +
                                              timedelta(days=1),
                                              locale='ru').build()
    bot.send_message(message.chat.id,
                     'Выберите дату выезда',
                     reply_markup=calendar)


def query_number_hotel(message):
    """
    Функция запроса, в зависимости от начальной команды:
        если начальная команда была НЕ '/bestdeal', то делается запрос на количество отелей в результат поиска.
        если начальная команда была '/bestdeal', то делается запрос на максимальную цену.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if user.command != '/bestdeal':
        bot.send_message(chat_id,
                         'Введите количество отелей, которые необходимо вывести в результате',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_number_hotels)
    else:
        bot.send_message(chat_id,
                         'Введите максимальную цену в $:',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_max_price)


def set_max_price(message):
    """
    Функция ввода максимальной цены.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    num = message.text
    logger.info('{}: {}'.format(chat_id, num))
    if num.translate({ord('.'): None}).isdigit():
        user.method_filter['price']['max'] = float(num)
        bot.send_message(chat_id,
                         'Введите минимальную цену в $:',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_min_price)
    else:
        bot.send_message(chat_id,
                         'Вводимая цена должна быть <b>числом</b>!',
                         parse_mode='html')
        message.text = user.city
        set_city(message)


def set_min_price(message):
    """
    Функция ввода минимальной цены.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    num = message.text
    logger.info('{}: {}'.format(chat_id, num))
    if num.translate({ord('.'): None}).isdigit():
        user.method_filter['price']['min'] = float(num)
        bot.send_message(chat_id,
                         'Введите максимальное расстояние от центра города в км:',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_max_distance)
    else:
        bot.send_message(chat_id,
                         'Вводимая цена должна быть <b>числом</b>!',
                         parse_mode='html')
        message.text = str(user.method_filter['price']['max'])
        set_max_price(message)


def set_max_distance(message):
    """
    Функция ввода максимального расстояния (в км) от центра города.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    num = message.text
    logger.info('{}: {}'.format(chat_id, num))
    if num.translate({ord('.'): None}).isdigit():
        user.distance_filter['distance']['max'] = float(num)
        bot.send_message(chat_id,
                         'Введите минимальное расстояние от центра города в км:',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_min_distance)
    else:
        bot.send_message(chat_id,
                         'Вводимое расстояние должно быть <b>числом</b>!',
                         parse_mode='html')
        message.text = str(user.method_filter['price']['min'])
        set_min_price(message)


def set_min_distance(message):
    """
    Функция ввода минимального расстояния (в км) от центра города.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    num = message.text
    logger.info('{}: {}'.format(chat_id, num))
    if num.translate({ord('.'): None}).isdigit():
        user.distance_filter['distance']['min'] = float(num)
        bot.send_message(chat_id,
                         'Введите количество отелей, которые необходимо вывести в результате',
                         parse_mode='html')
        bot.register_next_step_handler(message, set_number_hotels)
    else:
        bot.send_message(chat_id,
                         'Вводимое расстояние должно быть <b>числом</b>!',
                         parse_mode='html')
        message.text = str(user.distance_filter['distance']['max'])
        set_max_distance(message)


def set_number_hotels(message):
    """
    Функция ввода количества отелей, которые необходимо вывести в результате.
    Так же здесь появляются Inline кнопки с CallBack запросом, нужно ли загружать фото отеля.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    num = message.text
    logger.info('{}: {}'.format(chat_id, num))
    if num.isdigit():
        user.number_hotels = int(num)
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(InlineKeyboardButton('Да', callback_data='ph_yes'),
                   InlineKeyboardButton('Нет', callback_data='ph_no'))
        bot.send_message(chat_id,
                         'Нужно загрузить фото отеля?',
                         reply_markup=markup)
    else:
        if user.command == '/bestdeal':
            bot.send_message(chat_id,
                             'Вводимое количество должно быть <b>числом</b>!',
                             parse_mode='html')
            message.text = str(user.distance_filter['distance']['min'])
            set_min_distance(message)
        else:
            bot.send_message(chat_id,
                             'Вводимое количество должно быть <b>целым числом</b>!',
                             parse_mode='html')
            message.text = user.city
            set_city(message)


def set_query_photo(message):
    """
    Функция запроса количества фото.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    user.photo = True
    bot.send_message(chat_id,
                     'Введите количество необходимых фотографий: ',
                     parse_mode='html')
    bot.register_next_step_handler(message, set_number_photo)


def set_number_photo(message):
    """
    Функция ввода количества фото.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    num = message.text
    logger.info('{}: {}'.format(chat_id, num))
    if num.isdigit():
        user.num_photo = int(num)
        get_price_hotels(message)
    else:
        bot.send_message(message.chat.id,
                         'Вводимое количество должно быть числом.',
                         parse_mode='html')
        set_query_photo(message)
    command_help(message)


def get_price_hotels(message):
    """
    Функция запроса ответа от API HOTELS.COM
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    send_message_searching(message)
    city_id = user.city_id
    city = user.city
    distance_filter = user.distance_filter
    command = user.command
    number_hotels = user.number_hotels
    photo = user.photo
    num_photo = user.num_photo
    sort_method = user.sort_method
    method_filter = user.method_filter
    checkIn_day = user.checkIn_day
    checkIn_month = user.checkIn_month
    checkIn_year = user.checkIn_year
    checkOut_day = user.checkOut_day
    checkOut_month = user.checkOut_month
    checkOut_year = user.checkOut_year
    if command == '/bestdeal':
        list_hotels = get_best_deal(cityID=city_id,
                                    city_name=city,
                                    num_hotels=number_hotels,
                                    photo_get=photo,
                                    num_photo=num_photo,
                                    sort_method=sort_method,
                                    method_filter=method_filter,
                                    distance_filter=distance_filter,
                                    checkIn_day=checkIn_day,
                                    checkIn_month=checkIn_month,
                                    checkIn_year=checkIn_year,
                                    checkOut_day=checkOut_day,
                                    checkOut_month=checkOut_month,
                                    checkOut_year=checkOut_year
                                    )
    else:
        list_hotels = get_price(cityID=city_id,
                                city_name=city,
                                num_hotels=number_hotels,
                                photo_get=photo,
                                num_photo=num_photo,
                                sort_method=sort_method,
                                method_filter=method_filter,
                                checkIn_day=checkIn_day,
                                checkIn_month=checkIn_month,
                                checkIn_year=checkIn_year,
                                checkOut_day=checkOut_day,
                                checkOut_month=checkOut_month,
                                checkOut_year=checkOut_year
                                )

    send_price_hotels(message, list_hotels=list_hotels)


def send_price_hotels(message, list_hotels: list = None):
    """
    Функция отправки сообщения в чат бота с полученными данными.
    """
    chat_id = message.chat.id
    user = user_dict[chat_id]
    command = user.command
    if len(list_hotels) > 0:
        if ('error_city' or 'error_hotels' or 'error_hotel') not in list_hotels[0].keys():
            for hotel in list_hotels:
                if 'error_hotel' not in hotel.keys():
                    text = '<b>Название отеля:</b> {}\n<b>Адрес:</b> {}\n' \
                           '<b>Как далеко расположен от центра:</b> {} км\n<b>Цена:</b> {} $\n' \
                           'https://www.hotels.com/h{}.Hotel-Information'.format(
                            hotel['name_hotel'], hotel['address'],
                            hotel['distance_to_centre'], round(hotel['price'], 2), hotel['id_hotel'])
                    bot.send_message(chat_id,
                                     text,
                                     parse_mode='html')
                    if 'photos' in hotel.keys():
                        send_group_photo(message, hotel['photos'])
            if command != '/history':
                date_command = user.date
                set_history(name_table=chat_id, command=command, date=date_command, data_hotels=list_hotels)

        elif 'error_city' in list_hotels[0].keys():
            bot.send_message(chat_id,
                             'К сожалению такого города нет в базе поиска...',
                             parse_mode='html')
        elif 'error_hotels' in list_hotels[0].keys():
            bot.send_message(chat_id,
                             'К сожалению в этом городе нет подходящих отелей...',
                             parse_mode='html')
    elif len(list_hotels) == 0:
        bot.send_message(chat_id,
                         'К сожалению в этом городе нет подходящих отелей...',
                         parse_mode='html')


def send_message_searching(message):
    """
    Функция отправки сообщения 'Идёт поиск...' в чат бота.
    """
    bot.send_message(message.chat.id,
                     'Идёт поиск...',
                     parse_mode='html')


@bot.message_handler(content_types=['photo'])
def send_group_photo(message, image_list):
    """
    Функция отправки сгруппированных фотографий.
    """
    medias = []
    for image_url in image_list:
        medias.append(InputMediaPhoto(image_url))
    bot.send_media_group(message.chat.id, medias)


if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except Exception as ex:
        logger.error('Общая ошибка: {}'.format(str(ex)))
