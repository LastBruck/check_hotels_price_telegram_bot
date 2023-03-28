from peewee import *
from loguru import logger

from src.hotel_requests import request_hotels, request_details_hotel


def get_price(
            cityID: str = None,
            city_name: str = None,
            num_hotels: int = None,
            photo_get: bool = False,
            num_photo: int = None,
            sort_method: str = None,
            method_filter: dict = None,
            checkIn_day: int = None,
            checkIn_month: int = None,
            checkIn_year: int = None,
            checkOut_day: int = None,
            checkOut_month: int = None,
            checkOut_year: int = None
            ):
    """
    Функция запроса данных от API.

    :param cityID: str - ID города
    :param city_name: str - название города
    :param num_hotels: int - количество отелей
    :param photo_get: bool - загружать фото или нет False/True
    :param num_photo: int - кол-во фото
    :param sort_method: str - метод сортировки
    :param method_filter: dict - метод фильтрации запроса
    :param checkIn_day: int - день въезда в отель
    :param checkIn_month: int - месяц въезда в отель
    :param checkIn_year: int - год въезда в отель
    :param checkOut_day: int - день выезда из отель
    :param checkOut_month: int - месяц выезда из отель
    :param checkOut_year: int - год выезда из отель
    :return: list
    """
    result_price = []
    try:
        hotels_list = request_hotels(city_id=cityID,
                                     number_of_hotels=num_hotels,
                                     sort_method=sort_method,
                                     filter_data=method_filter,
                                     checkIn_day=checkIn_day,
                                     checkIn_month=checkIn_month,
                                     checkIn_year=checkIn_year,
                                     checkOut_day=checkOut_day,
                                     checkOut_month=checkOut_month,
                                     checkOut_year=checkOut_year
                                     )
        if not hotels_list:
            logger.error('error_hotels: Hotels in {city_name}: "NOT FOUND"'.format(city_name=city_name))
            return [{'error_hotels': 'NOT FOUND'}]
        for i_hotel in range(len(hotels_list)):
            try:
                details_hotel = request_details_hotel(id_hotel=hotels_list[i_hotel]['id'])
                hotel_dict = {
                    'id_hotel': hotels_list[i_hotel]['id'],
                    'name_hotel': hotels_list[i_hotel]['name'],
                    'address': details_hotel['data']['propertyInfo']['summary']['location']['address']['addressLine'],
                    'distance_to_centre': hotels_list[i_hotel]['destinationInfo']['distanceFromDestination']['value'],
                    'price': hotels_list[i_hotel]['price']['lead']['amount'],
                    }
                if photo_get:
                    hotel_dict['photos'] = []
                    if num_photo > len(details_hotel['data']['propertyInfo']['propertyGallery']['images']):
                        num_photo = len(details_hotel['data']['propertyInfo']['propertyGallery']['images'])
                    for i_num in range(num_photo):
                        hotel_dict['photos'].append(
                            details_hotel['data']['propertyInfo']['propertyGallery']['images'][i_num]['image']['url']
                        )
                result_price.append(hotel_dict)
                if sort_method == 'PRICE_LOW_TO_HIGH':
                    result_price.sort(key=lambda x: x['price'])
                elif sort_method == 'PRICE_HIGH_TO_LOW':
                    result_price.sort(key=lambda x: x['price'], reverse=True)
            except Exception as ex_hotel:
                logger.error('error_hotel: Hotels {id_hotel} in {city_name}: {ex}'.format(
                    id_hotel=hotels_list[i_hotel]['id'], city_name=city_name, ex=str(ex_hotel)))
                result_price.append({'error_hotel': '{ex}'.format(city_name=city_name, ex=str(ex_hotel))})
    except Exception as ex_hotels:
        logger.error('error_hotels: Hotels in {city_name}: {ex}'.format(city_name=city_name, ex=str(ex_hotels)))
        result_price.append({'error_hotels': '{ex}'.format(city_name=city_name, ex=str(ex_hotels))})
    return result_price


