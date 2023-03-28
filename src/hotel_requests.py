import os
import requests
from loguru import logger
from dotenv import load_dotenv

load_dotenv()
X_RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')


@logger.catch
def api_request(method_endswith,
                params,
                method_type
                ):
    """
    Функция общего запроса.

    :param method_endswith:
    :param params:
    :param method_type:
    :return: dict
    """
    url = 'https://hotels4.p.rapidapi.com/{}'.format(method_endswith)

    if method_type == 'GET':
        return get_request(
            url=url,
            params=params
        )
    else:
        return post_request(
            url=url,
            params=params
        )


@logger.catch
def post_request(url, params):
    """
    Функция POST запроса

    :param url: str - ссылка на запрос:
    :param params: dict - параметры запроса
    :return:  dict
    """
    headers = {
        'X-RapidAPI-Key': X_RAPIDAPI_KEY,
        'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'
    }
    try:
        response = requests.request("POST", url, json=params, headers=headers, timeout=25)
        if response.status_code == requests.codes.ok:
            return response.json()
    except Exception as ex:
        logger.error('error_post_request: {ex}'.format(ex=str(ex)))
        return ex


def get_request(url, params):
    """
    Функция GET запроса

    :param url: str - ссылка на запрос:
    :param params: dict - параметры запроса
    :return:  dict
    """
    headers = {
        'X-RapidAPI-Key': X_RAPIDAPI_KEY,
        'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'
    }
    try:
        response = requests.request("GET", url, headers=headers, params=params, timeout=25)
        if response.status_code == requests.codes.ok:
            return response.json()
    except Exception as ex:
        logger.error('error_get_request: {ex}'.format(ex=str(ex)))
        return ex


def request_location(city: str = None):
    """
    Функция запроса ID города по названию.

    :param city: str - название города:
    :return: list
    """

    endswith = 'locations/v3/search'
    querystring = {'q': city, 'locale': 'ru_RU'}
    m_type = 'GET'
    try:
        data = api_request(endswith,
                           querystring,
                           m_type
                           )

        return data['sr']
    except Exception as ex:
        logger.error('error_location_request: {ex}'.format(ex=str(ex)))
        return ex


def request_hotels(city_id: str = None,
                   number_of_hotels: int = None,
                   sort_method: str = None,
                   filter_data: dict = None,
                   checkIn_day: int = None,
                   checkIn_month: int = None,
                   checkIn_year: int = None,
                   checkOut_day: int = None,
                   checkOut_month: int = None,
                   checkOut_year: int = None,
                   ):
    """
    Функция запроса списка отелей, по заданным параметрам.

    :param city_id: str - ID города
    :param number_of_hotels: int - количество отелей
    :param sort_method: str - метод сортировки
    :param filter_data: dict - фильтр поиска
    :param checkIn_day: int - день въезда
    :param checkIn_month: int - месяц въезда
    :param checkIn_year: int - год въезда
    :param checkOut_day: int - день выезда
    :param checkOut_month: int - месяц выезда
    :param checkOut_year: int - год выезда
    :return: dict
    """

    endswith = 'properties/v2/list'
    payload = {'currency': 'USD',
               'eapid': 1,
               'locale': 'ru_RU',
               'siteId': 300000001,
               'destination': {'regionId': city_id},
               'checkInDate': {'day': checkIn_day, 'month': checkIn_month, 'year': checkIn_year},
               'checkOutDate': {'day': checkOut_day, 'month': checkOut_month, 'year': checkOut_year},
               'rooms': [{'adults': 1}],
               'resultsStartingIndex': 0,
               'resultsSize': number_of_hotels,
               'sort': sort_method,
               'filters': filter_data
               }
    m_type = 'POST'
    try:
        data = api_request(endswith,
                           payload,
                           m_type
                           )
        return data['data']['propertySearch']['properties']
    except Exception as ex:
        logger.error('error_hotels_request: {ex}'.format(ex=str(ex)))
        return ex


def request_details_hotel(id_hotel: str = None):
    """
    Функция запроса деталей отеля.

    :param id_hotel: str - ID отеля, детали которого надо найти
    :return: dict
    """
    endswith = 'properties/v2/detail'
    payload = {
        'currency': 'USD',
        'eapid': 1,
        'locale': 'en_US',
        'siteId': 300000001,
        'propertyId': id_hotel
    }
    m_type = 'POST'
    try:
        data = api_request(endswith,
                           payload,
                           m_type
                           )
        return data
    except Exception as ex:
        logger.error('error_details_hotel_request: {ex}'.format(ex=str(ex)))
        return ex