def get_best_deal(
            cityID: str = None,
            city_name: str = None,
            num_hotels: int = None,
            photo_get: bool = False,
            num_photo: int = None,
            sort_method: str = None,
            method_filter: dict = None,
            distance_filter: dict = None,
            checkIn_day: int = None,
            checkIn_month: int = None,
            checkIn_year: int = None,
            checkOut_day: int = None,
            checkOut_month: int = None,
            checkOut_year: int = None
            ):
    """
    Функция запроса данных от API.

    :param cityID: str - ID города
    :param city_name: str - название города
    :param num_hotels: int - количество отелей
    :param photo_get: bool - загружать фото или нет False/True
    :param num_photo: int - кол-во фото
    :param sort_method: str - метод сортировки
    :param method_filter: dict - метод фильтрации запроса
    :param distance_filter:  dict - фильтр расстояния от центра города
    :param checkIn_day: int - день въезда в отель
    :param checkIn_month: int - месяц въезда в отель
    :param checkIn_year: int - год въезда в отель
    :param checkOut_day: int - день выезда из отель
    :param checkOut_month: int - месяц выезда из отель
    :param checkOut_year: int - год выезда из отель
    :return: list
    """
    result_best_deal = []
    try:
        hotels_list = request_hotels(city_id=cityID,
                                     number_of_hotels=50,
                                     sort_method=sort_method,
                                     filter_data=method_filter,
                                     checkIn_day=checkIn_day,
                                     checkIn_month=checkIn_month,
                                     checkIn_year=checkIn_year,
                                     checkOut_day=checkOut_day,
                                     checkOut_month=checkOut_month,
                                     checkOut_year=checkOut_year
                                     )
        if not hotels_list:
            logger.error('error_hotels: Hotels in {city_name}: "NOT FOUND"'.format(city_name=city_name))
            return [{'error_hotels': 'NOT FOUND'}]
        hotels_list.sort(key=lambda x: x['price']['lead']['amount'])
        hotels_list.sort(key=lambda x: x['destinationInfo']['distanceFromDestination']['value'])
        for i_hotel in range(len(hotels_list)):
            if len(result_best_deal) < num_hotels:
                if distance_filter['distance']['min'] <= hotels_list[i_hotel]['destinationInfo']['distanceFromDestination']['value'] <= distance_filter['distance']['max']:
                    try:
                        details_hotel = request_details_hotel(id_hotel=hotels_list[i_hotel]['id'])
                        hotel_dict = {
                            'id_hotel': hotels_list[i_hotel]['id'],
                            'name_hotel': hotels_list[i_hotel]['name'],
                            'address': details_hotel['data']['propertyInfo']['summary']['location']['address'][
                                'addressLine'],
                            'distance_to_centre': hotels_list[i_hotel]['destinationInfo']['distanceFromDestination'][
                                'value'],
                            'price': hotels_list[i_hotel]['price']['lead']['amount'],
                        }
                        if photo_get:
                            hotel_dict['photos'] = []
                            if num_photo > len(details_hotel['data']['propertyInfo']['propertyGallery']['images']):
                                num_photo = len(details_hotel['data']['propertyInfo']['propertyGallery']['images'])
                            for i_num in range(num_photo):
                                hotel_dict['photos'].append(
                                    details_hotel['data']['propertyInfo']['propertyGallery']['images'][i_num]['image'][
                                        'url']
                                )

                        result_best_deal.append(hotel_dict)
                        result_best_deal.sort(key=lambda x: x['price'])
                    except Exception as ex_hotel:
                        logger.error('error_hotel: Hotels {id_hotel} in {city_name}: {ex}'.format(
                            id_hotel=hotels_list[i_hotel]['id'], city_name=city_name, ex=str(ex_hotel)))
                        result_best_deal.append({'error_hotel': '{ex}'.format(ex=str(ex_hotel))})
    except Exception as ex_hotels:
        logger.error('error_hotels: Hotels in {city_name}: {ex}'.format(city_name=city_name, ex=str(ex_hotels)))
        result_best_deal.append({'error_hotels': '{ex}'.format(ex=str(ex_hotels))})
    return result_best_deal


def set_history(name_table: str = None, command: str = None, date: int = None, data_hotels: list = None):
    """
    Функция записи полученных положительных результатов в БД.

    :param name_table: str - ID чата
    :param command: str - начальная команда чата
    :param date: int - дата выбора команды
    :param data_hotels: list - список полученных результатов.
    """
    try:
        db = SqliteDatabase('db_history.db')

        class History(Model):
            id = PrimaryKeyField(null=False)
            command = CharField()
            date = CharField()

            class Meta:
                database = db
                db_table = 'history_{name_table}'.format(name_table=name_table)

        class HistoryResponse(Model):
            owner = ForeignKeyField(History, related_name='responses')
            id_hotel = CharField()
            name_hotel = CharField()
            address = CharField()
            distance_to_centre = CharField()
            price = CharField()
            photos = CharField(null=True)

            class Meta:
                database = db
                db_table = 'history_response{name_table}'.format(name_table=name_table)

        History.create_table()
        HistoryResponse.create_table()
        history_comm = History.create(command=command, date=date)
        for data in data_hotels:
            if 'photos' not in data.keys():
                HistoryResponse.create(owner=history_comm, id_hotel=data['id_hotel'],
                                       name_hotel=data['name_hotel'], address=data['address'],
                                       distance_to_centre=data['distance_to_centre'], price=data['price'],
                                       photos='')
            else:
                photo_str = ' [;] '.join(data['photos'])
                HistoryResponse.create(owner=history_comm, id_hotel=data['id_hotel'],
                                       name_hotel=data['name_hotel'], address=data['address'],
                                       distance_to_centre=data['distance_to_centre'], price=data['price'],
                                       photos=photo_str)
    except Exception as db_set_ex:
        logger.error('error_db: {chat_id}: {ex}'.format(chat_id=name_table, ex=str(db_set_ex)))
        return [{'error_db': '{ex}'.format(city_name=name_table, ex=str(db_set_ex))}]


def get_history(name_table: str = None):
    """
    Функция получения истории юзера из базы данных.

    :param name_table: str - ID чата.
    :return: list
    """
    try:
        db = SqliteDatabase('db_history.db')

        class History(Model):
            id = PrimaryKeyField(null=False)
            command = CharField()
            date = CharField()

            class Meta:
                database = db
                db_table = 'history_{name_table}'.format(name_table=name_table)

        class HistoryResponse(Model):
            owner = ForeignKeyField(History, related_name='responses')
            id_hotel = CharField()
            name_hotel = CharField()
            address = CharField()
            distance_to_centre = CharField()
            price = CharField()
            photos = CharField()

            class Meta:
                database = db
                db_table = 'history_response{name_table}'.format(name_table=name_table)

        result_list = []
        for command in History.select():
            command_dict = {
                'command': command.command,
                'date': command.date,
                'history_responses': []
            }

            for resp in command.responses:
                resp_dict = {
                    'id_hotel': resp.id_hotel,
                    'name_hotel': resp.name_hotel,
                    'address': resp.address,
                    'distance_to_centre': float(resp.distance_to_centre),
                    'price': float(resp.price)
                }
                if resp.photos:
                    resp_dict['photos'] = resp.photos.split(' [;] ')
                command_dict['history_responses'].append(resp_dict)
            result_list.append(command_dict)
        return result_list
    except Exception as db_ex:
        logger.error('error_db: {chat_id}: {ex}'.format(chat_id=name_table, ex=str(db_ex)))
        return [{'error_db': '{ex}'.format(city_name=name_table, ex=str(db_ex))}]
